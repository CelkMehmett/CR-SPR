# Checkpoint encryption (optional)

The RL checkpoint system supports optional AES-GCM encryption of checkpoint blobs at rest.

How it works

- If the environment variable `CHECKPOINT_ENC_KEY` is set, `core.rl_checkpoint` will encrypt blobs using AES-GCM before storing them in `rl_checkpoints.db`.
- The key can be provided either as a hex string (16 or 32 bytes hex) or as a passphrase; a passphrase will be hashed with SHA256 to derive a 32-byte key.
- Encrypted blobs are prefixed with a small header so the loader can detect encrypted vs plain blobs.

Environment variable example (in `.env` or `.env.example`):

```env
# hex key (32 bytes hex => 64 chars)
CHECKPOINT_ENC_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

# or a passphrase (less secure unless protected)
CHECKPOINT_ENC_KEY=my-secret-passphrase
```

Notes & caveats

- The `cryptography` package must be installed for encryption to work. If the env var is set but `cryptography` is unavailable, saving a checkpoint will raise an error.
- For production, use a proper secret manager (Vault, KMS) and never commit keys into the repository.
- Consider rotating keys and providing a migration plan for re-encrypting old blobs.

Re-encrypting existing DB entries

We've included a helper script `scripts/reencrypt_checkpoints.py` that will re-encrypt blobs in-place.

Example (dry run):

```bash
python scripts/reencrypt_checkpoints.py --db rl_checkpoints.db --old-key OLDKEY --new-key NEWKEY --dry-run
```

# Checkpoint encryption (optional)

The RL checkpoint system supports optional AES-GCM encryption of checkpoint blobs at rest.

How it works

- If the environment variable `CHECKPOINT_ENC_KEY` is set, `core.rl_checkpoint` will encrypt blobs using AES-GCM before storing them in `rl_checkpoints.db`.
- The key can be provided either as a hex string (16 or 32 bytes hex) or as a passphrase; a passphrase will be hashed with SHA256 to derive a 32-byte key.
- Encrypted blobs are prefixed with a small header so the loader can detect encrypted vs plain blobs.

Environment variable example (in `.env` or `.env.example`):

```env
# hex key (32 bytes hex => 64 chars)
CHECKPOINT_ENC_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

# or a passphrase (less secure unless protected)
CHECKPOINT_ENC_KEY=my-secret-passphrase
```

Notes & caveats

- The `cryptography` package must be installed for encryption to work. If the env var is set but `cryptography` is unavailable, saving a checkpoint will raise an error.
- For production, use a proper secret manager (Vault, KMS) and never commit keys into the repository.
- Consider rotating keys and providing a migration plan for re-encrypting old blobs.

Re-encrypting existing DB entries

We've included a helper script `scripts/reencrypt_checkpoints.py` that will re-encrypt blobs in-place.

Example (dry run):

```bash
python scripts/reencrypt_checkpoints.py --db rl_checkpoints.db --old-key OLDKEY --new-key NEWKEY --dry-run
```

To perform the re-encryption:

```bash
python scripts/reencrypt_checkpoints.py --db rl_checkpoints.db --old-key OLDKEY --new-key NEWKEY
```

If blobs are currently plaintext, omit `--old-key` and the script will encrypt them with the new key.

Backup and export options

- `--backup` will create a timestamped copy of the DB before changes.
- `--export-dir DIR` will export the current blobs as files before re-encrypting (useful for offline backups).

Example with backup and export:

```bash
python scripts/reencrypt_checkpoints.py --db rl_checkpoints.db --old-key OLDKEY --new-key NEWKEY --backup --export-dir ./ckpt_exports
```

If you exported blobs and want to re-import them into another environment, use:

```bash
PYTHONPATH=. python3 scripts/import_checkpoints_from_dir.py --db rl_checkpoints.db --dir ./ckpt_exports --dry-run
```

Remove `--dry-run` to actually import.

Strong confirmation

The re-encrypt script now requires you to type a confirmation token to proceed (unless you pass `--yes`). The token is:

```text
REALLY REENCRYPT
```

This helps prevent accidental destructive operations.

Logging

- Use `--log-file reencrypt.log` to persist logs to a file in addition to console output.
- The script emits INFO logs about backups, exports, and operations.
