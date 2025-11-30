#!/usr/bin/env python3
"""Re-encrypt checkpoint blobs in an existing SQLite DB.

Usage:
  python scripts/reencrypt_checkpoints.py --db rl_checkpoints.db --new-key NEWKEY [--old-key OLDKEY] [--dry-run]

Notes:
 - NEWKEY/OLDKEY may be a hex key (32 bytes hex => 64 chars) or a passphrase.
 - This script requires the `cryptography` package when the new key is provided.
"""
import argparse
import sqlite3
import os
import sys

from core.crypto_utils import ENC_HEADER, encryption_available, encrypt_blob, decrypt_blob


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--db', required=True, help='Path to rl_checkpoints.db')
    p.add_argument('--old-key', default=None, help='Old CHECKPOINT_ENC_KEY (hex or passphrase)')
    p.add_argument('--new-key', required=True, help='New CHECKPOINT_ENC_KEY (hex or passphrase)')
    p.add_argument('--dry-run', action='store_true', help='Do not modify DB, just report')
    p.add_argument('--backup', action='store_true', help='Create a timestamped backup copy of the DB before modifying')
    p.add_argument('--export-dir', default=None, help='Directory to export current blobs as files before re-encrypting')
    p.add_argument('--log-file', default=None, help='Path to write an operation log')
    p.add_argument('--yes', action='store_true', help='Assume yes for confirmation and skip interactive prompt')
    return p.parse_args()


def set_env_key(key: str):
    if key is None:
        if 'CHECKPOINT_ENC_KEY' in os.environ:
            del os.environ['CHECKPOINT_ENC_KEY']
    else:
        os.environ['CHECKPOINT_ENC_KEY'] = key


def main():
    args = parse_args()

    if not encryption_available():
        print('cryptography package is required for encryption. Install with `pip install cryptography`')
        sys.exit(2)

    db = args.db
    if not os.path.exists(db):
        print('DB not found:', db)
        sys.exit(1)

    # optional backup
    if args.backup:
        import shutil
        import datetime as _dt
        bak = f"{db}.bak.{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
        shutil.copy2(db, bak)
        log.info('Backup created at %s', bak)

    # configure logging
    import logging
    log = logging.getLogger('reencrypt')
    log.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    log.addHandler(ch)
    if args.log_file:
        fh = logging.FileHandler(args.log_file)
        fh.setFormatter(fmt)
        log.addHandler(fh)

    log.info('Opening DB %s', db)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT id, name, blob FROM checkpoints ORDER BY id')
    rows = cur.fetchall()

    to_update = []

    for id_, name, blob in rows:
        # ensure blob is bytes
        if isinstance(blob, memoryview):
            raw = blob.tobytes()
        else:
            raw = blob

        # determine if currently encrypted
        encrypted = raw.startswith(ENC_HEADER)

        # obtain plaintext
        if encrypted:
            if not args.old_key:
                print(f'Encrypted checkpoint {name} found but no --old-key provided; aborting')
                conn.close()
                sys.exit(1)
            # set old key and decrypt
            set_env_key(args.old_key)
            try:
                plaintext = decrypt_blob(raw)
            except Exception as e:
                print(f'Failed to decrypt {name}: {e}')
                conn.close()
                sys.exit(1)
        else:
            # already plaintext
            plaintext = raw

        # encrypt with new key
        set_env_key(args.new_key)
        try:
            new_blob = encrypt_blob(plaintext)
        except Exception as e:
            print(f'Failed to encrypt {name} with new key: {e}')
            conn.close()
            sys.exit(1)

        to_update.append((id_, name, new_blob))

    # report
    log.info('Found %d checkpoints to re-encrypt', len(to_update))
    # optionally export current blobs to files
    if args.export_dir:
        os.makedirs(args.export_dir, exist_ok=True)
        manifest = []
        for id_, name, blob in rows:
            fn = os.path.join(args.export_dir, f"ckpt_{id_}_{name}.blob")
            with open(fn, 'wb') as f:
                if isinstance(blob, memoryview):
                    f.write(blob.tobytes())
                else:
                    f.write(blob)
            manifest.append({'id': id_, 'name': name, 'file': os.path.basename(fn)})
        # write manifest
        import json
        with open(os.path.join(args.export_dir, 'manifest.json'), 'w') as mf:
            json.dump(manifest, mf, indent=2)
        log.info('Exported current blobs to %s', args.export_dir)

    if args.dry_run:
        for id_, name, _ in to_update:
            log.info('Would update id=%s name=%s', id_, name)
        conn.close()
        return

    # confirm destructive action
    if not args.yes:
        token = 'REALLY REENCRYPT'
        print('\nDestructive action: this will overwrite checkpoint blobs in the DB.')
        print('To confirm, type exactly:', token)
        resp = input('Confirmation: ').strip()
        if resp != token:
            log.info('Aborted by user (confirmation mismatch)')
            conn.close()
            return
        log.info('User confirmed by token')
    else:
        log.info('Auto-confirmation enabled (--yes)')

    # perform updates with progress indicator and atomic replace
    try:
        from tqdm import tqdm  # type: ignore
        use_tqdm = True
    except Exception:
        use_tqdm = False

    items = to_update
    rng = tqdm(items) if use_tqdm else items
    for id_, name, blob in rng:
        cur.execute('UPDATE checkpoints SET blob = ?, created_at = ? WHERE id = ?', (sqlite3.Binary(blob), sqlite3.datetime.datetime.utcnow().isoformat(), id_))

    conn.commit()
    conn.close()

    # atomic replace: write to temp file then move (already in-place updates DB file; we also wrote backup earlier)
    log.info('Re-encryption completed')


if __name__ == '__main__':
    main()
