import os
import pytest

from core.disk_cache import DiskCache


@pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1", reason="Local integration tests disabled")
def test_diskcache_ssm_kms_integration(tmp_path):
    # This test expects LocalStack to be running and SSM/KMS to be available on localhost:4566
    # It will read environment variables set by the CI job to locate keys
    cache_dir = tmp_path / "diskcache"
    cache_dir.mkdir()

    # Create disk cache; DiskCache should pick up SSM or KMS env vars (set by CI)
    dc = DiskCache(str(cache_dir), key=None)

    # Basic set/get
    dc.set("test-key", b"hello")
    got = dc.get("test-key")
    assert got == b"hello"
