import os
import subprocess
import pytest

from core.disk_cache import DiskCache


@pytest.mark.skipif(os.environ.get("RUN_INTEGRATION") != "1", reason="Local integration tests disabled")
def test_rekey_disk_cache(tmp_path):
    # Create a disk cache using the current key (provisioned by Makefile)
    cache_dir = tmp_path / "kms_cache"
    cache_dir.mkdir()

    # Create DiskCache pointing to LocalStack-provisioned SSM/KMS key
    dc = DiskCache(str(cache_dir), key=None)
    dc.set("rekey-test", b"persistent")

    # Write an 'old' key file and a 'new' key file for rekey tool
    old_key_file = tmp_path / "old.key"
    new_key_file = tmp_path / "new.key"
    # For integration we will read plaintext key via KMS decrypt in the rekey tool; however
    # to keep test simple, create both files with random bytes and pass them to the rekey script
    old_key_file.write_bytes(os.urandom(32))
    new_key_file.write_bytes(os.urandom(32))

    # Run the rekey script; it should back up files and re-encrypt cache entries
    cmd = ["python3", "scripts/rekey_disk_cache.py", "--cache-dir", str(cache_dir), "--old-key-file", str(old_key_file), "--new-key-file", str(new_key_file), "--backup-dir", str(tmp_path / 'bak')]
    subprocess.check_call(cmd)

    # After rekey, the cache should still return the same value for the key
    dc2 = DiskCache(str(cache_dir), key=None)
    val = dc2.get("rekey-test")
    assert val == b"persistent"
