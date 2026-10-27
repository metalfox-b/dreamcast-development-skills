#!/usr/bin/env python3
"""Preview a Dreamcast texture on an approximate 640x480 frame.

Usage:
  preview_480.py --platform dc TEX [--tile U,V] [--repeat U,V] [--shade TOP,BOTTOM]
                 [--mips] [--vq] [--fb16] [--out PATH]

Draws the texture at 64, 128 and 256 px on a 640x480 frame with bilinear
sampling: plain bilinear without --mips (so oversized textures shimmer, as on
hardware), area-filtered with --mips. PC renderers and most emulators hide
these, so the preview is the reference for style targets.

--tile U,V   repeat|mirror|clamp per axis (default repeat,repeat), with --repeat
             copies per axis (default 1,1).
--shade      multiply a vertical vertex-color gradient, e.g. #F0E8E0,#8A7FA0.
--vq         simulate DC VQ compression (256 codewords of 2x2 texels, k-means)
             so the loss can be judged before pvrtex runs. Needs numpy.
--fb16       write the frame through an RGB565 framebuffer with ordered
             dither. Actual display output depends on the game and video mode.

Writes <name>.preview.png beside TEX (or --out), at 2x with nearest scaling.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

from dcfmt import format_from_name, platform, platform_key, snap, stem_without_tag

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
SIZES = (64, 128, 256)


def vq_simulate(img: Image.Image, codewords: int = 256, iterations: int = 10) -> Image.Image:
    import numpy as np  # only this option needs numpy

    a = np.asarray(img.convert("RGBA"), dtype=np.float32)
    h, w = a.shape[:2]
    if h % 2 or w % 2:
        raise ValueError("VQ preview requires even image dimensions")
    blocks = a.reshape(h // 2, 2, w // 2, 2, 4).transpose(0, 2, 1, 3, 4).reshape(-1, 16)
    rng = np.random.default_rng(0)
    k = min(codewords, len(blocks))
    centers = blocks[rng.choice(len(blocks), k, replace=False)].copy()
    for _ in range(iterations):
        labels = np.empty(len(blocks), dtype=np.int32)
        for start in range(0, len(blocks), 512):
            chunk = blocks[start:start + 512]
            d = ((chunk[:, None, :] - centers[None, :, :]) ** 2).sum(-1)
            labels[start:start + len(chunk)] = d.argmin(1)
        for c in range(k):
            members = blocks[labels == c]
            if len(members):
                centers[c] = members.mean(0)
    out = centers[labels].reshape(h // 2, w // 2, 2, 2, 4).transpose(0, 2, 1, 3, 4).reshape(h, w, 4)
    return Image.fromarray(out.round().clip(0, 255).astype(np.uint8))


def tiled(img: Image.Image, modes: list[str], repeat: list[int]) -> Image.Image:
    w, h = img.size
    out = Image.new("RGBA", (w * repeat[0], h * repeat[1]))
    for j in range(repeat[1]):
        for i in range(repeat[0]):
            t = img
            if modes[0] == "mirror" and i % 2:
                t = ImageOps.mirror(t)
            if modes[1] == "mirror" and j % 2:
                t = ImageOps.flip(t)
            if modes[0] == "clamp" and i:
                t = t.crop((w - 1, 0, w, h)).resize((w, h))
            if modes[1] == "clamp" and j:
                t = t.crop((0, h - 1, w, h)).resize((w, h))
            out.paste(t, (i * w, j * h))
    return out


def scaled(img: Image.Image, size: tuple[int, int], mips: bool) -> Image.Image:
    if mips:
        return img.resize(size, Image.Resampling.BILINEAR)
    sx, sy = img.width / size[0], img.height / size[1]
    # transform samples at the mapped points with no prefilter: hardware bilinear without mips
    return img.transform(size, Image.Transform.AFFINE, (sx, 0, sx / 2 - 0.5, 0, sy, sy / 2 - 0.5),
                         resample=Image.Resampling.BILINEAR)


def hex_rgb(s: str) -> tuple[int, int, int]:
    s = s.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def shade(img: Image.Image, top, bottom) -> Image.Image:
    w, h = img.size
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = [top[i] + (bottom[i] - top[i]) * t for i in range(3)]
        for x in range(w):
            r, g, b, a = px[x, y]
            px[x, y] = (round(r * c[0] / 255), round(g * c[1] / 255), round(b * c[2] / 255), a)
    return img


def fb16(img: Image.Image) -> Image.Image:
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            d = BAYER4[y % 4][x % 4] / 15 - 0.5
            r, g, b = px[x, y][:3]
            px[x, y] = (snap(max(0, min(255, round(r + d * 8))), 5),
                        snap(max(0, min(255, round(g + d * 4))), 6),
                        snap(max(0, min(255, round(b + d * 8))), 5))
    return img


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tex", type=Path)
    ap.add_argument("--platform", default="dc", help="dc or dreamcast")
    ap.add_argument("--tile", default="repeat,repeat")
    ap.add_argument("--repeat", default="1,1")
    ap.add_argument("--shade")
    ap.add_argument("--mips", action="store_true")
    ap.add_argument("--vq", action="store_true")
    ap.add_argument("--fb16", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    plat = platform_key(args.platform)
    modes = args.tile.split(",")
    if len(modes) != 2 or any(mode not in platform(plat)["tile_modes"] for mode in modes):
        ap.error("--tile needs two modes: repeat, mirror, or clamp")
    try:
        repeat = [int(v) for v in args.repeat.split(",")]
    except ValueError:
        ap.error("--repeat needs two positive integers")
    if len(repeat) != 2 or any(v < 1 for v in repeat):
        ap.error("--repeat needs two positive integers")
    fmt = format_from_name(args.tex, plat)
    img = Image.open(args.tex).convert("RGBA")
    if args.vq or (fmt and fmt.kind == "vq"):
        try:
            img = vq_simulate(img)
        except ImportError:
            ap.error("VQ preview needs numpy (python3 -m pip install numpy)")
        except ValueError as exc:
            ap.error(str(exc))
    img = tiled(img, modes, repeat)
    if args.shade:
        top, bottom = (hex_rgb(c) for c in args.shade.split(","))
        img = shade(img, top, bottom)

    frame = Image.new("RGB", (640, 480), (96, 96, 104))
    x = 32
    for s in SIZES:
        sw, sh = s, round(s * img.height / img.width)
        tile = scaled(img, (sw, sh), args.mips)
        frame.paste(tile, (x, (480 - sh) // 2), tile)
        x += sw + 32
    if args.fb16:
        frame = fb16(frame)
    out = args.out or args.tex.with_name(stem_without_tag(args.tex) + ".preview.png")
    frame.resize((1280, 960), Image.Resampling.NEAREST).save(out)
    print(f"wrote {out}  (640x480 frame at 2x; sizes {', '.join(map(str, SIZES))} px"
          f"{'; VQ simulated' if args.vq or (fmt and fmt.kind == 'vq') else ''}{'; RGB565 framebuffer' if args.fb16 else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
