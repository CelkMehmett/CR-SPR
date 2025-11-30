#!/usr/bin/env python3
"""Small CLI to help generate disk cache keys for deployment.

Commands:
 - encrypt-with-kms --key-file key.bin --key-id <kms-key-id> [--region ..] [--role-arn ..]
   -> prints base64 ciphertext to stdout

 - upload-to-ssm --key-file key.bin --param-name /prod/keys/disk-cache [--region ..] [--role-arn ..]
   -> uploads as SecureString

This tool intentionally uses boto3 and will error if boto3 is not installed.
"""
import argparse
import base64
import sys


def _assume_role_session(role_arn):
    try:
        import boto3
        sts = boto3.client('sts')
        resp = sts.assume_role(RoleArn=role_arn, RoleSessionName='crispr-disk-key-tool')
        creds = resp['Credentials']
        return boto3.session.Session(
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken'],
        )
    except Exception:
        raise


def encrypt_with_kms(key_file, key_id, region='us-east-1', role_arn=None):
    try:
        import boto3
        from botocore.config import Config
    except Exception:
        print('boto3 is required for KMS operations', file=sys.stderr)
        raise

    with open(key_file, 'rb') as f:
        pt = f.read()

    if role_arn:
        session = _assume_role_session(role_arn)
        kms = session.client('kms', region_name=region, config=Config(retries={'max_attempts': 3}))
    else:
        kms = boto3.client('kms', region_name=region, config=Config(retries={'max_attempts': 3}))

    resp = kms.encrypt(KeyId=key_id, Plaintext=pt)
    ct = resp.get('CiphertextBlob')
    if isinstance(ct, bytes):
        print(base64.b64encode(ct).decode())
    else:
        print(ct)


def upload_to_ssm(key_file, param_name, region='us-east-1', role_arn=None, description=None):
    try:
        import boto3
        from botocore.config import Config
    except Exception:
        print('boto3 is required for SSM operations', file=sys.stderr)
        raise

    with open(key_file, 'rb') as f:
        pt = f.read()

    if role_arn:
        session = _assume_role_session(role_arn)
        ssm = session.client('ssm', region_name=region, config=Config(retries={'max_attempts': 3}))
    else:
        ssm = boto3.client('ssm', region_name=region, config=Config(retries={'max_attempts': 3}))

    ssm.put_parameter(Name=param_name, Value=pt.decode('utf-8'), Type='SecureString', Overwrite=True, Description=description or '')
    print(f'Uploaded {param_name} as SecureString')


def main(argv=None):
    p = argparse.ArgumentParser(description='Disk key helper')
    sub = p.add_subparsers(dest='cmd')

    e = sub.add_parser('encrypt-with-kms')
    e.add_argument('--key-file', required=True)
    e.add_argument('--key-id', required=True)
    e.add_argument('--region', default='us-east-1')
    e.add_argument('--role-arn')

    u = sub.add_parser('upload-to-ssm')
    u.add_argument('--key-file', required=True)
    u.add_argument('--param-name', required=True)
    u.add_argument('--region', default='us-east-1')
    u.add_argument('--role-arn')
    u.add_argument('--description')

    args = p.parse_args(argv)
    if args.cmd == 'encrypt-with-kms':
        encrypt_with_kms(args.key_file, args.key_id, region=args.region, role_arn=args.role_arn)
    elif args.cmd == 'upload-to-ssm':
        upload_to_ssm(args.key_file, args.param_name, region=args.region, role_arn=args.role_arn, description=args.description)
    else:
        p.print_help()


if __name__ == '__main__':
    main()
