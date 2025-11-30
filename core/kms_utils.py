"""AWS KMS helper utilities used by the API.

Provides lightweight wrappers around boto3 for GenerateMac/VerifyMac (HMAC)
and Sign/Verify (asymmetric). These helpers don't assume any particular IAM
environment; they accept optional role_arn and region_name parameters.
"""
from typing import Optional, Tuple
import base64
import os
import threading
import time
from collections import OrderedDict
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from core.metrics import Counter
from core.redis_cache import RedisCache
from core.disk_cache import DiskCache
import logging

_logger = logging.getLogger(__name__)


def _assume_role_session(role_arn: Optional[str]):
    try:
        import boto3
        if not role_arn:
            return boto3.session.Session()
        sts = boto3.client('sts')
        resp = sts.assume_role(RoleArn=role_arn, RoleSessionName='crispr-kms')
        creds = resp['Credentials']
        return boto3.session.Session(
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
        )
    except Exception:
        raise


def kms_generate_mac(key_id: str, message: bytes, region: str = 'us-east-1', role_arn: Optional[str] = None) -> str:
    """Call KMS GenerateMac and return hex-encoded MAC string."""
    session = _assume_role_session(role_arn)
    kms = session.client('kms', region_name=region)
    resp = kms.generate_mac(KeyId=key_id, Message=message, MacAlgorithm='HMAC_SHA_256')
    mac = resp.get('Mac')
    # boto3 may return bytes or base64; ensure bytes
    if isinstance(mac, str):
        mac_b = base64.b64decode(mac)
    else:
        mac_b = mac
    return mac_b.hex()


def kms_verify_mac(key_id: str, message: bytes, mac_hex: str, region: str = 'us-east-1', role_arn: Optional[str] = None) -> bool:
    session = _assume_role_session(role_arn)
    kms = session.client('kms', region_name=region)
    mac_b = bytes.fromhex(mac_hex)
    # KMS VerifyMac accepts Mac as bytes
    resp = kms.verify_mac(KeyId=key_id, Message=message, Mac=mac_b, MacAlgorithm='HMAC_SHA_256')
    return bool(resp.get('MacValid', False))


def kms_sign_digest(key_id: str, digest: bytes, signing_algorithm: str = 'ECDSA_SHA_256', region: str = 'us-east-1', role_arn: Optional[str] = None) -> str:
    """Call KMS Sign with a digest and return hex-encoded signature."""
    session = _assume_role_session(role_arn)
    kms = session.client('kms', region_name=region)
    resp = kms.sign(KeyId=key_id, Message=digest, MessageType='DIGEST', SigningAlgorithm=signing_algorithm)
    sig = resp.get('Signature')
    if isinstance(sig, str):
        sig_b = base64.b64decode(sig)
    else:
        sig_b = sig
    return sig_b.hex()


def kms_verify_signature(key_id: str, digest: bytes, signature_hex: str, signing_algorithm: str = 'ECDSA_SHA_256', region: str = 'us-east-1', role_arn: Optional[str] = None) -> bool:
    session = _assume_role_session(role_arn)
    kms = session.client('kms', region_name=region)
    sig_b = bytes.fromhex(signature_hex)
    resp = kms.verify(KeyId=key_id, Message=digest, MessageType='DIGEST', Signature=sig_b, SigningAlgorithm=signing_algorithm)
    return bool(resp.get('SignatureValid', False))


def kms_get_public_key(key_id: str, region: str = 'us-east-1', role_arn: Optional[str] = None) -> Tuple[bytes, str]:
    """Return (public_key_pem_bytes, algorithm) by calling GetPublicKey on KMS."""
    session = _assume_role_session(role_arn)
    kms = session.client('kms', region_name=region)
    resp = kms.get_public_key(KeyId=key_id)
    pub_b = resp.get('PublicKey')
    # KMS returns DER; wrap in PEM
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization import load_der_public_key
        pub = load_der_public_key(pub_b)
        pem = pub.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
        alg = resp.get('SigningAlgorithms', [None])[0]
        return pem, alg
    except Exception:
        # fallback: return DER
        return pub_b, ''


# --- Small helpers: retries and a tiny TTL LRU cache for public keys ---
# use tenacity for robust retry behavior
def _tenacity_retry_decorator():
    # increment kms_attempts before each try
    def _before(retry_state):
        try:
            kms_attempts.inc()
        except Exception:
            pass
        try:
            _logger.debug("KMS public key attempt %s for %s", retry_state.attempt_number, retry_state.args)
        except Exception:
            pass

    def _after(retry_state):
        # after a failed attempt
        try:
            _logger.warning("KMS public key attempt %s failed: %s", retry_state.attempt_number, retry_state.outcome.exception())
        except Exception:
            pass

    def _reraise(retry_state):
        try:
            _logger.error("KMS public key final failure after %s attempts: %s", retry_state.attempt_number, retry_state.outcome.exception())
        except Exception:
            pass

    return retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=0.08, max=1.0), retry=retry_if_exception_type(Exception), before=_before, after=_after, reraise=True)


class _PublicKeyCache:
    """Thread-safe tiny TTL LRU cache for KMS public keys.

    Keeps up to `maxsize` items and evicts least-recently-used. Entries expire after `ttl` seconds.
    """
    def __init__(self, maxsize=32, ttl=300):
        self.maxsize = maxsize
        self.ttl = ttl
        self.lock = threading.RLock()
        self.data = OrderedDict()  # key -> (value, inserted_at)

    def get(self, key):
        with self.lock:
            v = self.data.get(key)
            if not v:
                return None
            val, ts = v
            if time.time() - ts > self.ttl:
                # expired
                del self.data[key]
                return None
            # refresh LRU position
            self.data.move_to_end(key)
            return val

    def set(self, key, value):
        with self.lock:
            if key in self.data:
                del self.data[key]
            self.data[key] = (value, time.time())
            # evict
            while len(self.data) > self.maxsize:
                self.data.popitem(last=False)


# module-level cache instance
_PK_CACHE = _PublicKeyCache(maxsize=int(os.environ.get('KMS_PUBKEY_CACHE_MAX', '64')), ttl=int(os.environ.get('KMS_PUBKEY_CACHE_TTL', '600')))
# Redis adapter (optional)
_CACHE_ADAPTER = RedisCache(os.environ.get('KMS_PUBKEY_REDIS_URL'))

# optional disk cache
_DISK_CACHE = None
if os.environ.get('KMS_PUBKEY_USE_DISK', 'false').lower() in ('1', 'true', 'yes'):
    disk_dir = os.environ.get('KMS_PUBKEY_DISK_DIR', './kms_disk_cache')
    _DISK_CACHE = DiskCache(disk_dir)


# metrics
cache_hits = Counter('kms_pubkey_cache_hits_total', 'KMS public key cache hits')
cache_misses = Counter('kms_pubkey_cache_misses_total', 'KMS public key cache misses')
kms_attempts = Counter('kms_pubkey_kms_attempts_total', 'KMS GetPublicKey attempts (including retries)')


def get_cached_public_key(key_id: str, region: str = 'us-east-1', role_arn: Optional[str] = None) -> Tuple[bytes, str]:
    """Get public key from cache or KMS. Retries on transient errors.

    Behavior: check cache; if miss, call `kms_get_public_key` and populate cache. Returns (pem_or_der, alg).
    """
    cache_key = f"{region}:{key_id}:{role_arn or ''}"
    # Try Redis-backed cache first (if configured), then disk, then in-memory
    try:
        v = _CACHE_ADAPTER.get(cache_key)
        if v:
            try:
                cache_hits.inc()
            except Exception:
                pass
            # stored as bytes (PEM/DER)
            return (v, '')
        # Redis miss -> try disk cache if enabled
        if _DISK_CACHE is not None:
            dv = _DISK_CACHE.get(cache_key)
            if dv is not None:
                try:
                    cache_hits.inc()
                except Exception:
                    pass
                return (dv, '')
    except Exception:
        v = None

    existing = _PK_CACHE.get(cache_key)
    if existing is not None:
        try:
            cache_hits.inc()
        except Exception:
            pass
        return existing
    try:
        cache_misses.inc()
    except Exception:
        pass
    # call the underlying function (with retries only around the actual KMS call)
    # wrap kms_get_public_key with retry behavior so attempts counter is only
    # incremented when we actually contact KMS.
    @_tenacity_retry_decorator()
    def _call_kms(key_id_inner, region_inner='us-east-1', role_arn_inner=None):
        return kms_get_public_key(key_id=key_id_inner, region=region_inner, role_arn=role_arn_inner)

    pk = _call_kms(key_id, region, role_arn)
    try:
        _PK_CACHE.set(cache_key, pk)
    except Exception:
        # non-fatal: caching failure shouldn't break correctness
        pass
    # also populate Redis adapter if available
    try:
        # store PEM/DER bytes, set TTL from env or default
        ttl = int(os.environ.get('KMS_PUBKEY_CACHE_TTL', '600'))
        _CACHE_ADAPTER.set(cache_key, pk[0], ttl_seconds=ttl)
    except Exception:
        pass
    # and populate disk cache if enabled
    try:
        if _DISK_CACHE is not None:
            _DISK_CACHE.set(cache_key, pk[0], ttl_seconds=int(os.environ.get('KMS_PUBKEY_CACHE_TTL', '600')))
    except Exception:
        pass
    return pk

