import os
import sys
import base64

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from core.api_server import app, autolab, ledger_fallback
from core.merkle_ledger import MerkleLedger

client = TestClient(app)
API_KEY = "your-secret-api-key-here"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    _HAS_CRYPTO = True
except Exception:
    _HAS_CRYPTO = False


import pytest


@pytest.mark.skipif(not _HAS_CRYPTO, reason='cryptography not available')
def test_ed25519_sign_and_verify_roundtrip():
    # generate key
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    priv_pem = priv.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
    pub_pem = pub.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

    b64_priv = base64.b64encode(priv_pem).decode()
    b64_pub = base64.b64encode(pub_pem).decode()

    # create ledger
    ml = MerkleLedger()
    ml.append({'a': 1})
    ml.append({'b': 2})

    if autolab is None:
        ledger_fallback.leaves = ml.leaves.copy()
    else:
        autolab.ledger.leaves = ml.leaves.copy()

    # sign via API
    r = client.post('/api/ledger/sign_ed25519', headers=HEADERS, json={'private_pem_b64': b64_priv})
    assert r.status_code == 200
    data = r.json()
    sig = data.get('signature')
    root = data.get('root')
    assert sig is not None and root is not None

    # verify via verify endpoint
    rv = client.post('/api/ledger/verify_ed25519', headers=HEADERS, json={'public_pem_b64': b64_pub, 'signature_hex': sig, 'root_hex': root})
    assert rv.status_code == 200
    assert rv.json().get('valid') is True

    # tamper signature
    bad = sig[:-1] + ('0' if sig[-1] != '0' else '1')
    rv2 = client.post('/api/ledger/verify_ed25519', headers=HEADERS, json={'public_pem_b64': b64_pub, 'signature_hex': bad, 'root_hex': root})
    assert rv2.status_code == 200
    assert rv2.json().get('valid') is False
