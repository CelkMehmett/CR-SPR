PHONY: install-dev install-ops install-ci test lint clean

PYTHON := python3

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-dev.txt || true

install-ops:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-ops.txt

install-ci:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-ci.txt

test:
	PYTHONPATH=. $(PYTHON) -m pytest -q

lint:
	# Install ruff locally and run checks; non-fatal so CI can opt-in
	$(PYTHON) -m pip install ruff || true
	ruff check . || true

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache

integration:
	# Start LocalStack, provision a sample SSM param and KMS ciphertext, run integration test, then stop LocalStack
	$(MAKE) start-localstack
	$(MAKE) provision-localstack
	$(MAKE) run-integration
	$(MAKE) stop-localstack

.PHONY: start-localstack provision-localstack run-integration stop-localstack

start-localstack:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-ops.txt
	# start this in detached mode
	localstack start -d
	# wait until the edge port is ready
	n=0; until nc -z localhost 4566 || [ $$n -ge 60 ]; do n=$$((n+1)); sleep 1; done

provision-localstack:
	# create a sample SSM parameter and a KMS ciphertext in LocalStack
	aws --endpoint-url=http://localhost:4566 ssm put-parameter --name /ci/keys/disk-cache --value "$$(openssl rand -hex 32)" --type SecureString --overwrite
	KEY_ID=$$(aws --endpoint-url=http://localhost:4566 kms create-key --query KeyMetadata.KeyId --output text)
	# persist KEY_ID for later steps
	echo $$KEY_ID > kms_key_id.txt
	openssl rand -hex 32 > key.bin
	aws --endpoint-url=http://localhost:4566 kms encrypt --key-id $$KEY_ID --plaintext fileb://key.bin --output text --query CiphertextBlob > key.b64
	# Create a test IAM role that can be assumed. Persist its ARN for the assume-role test.
	cat > assume_policy.json <<'POL'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": "*"},
      "Action": "sts:AssumeRole"
    }
  ]
}
POL
	ROLE_NAME=CrisprTestRole
	ROLE_ARN=$$(aws --endpoint-url=http://localhost:4566 iam create-role --role-name $$ROLE_NAME --assume-role-policy-document file://assume_policy.json --query Role.Arn --output text)
	echo $$ROLE_ARN > ROLE_ARN.txt
	rm -f assume_policy.json || true

run-integration:
	# run all integration tests that follow the naming pattern
	KMS_KEY_ID=$$(cat kms_key_id.txt) ROLE_ARN=$$(cat ROLE_ARN.txt) DISK_CACHE_KEY_SSM_PATH=/ci/keys/disk-cache DISK_CACHE_KEY_KMS_CIPHERTEXT="$$(cat key.b64)" RUN_INTEGRATION=1 PYTHONPATH=. pytest tests/test_integration_*.py -q

stop-localstack:
	localstack stop || true
