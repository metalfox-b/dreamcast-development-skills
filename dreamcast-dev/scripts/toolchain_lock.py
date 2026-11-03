#!/usr/bin/env python3
"""Record or verify SHA-256 files in a project lock. Paths are relative to the lock.

Lock-file idea: gsimone's typegpu-crt-shaders; original implementation.
"""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['record', 'verify'])
    ap.add_argument('lock', type=Path)
    ap.add_argument('--version', action='append', default=[], metavar='NAME=VALUE')
    ap.add_argument('--commit', action='append', default=[], metavar='NAME=VALUE')
    args = ap.parse_args()
    try:
        data = json.loads(args.lock.read_text())
        if not isinstance(data.get('files'), dict) or not data['files']:
            raise ValueError('list at least one file in the files object before recording or verifying')
        if args.command == 'verify' and (args.version or args.commit):
            raise ValueError('version and commit values are recorded assertions; only record accepts them')
        if args.command == 'record':
            for field, entries in [('versions', args.version), ('commits', args.commit)]:
                for entry in entries:
                    key, value = entry.split('=', 1)
                    if not key or not value:
                        raise ValueError('expected NAME=VALUE')
                    data.setdefault(field, {})[key] = value
            hashes = {name: digest(args.lock.parent / name) for name in data['files']}
            data['files'] = hashes
            args.lock.write_text(json.dumps(data, indent=2)+'\n')
            print(f'Recorded {len(hashes)} files')
            return 0
        drift = []
        for name, expected in data['files'].items():
            try:
                actual = digest(args.lock.parent / name)
            except OSError:
                actual = None
            if actual != expected or expected is None:
                drift.append(name)
        print('DRIFT: '+', '.join(drift) if drift else 'Verified all file hashes')
        return int(bool(drift))
    except (OSError, ValueError, TypeError) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    raise SystemExit(main())
