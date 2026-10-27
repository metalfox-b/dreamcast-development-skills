#!/usr/bin/env python3
"""Prepare a PNG for a Dreamcast texture encoder.

Usage:
  quantize_texture.py --platform dc SRC OUT.<fmt>.png [--size 256x256] [--colors N]
                      [--half-mirror x|y] [--lock FILE] [--palette-from TEX.png]
                      [--dither none|ordered] [--pal-format argb1555]

Steps: box-resize to --size -> alpha to the format's bits -> reduce colors
(median cut for palette formats, channel bits for direct ones) -> optional ordered dither -> bleed edge colors into transparent
texels -> write -> validate.

Palette formats (pal4/pal8) keep 1-bit alpha: one transparent entry. VQ tags
produce their base format's pixels (e.g. vq565 -> RGB565); a Dreamcast encoder
such as pvrtex performs the VQ encoding at export. preview_480.py --vq shows the VQ loss now.

--half-mirror x: SRC is the full symmetric image; OUT keeps the left half,
  drawn with mirror repeat.
--lock: colors (#RRGGBB per line) that must survive. Defaults to OUT's lock
  file (npc_face.lock.txt) if present.
--palette-from: restrict PNG colors to those in another texture. To share a
  hardware palette bank, encode with the same .pal and verify palette indices.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from dcfmt import (Fmt, format_from_name, get_format, lock_file_for, pal_entry_depth, parse_size,
                    platform, platform_key, read_lock_file, snap)
from validate_textures import validate

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
LOCK_RADIUS = 9 * 24 ** 2  # weighted squared distance: about 24 levels per channel


def resize(img: Image.Image, size: tuple[int, int], half_mirror: str | None) -> Image.Image:
    w, h = size
    full = (w * 2, h) if half_mirror == "x" else (w, h * 2) if half_mirror == "y" else (w, h)
    if img.size != full:
        down = img.width >= full[0] and img.height >= full[1]
        img = img.resize(full, Image.Resampling.BOX if down else Image.Resampling.BICUBIC)
    return img.crop((0, 0, w, h))


def snap_alpha(a: int, bits: int) -> int:
    if bits == 0:
        return 255
    if bits == 1:
        return 255 if a >= 128 else 0
    return snap(a, bits)


def snap_rgb(c, bits) -> list[int]:
    return [snap(max(0, min(255, c[i])), bits[i]) for i in range(3)]


def dist(a, b) -> int:
    return (a[0] - b[0]) ** 2 * 3 + (a[1] - b[1]) ** 2 * 4 + (a[2] - b[2]) ** 2 * 2


def dither_offset(x: int, y: int, amplitude: int) -> int:
    return round((BAYER4[y % 4][x % 4] / 15 - 0.5) * amplitude)


def median_cut(colors: list[tuple[int, int, int]], k: int) -> list[tuple[int, int, int]]:
    if k <= 0 or not colors:
        return []
    strip = Image.new("RGB", (len(colors), 1))
    strip.putdata(colors)
    q = strip.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[: 3 * k]
    return [tuple(pal[3 * i: 3 * i + 3]) for i in sorted(set(q.getdata()))]


def bleed(px: list[list[int]], w: int, h: int) -> None:
    """Give transparent texels the average color of nearby opaque texels (in place),
    so bilinear filtering shows no dark halo around cutouts."""
    known = [[px[y * w + x][3] > 0 for x in range(w)] for y in range(h)]
    for _ in range(max(w, h)):
        updates = []
        for y in range(h):
            for x in range(w):
                if known[y][x]:
                    continue
                ns = [px[ny * w + nx] for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
                      if 0 <= nx < w and 0 <= ny < h and known[ny][nx]]
                if ns:
                    updates.append((x, y, [sum(n[i] for n in ns) // len(ns) for i in range(3)]))
        if not updates:
            break
        for x, y, rgb in updates:
            px[y * w + x][:3] = rgb
            known[y][x] = True


def quantize_palette(px, w, h, fmt: Fmt, colors, locks, dither, pal_format, fixed_palette) -> None:
    rgb_bits, _ = pal_entry_depth(fmt, pal_format)
    for p in px:
        p[3] = snap_alpha(p[3], 1)
    has_alpha = any(p[3] == 0 for p in px)
    snapped_locks = [tuple(snap_rgb(c, rgb_bits)) for c in locks]
    for lock, snapped in zip(locks, snapped_locks):
        hits = 0
        for p in px:
            if p[3] and dist(p[:3], lock) <= LOCK_RADIUS:
                p[:3] = snapped
                hits += 1
        if not hits:
            print(f"   WARN:  locked color #{'%02X%02X%02X' % lock} matches no source pixels; check the lock file")
    if fixed_palette:
        palette = fixed_palette
    else:
        cap = colors or fmt.max_colors
        room = cap - (1 if has_alpha else 0) - len(set(snapped_locks))
        if room < 0:
            raise SystemExit(f"{len(set(snapped_locks))} locked colors leave no room in a {cap}-color palette")
        opaque = [tuple(p[:3]) for p in px if p[3] and tuple(p[:3]) not in snapped_locks]
        palette = sorted({tuple(snap_rgb(c, rgb_bits)) for c in median_cut(opaque, room)} | set(snapped_locks))
    amp = 64 // max(2, int(len(palette) ** (1 / 3))) if dither == "ordered" else 0
    for i, p in enumerate(px):
        if not p[3] or (tuple(p[:3]) in snapped_locks and not fixed_palette):
            continue
        d = dither_offset(i % w, i // w, amp)
        c = tuple(max(0, min(255, v + d)) for v in p[:3])
        p[:3] = min(palette, key=lambda q: dist(q, c))
    if has_alpha:
        # one shared transparent entry: the mean color of the opaque edge texels
        edge = []
        for y in range(h):
            for x in range(w):
                if not px[y * w + x][3]:
                    edge += [px[ny * w + nx][:3] for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
                             if 0 <= nx < w and 0 <= ny < h and px[ny * w + nx][3]]
        mean = snap_rgb([sum(c[i] for c in edge) // len(edge) for i in range(3)], rgb_bits) if edge else [0, 0, 0]
        for p in px:
            if not p[3]:
                p[:3] = mean


def quantize_direct(px, w, h, fmt: Fmt, locks, dither) -> None:
    for i, p in enumerate(px):
        x, y = i % w, i // w
        p[3] = snap_alpha(p[3], fmt.alpha_bits)
        bits = fmt.rgb_bits
        if any(dist(p[:3], lock) <= LOCK_RADIUS for lock in locks):
            p[:3] = snap_rgb(min(locks, key=lambda q: dist(q, p[:3])), bits)
            continue
        amps = [255 // ((1 << b) - 1) if dither == "ordered" and b < 8 else 0 for b in bits]
        p[:3] = [snap(max(0, min(255, p[c] + dither_offset(x, y, amps[c]))), bits[c]) for c in range(3)]
    if any(p[3] < 255 for p in px):
        bleed(px, w, h)
        for p in px:
            if p[3] < 255:
                p[:3] = [snap(p[c], fmt.rgb_bits[c]) for c in range(3)]


def save(px, w, h, fmt: Fmt, path: Path) -> None:
    img = Image.new("RGBA", (w, h))
    img.putdata([tuple(p) for p in px])
    if fmt.kind == "pal":
        colors = sorted({p for p in img.getdata()}, key=lambda p: (p[3], p))  # transparent entry first
        index = {c: i for i, c in enumerate(colors)}
        out = Image.new("P", img.size)
        out.putpalette([v for c in colors for v in c[:3]])
        out.putdata([index[p] for p in img.getdata()])
        transparent = [i for i, c in enumerate(colors) if c[3] == 0]
        out.save(path, transparency=transparent[0]) if transparent else out.save(path)
    else:
        img.save(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--platform", default="dc", help="dc or dreamcast")
    ap.add_argument("--format", help="override the format tag in OUT")
    ap.add_argument("--size", help="final stored size, e.g. 256x256 (default: SRC size)")
    ap.add_argument("--colors", type=int, help="palette size cap (default: the format's maximum)")
    ap.add_argument("--half-mirror", choices=["x", "y"])
    ap.add_argument("--lock", type=Path)
    ap.add_argument("--palette-from", type=Path)
    ap.add_argument("--dither", choices=["none", "ordered"], default="none")
    ap.add_argument("--pal-format", help="palette entry format, e.g. argb4444")
    ap.add_argument("--allow-npot", action="store_true", help="allow valid strided direct or VQ textures")
    args = ap.parse_args()

    plat = platform_key(args.platform)
    fmt = get_format(plat, args.format) if args.format else format_from_name(args.out, plat)
    if fmt is None:
        ap.error(f"OUT needs a {plat} format tag (name.pal8.png) or pass --format")
    if args.half_mirror and "mirror" not in platform(plat)["tile_modes"]:
        ap.error(f"{platform(plat)['name']} has no mirror tile mode; store the full image")
    if args.colors is not None and (fmt.kind != "pal" or not 1 <= args.colors <= fmt.max_colors):
        ap.error(f"--colors requires a palette format and a value from 1 to {fmt.max_colors}")
    if args.palette_from and fmt.kind != "pal":
        ap.error("--palette-from only applies to palette formats")

    img = Image.open(args.src).convert("RGBA")
    size = parse_size(args.size) if args.size else img.size
    img = resize(img, size, args.half_mirror)
    w, h = img.size
    px = [list(p) for p in img.getdata()]

    lock = args.lock or lock_file_for(args.out)
    locks = read_lock_file(lock) if lock.exists() else []
    if fmt.kind == "pal":
        fixed = None
        if args.palette_from:
            fixed = sorted({p[:3] for p in Image.open(args.palette_from).convert("RGBA").getdata() if p[3]})
        quantize_palette(px, w, h, fmt, args.colors, locks, args.dither, args.pal_format, fixed)
    else:
        quantize_direct(px, w, h, fmt, locks, args.dither)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    save(px, w, h, fmt, args.out)

    r = validate(args.out, plat, fmt, allow_npot=args.allow_npot, pal_format=args.pal_format)
    verdict = "FAIL" if r["errors"] else "PASS"
    print(f"[{verdict}] {args.out}  platform={plat} size={r.get('size')} format={fmt.tag} "
          f"colors={r.get('colors')} bytes={r.get('bytes')}")
    for e in r["errors"]:
        print(f"   ERROR: {e}")
    for wmsg in r["warnings"]:
        print(f"   WARN:  {wmsg}")
    if fmt.kind == "vq":
        print(f"   NOTE:  pixels are {fmt.base}; the {fmt.tag} encode happens at export")
    return 1 if r["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
