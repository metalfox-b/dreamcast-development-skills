#!/usr/bin/env python3
"""Record an exact decoded-byte comparison, without resizing or tolerance.

Method idea: gsimone's typegpu-crt-shaders. Original code.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops


def compare(first, second, include_alpha=False):
    with Image.open(first) as a, Image.open(second) as b:
        if a.size != b.size:
            raise ValueError(f'image sizes differ: {a.size} versus {b.size}')
        mode = 'RGBA' if include_alpha else 'RGB'
        diff = ImageChops.difference(a.convert(mode), b.convert(mode))
    pixels = list(diff.getdata())
    values = [v for p in pixels for v in p]
    record = {'dimensions': list(diff.size), 'include_alpha': include_alpha,
              'differing_pixels': sum(any(p) for p in pixels),
              'differing_rgb_bytes': sum(v != 0 for p in pixels for v in p[:3]),
              'differing_bytes': sum(v != 0 for v in values),
              'mean_error': sum(values)/len(values), 'max_error': max(values),
              'exact': not any(values),
              'inputs': [{'path': str(p), 'sha256': hashlib.sha256(Path(p).read_bytes()).hexdigest()}
                         for p in (first, second)]}
    # RGBA differences have zero alpha at equal pixels: save channels as visible RGB,
    # with a separate grayscale alpha-difference image when requested.
    return record, diff


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('first', type=Path)
    ap.add_argument('second', type=Path)
    ap.add_argument('--out', type=Path, required=True, help='difference PNG; JSON uses the same stem')
    ap.add_argument('--include-alpha', action='store_true')
    ap.add_argument('--meta', action='append', default=[], metavar='KEY=VALUE')
    args = ap.parse_args()
    try:
        meta = {}
        for entry in args.meta:
            key, value = entry.split('=', 1)
            if not key:
                raise ValueError('metadata needs a nonempty key')
            meta[key] = value
        record, diff = compare(args.first, args.second, args.include_alpha)
        record['meta'] = meta
        diff.convert('RGB').save(args.out)
        if args.include_alpha:
            diff.getchannel('A').save(args.out.with_name(args.out.stem+'.alpha.png'))
        args.out.with_suffix('.json').write_text(json.dumps(record, indent=2)+'\n')
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    print(json.dumps(record, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
