#!/usr/bin/env python3
"""Fit conservative alpha-card polygons. Pixel origin and UV V both run downward.

Idea: gsimone's diet-sprite; Andrew monotone chain reference: Project Nayuki.
Original implementation. No third-party hull code used.
"""
import argparse
import json
import math
from pathlib import Path
from PIL import Image


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])


def hull(points):
    points = sorted(set(points))
    if len(points) < 3:
        return points
    chains = []
    for seq in (points, reversed(points)):
        chain = []
        for p in seq:
            while len(chain) > 1 and cross(chain[-2], chain[-1], p) <= 0:
                chain.pop()
            chain.append(p)
        chains.append(chain[:-1])
    return chains[0] + chains[1]


def area(poly):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(poly, poly[1:]+poly[:1]))) / 2


def intersection(a, b, c, d):
    u = (b[0]-a[0], b[1]-a[1])
    v = (d[0]-c[0], d[1]-c[1])
    det = u[0]*v[1]-u[1]*v[0]
    if abs(det) < 1e-10:
        return None
    t = ((c[0]-a[0])*v[1]-(c[1]-a[1])*v[0])/det
    return (a[0]+t*u[0], a[1]+t*u[1])


def contains(poly, points):
    return all(cross(a, b, p) >= -1e-7 for a, b in zip(poly, poly[1:]+poly[:1]) for p in points)


def reduce_hull(poly, count, w, h):
    original = poly[:]
    while len(poly) > count:
        candidates = []
        for i in range(len(poly)):
            q = poly[i:] + poly[:i]
            p = intersection(q[-1], q[0], q[1], q[2])
            if p is None or not (0 <= p[0] <= w and 0 <= p[1] <= h):
                continue
            candidate = [p] + q[2:]
            if contains(candidate, original):
                candidates.append(candidate)
        if not candidates:
            # An enclosing rectangle remains conservative when edge merges stall.
            if count >= 4:
                xs, ys = zip(*original)
                return [(min(xs), min(ys)), (max(xs), min(ys)),
                        (max(xs), max(ys)), (min(xs), max(ys))]
            # Try supporting triangles, retaining UVs inside the frame.
            for angle in range(360):
                normals = [(math.cos(math.radians(angle+120*j)),
                            math.sin(math.radians(angle+120*j))) for j in range(3)]
                lines = []
                for nx, ny in normals:
                    k = max(nx*x+ny*y for x, y in original)
                    lines.append(((nx*k, ny*k), (nx*k-ny, ny*k+nx)))
                tri = hull([intersection(*lines[j], *lines[(j+1)%3]) for j in range(3)])
                if all(0 <= x <= w and 0 <= y <= h for x, y in tri) and contains(tri, original):
                    return tri
            raise ValueError('cannot fit 3 vertices within image bounds; use more vertices or pad the image')
        poly = min(candidates, key=area)
    return poly


def pixel_corners(image, threshold):
    alpha = image.convert('RGBA').getchannel('A')
    # Only row endpoints are needed: their corners enclose every occupied pixel in that row.
    points = []
    px = alpha.load()
    for y in range(image.height):
        xs = [x for x in range(image.width) if px[x, y] > threshold]
        if xs:
            points.extend([(min(xs), y), (max(xs)+1, y), (max(xs)+1, y+1), (min(xs), y+1)])
    return points


def fit(points, w, h, count):
    poly = reduce_hull(hull(points), count, w, h) if points else []
    size = area(poly)
    return {'vertices_px': poly, 'vertices_uv': [[x/w, y/h] for x, y in poly],
            'triangles': [[0, i, i+1] for i in range(1, len(poly)-1)],
            'hull_area': size, 'full_quad_area': w*h, 'saved_fraction': 1-size/(w*h)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('image', type=Path)
    ap.add_argument('--grid', default='1x1', help='flipbook columns x rows')
    ap.add_argument('--threshold', type=int, default=0)
    ap.add_argument('--vertices', type=int, default=8)
    ap.add_argument('--shared', action='store_true')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    try:
        cols, rows = map(int, args.grid.lower().split('x'))
        if min(cols, rows) < 1 or args.vertices < 3 or not 0 <= args.threshold <= 255:
            raise ValueError('grid must be positive, vertices at least 3, threshold from 0 to 255')
        with Image.open(args.image) as image:
            if image.width % cols or image.height % rows:
                raise ValueError('grid must divide image dimensions')
            w, h = image.width//cols, image.height//rows
            frames = [pixel_corners(image.crop((x*w, y*h, (x+1)*w, (y+1)*h)), args.threshold)
                      for y in range(rows) for x in range(cols)]
        if args.shared:
            frames = [[p for frame in frames for p in frame]]
        report = {'frame_size': [w, h], 'grid': [cols, rows], 'shared': args.shared,
                  'uv_orientation': 'frame-local U right, V down; origin top left',
                  'frames': [fit(p, w, h, args.vertices) for p in frames]}
        args.out.write_text(json.dumps(report, indent=2)+'\n')
    except (ValueError, OSError) as exc:
        ap.error(str(exc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
