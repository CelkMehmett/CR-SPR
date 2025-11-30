#!/usr/bin/env python3
"""Import checkpoint blobs exported to a directory into the DB.

Supports files named `ckpt_<id>_<name>.blob` or `<name>.blob` or JSON with {name, blob_hex}.
"""
import argparse
import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.rl_checkpoint import save_checkpoint


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--db', required=True)
    p.add_argument('--dir', required=True)
    p.add_argument('--dry-run', action='store_true')
    return p.parse_args()


def main():
    args = parse_args()
    files = [f for f in os.listdir(args.dir) if os.path.isfile(os.path.join(args.dir, f))]
    found = 0
    for fn in files:
        path = os.path.join(args.dir, fn)
        if fn.endswith('.blob'):
            # try to infer name
            name = fn.rsplit('.', 1)[0]
            if name.startswith('ckpt_'):
                parts = name.split('_', 2)
                if len(parts) == 3:
                    name = parts[2]
            with open(path, 'rb') as f:
                blob = f.read()
            found += 1
            if not args.dry_run:
                save_checkpoint(args.db, name, blob)
                print('Imported', name)
        elif fn.endswith('.json'):
            import json
            with open(path) as f:
                j = json.load(f)
            name = j.get('name')
            blob_hex = j.get('blob')
            if name and blob_hex:
                blob = bytes.fromhex(blob_hex)
                found += 1
                if not args.dry_run:
                    save_checkpoint(args.db, name, blob)
                    print('Imported', name)
    print('Found', found, 'files')


if __name__ == '__main__':
    main()
