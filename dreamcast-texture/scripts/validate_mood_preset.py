#!/usr/bin/env python3
"""Validate a scene recipe restricted to PowerVR2 features, not post effects.

Mood idea: gsimone's public post; original schema and implementation.
Colors are RGB arrays in 0..1. Distances use project units; density is 0..1.
"""
import argparse
import json
import math
from pathlib import Path


def keys(value, required, optional=()):
    if not isinstance(value, dict):
        raise ValueError('expected an object')
    unknown = set(value)-set(required)-set(optional)
    missing = set(required)-set(value)
    if unknown or missing:
        raise ValueError(f'unknown keys {sorted(unknown)}; missing keys {sorted(missing)}')


def number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'number must be finite and between {low} and {high}')


def color(value):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError('color must be an RGB array')
    for channel in value:
        number(channel, 0, 1)


def validate(data):
    keys(data, ['name', 'fog', 'vertex_tint', 'ambient_gradient', 'sky'], ['palette_swap'])
    if not isinstance(data['name'], str) or not data['name'].strip():
        raise ValueError('name must be nonempty text')
    fog = data['fog']
    keys(fog, ['mode', 'color', 'start', 'end', 'density'])
    if fog['mode'] not in ('table', 'vertex'):
        raise ValueError('fog mode must be table or vertex')
    color(fog['color'])
    for key in ('start', 'end'):
        number(fog[key], 0, float('inf'))
    if fog['start'] > fog['end']:
        raise ValueError('fog start must not exceed end')
    number(fog['density'], 0, 1)
    color(data['vertex_tint'])
    for field in ('ambient_gradient', 'sky'):
        gradient = data[field]
        keys(gradient, ['top', 'bottom'] + (['mode'] if field == 'sky' else []))
        color(gradient['top'])
        color(gradient['bottom'])
    if data['sky']['mode'] not in ('geometry', 'texture'):
        raise ValueError('sky must use geometry or texture')
    if 'palette_swap' in data:
        palette = data['palette_swap']
        keys(palette, ['format', 'bank'])
        if palette['format'] not in ('PAL4', 'PAL8'):
            raise ValueError('palette format must be PAL4 or PAL8')
        if type(palette['bank']) is not int:
            raise ValueError('bank must be an integer')
        number(palette['bank'], 0, 63 if palette['format'] == 'PAL4' else 3)
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('preset', type=Path)
    args = ap.parse_args()
    try:
        validate(json.loads(args.preset.read_text()))
    except (OSError, ValueError, TypeError) as exc:
        ap.error(str(exc))
    print(f'PASS: {args.preset}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
