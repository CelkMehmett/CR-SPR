"""Redis-backed cache adapter with in-process fallback.

Provides a simple interface used by `core/kms_utils.py`:
- get(key) -> value or None
- set(key, value, ttl_seconds)

When the `redis` python client is available and the environment variable
`KMS_PUBKEY_REDIS_URL` is set, this adapter will use Redis. Otherwise it
falls back to an in-memory TTL cache suitable for tests or single-process
deployments.
"""
from typing import Optional
import os
import threading
import time

class _InMemoryFallback:
    def __init__(self):
        self.lock = threading.RLock()
        self.data = {}  # key -> (value_str, expires_at)

    def get(self, key: str) -> Optional[bytes]:
        with self.lock:
            v = self.data.get(key)
            if not v:
                return None
            val_str, exp = v
            if exp and time.time() > exp:
                del self.data[key]
                return None
            return val_str.encode()

    def set(self, key: str, value: bytes, ttl_seconds: Optional[int] = None):
        with self.lock:
            exp = time.time() + ttl_seconds if ttl_seconds else None
            self.data[key] = (value.decode(), exp)


class RedisCache:
    def __init__(self, url: Optional[str] = None):
        url = url or os.environ.get('KMS_PUBKEY_REDIS_URL')
        if not url:
            self._client = _InMemoryFallback()
            self._is_redis = False
            return
        try:
            import redis

            self._client = redis.from_url(url)
            self._is_redis = True
        except Exception:
            # fallback to in-memory
            self._client = _InMemoryFallback()
            self._is_redis = False

    def get(self, key: str) -> Optional[bytes]:
        try:
            if self._is_redis:
                v = self._client.get(key)
                return v
            return self._client.get(key)
        except Exception:
            return None

    def set(self, key: str, value: bytes, ttl_seconds: Optional[int] = None):
        try:
            if self._is_redis:
                if ttl_seconds:
                    self._client.set(key, value, ex=ttl_seconds)
                else:
                    self._client.set(key, value)
            else:
                self._client.set(key, value, ttl_seconds)
        except Exception:
            return
