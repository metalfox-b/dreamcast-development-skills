#!/usr/bin/env python3
"""Check prepared Dreamcast PNG textures and estimate texture and palette memory.

Usage:
  validate_textures.py --platform dc PATH... [--budget ASSET.budget.json] [--target hardware|style]
                       [--budget-bytes N] [--mips] [--allow-npot] [--pal-format argb1555] [--json]
  validate_textures.py --platform dc --plan 256x256 vq565 [--mips]
  validate_textures.py --platform dc --cheat-sheet

PATH is a texture (<name>.<fmt>.png) or a folder of them. The format tag is
read from the Dreamcast format tag in each PNG filename.

Per texture: the tag is a format of the platform, pixels satisfy it (palette
size and entry depth, channel bits, alpha bits), size rules (power of two,
min/max, block multiples).
Per set: the VRAM tally (every texture's bytes, palettes and VQ codebooks
included) against the platform's texture budget, and on DC the global
palette RAM (1024 entries; the real encoder and game control bank sharing).
With --budget: each PNG matches the listed size and format. Mipmap memory is
estimated from the plan; actual encoded mipmaps and palette indices need checking.

--target hardware turns set-level overruns into errors; style reports them as warnings. Exit 1 on any error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

import dcfmt
from dcfmt import (FORMATS, Fmt, format_from_name, get_format, is_pot, kib, pal_entry_depth,
                    parse_size, platform, platform_key, representable, stem_without_tag, texture_bytes)


def _pixels(path: Path) -> tuple[Image.Image, list[tuple[int, int, int, int]]]:
    img = Image.open(path)
    return img, list(img.convert("RGBA").getdata())


def check_pixels(fmt: Fmt, px: list[tuple[int, int, int, int]], pal_format: str | None) -> tuple[list[str], int]:
    errors: list[str] = []
    colors = set(px)
    if fmt.kind == "pal":
        if len(colors) > fmt.max_colors:
            errors.append(f"{len(colors)} colors; {fmt.tag} allows {fmt.max_colors}")
        rgb_bits, a_bits = pal_entry_depth(fmt, pal_format)
        bad = [c for c in colors if not _depth_ok(c, rgb_bits, a_bits)]
        if bad:
            errors.append(f"{len(bad)} palette colors not representable in {pal_format or fmt.pal_entry} entries, e.g. {bad[0]}")
        return errors, len(colors)

    bad = sum(1 for p in px if not _depth_ok(p, fmt.rgb_bits, fmt.alpha_bits))
    if bad:
        what = f"{fmt.base} source pixels" if fmt.base else fmt.tag
        errors.append(f"{bad} texels not representable as {what} (run quantize_texture.py)")
    return errors, len(colors)


def _alpha_ok(a: int, bits: int) -> bool:
    if bits == 0:
        return a == 255
    if bits == 1:
        return a in (0, 255)
    return representable(a, bits)


def _depth_ok(p, rgb_bits, a_bits) -> bool:
    return all(representable(p[i], rgb_bits[i]) for i in range(3)) and _alpha_ok(p[3], a_bits)


def dimension_checks(w: int, h: int, fmt: Fmt, prof: dict, mips: bool, allow_npot: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for side in (w, h):
        if side > prof["max_texture"]:
            errors.append(f"{w}x{h} exceeds the {prof['name']} maximum of {prof['max_texture']}")
            break
        if side < prof["min_texture"]:
            errors.append(f"{w}x{h} is below the {prof['name']} minimum of {prof['min_texture']}")
            break
    if not (is_pot(w) and is_pot(h)):
        if not allow_npot:
            errors.append(f"{w}x{h} is not power-of-two (use --allow-npot only for supported strided textures)")
        elif mips:
            errors.append("non-power-of-two strided textures cannot have mipmaps")
        elif fmt.kind not in ("direct", "vq"):
            errors.append("DC strided (non-power-of-two) textures need a 16-bit direct or VQ format")
        elif w % 32 or not is_pot(h):
            errors.append("DC strided textures need a width that is a multiple of 32 and a power-of-two height")
        else:
            warnings.append("DC stride is one global register: every strided texture drawn at once must share this width")
    if mips and w != h:
        warnings.append("DC mipmapped textures must be square (verify with the encoder and loader)")

    return errors, warnings


def validate(path: Path, plat: str, fmt: Fmt | None = None, mips: bool = False, allow_npot: bool = False,
             pal_format: str | None = None) -> dict:
    plat = platform_key(plat)
    prof = platform(plat)
    fmt = fmt or format_from_name(path, plat)
    r: dict = {"file": str(path), "errors": [], "warnings": [], "format": fmt.tag if fmt else None, "mips": mips}
    if fmt is None:
        r["errors"].append(f"no {plat} format tag in the name (one of: {', '.join(FORMATS[plat])})")
        return r
    img, px = _pixels(path)
    w, h = img.size
    r["size"] = f"{w}x{h}"

    e, ncolors = check_pixels(fmt, px, pal_format)
    r["errors"] += e
    r["colors"] = ncolors
    if fmt.kind == "pal":
        r["palette"] = sorted(set(px))

    dimension_errors, dimension_warnings = dimension_checks(w, h, fmt, prof, mips, allow_npot)
    r["errors"] += dimension_errors
    r["warnings"] += dimension_warnings

    if max(w, h) > prof["recommended_max_texture"]:
        r["warnings"].append(f"{w}x{h} is above {prof['recommended_max_texture']}; keep that for skies and hero textures")
    nbytes = texture_bytes(plat, fmt, w, h, mips)
    r["bytes"] = nbytes
    pal8 = texture_bytes(plat, get_format("dc", "pal8"), w, h, mips)
    if fmt.kind == "vq" and nbytes >= pal8:
        r["warnings"].append(f"VQ costs {kib(nbytes)} here, no less than PAL8 ({kib(pal8)})")
    if fmt.kind == "direct" and w * h >= 128 * 128:
        vq = texture_bytes(plat, get_format("dc", "vq" + fmt.tag.replace("argb", "").replace("rgb", "")), w, h, mips)
        r["warnings"].append(f"{fmt.tag} costs {kib(nbytes)}; as VQ it would be about {kib(vq)}")
    return r


def collect(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        files += sorted(p.rglob("*.png")) if p.is_dir() else [p]
    return [f for f in files if not f.name.endswith(".preview.png")]


def check_set(results: list[dict], plat: str, target: str, budget_bytes: int | None) -> dict:
    prof = platform(plat)
    cap = budget_bytes or prof["texture_budget_bytes"]
    total = sum(r.get("bytes", 0) for r in results)
    s: dict = {"total_bytes": total, "budget_bytes": cap, "errors": [], "warnings": []}
    sink = s["errors"] if target == "hardware" else s["warnings"]
    if total > cap:
        sink.append(f"VRAM tally {kib(total)} is over the {prof['name']} texture budget of {kib(cap)}")
    if plat == "dc":
        p8 = {tuple(r["palette"]) for r in results if r.get("format") == "pal8" and "palette" in r}
        p4 = {tuple(r["palette"]) for r in results if r.get("format") == "pal4" and "palette" in r}
        used = dcfmt.dc_palette_entries(len(p8), len(p4))
        s["palette_entries"] = used
        if p8 or p4:
            s["warnings"].append("Palette RAM is an estimate: verify encoded palette indices and bank assignments in the game")
        if used > prof["palette_ram_entries"]:
            sink.append(f"palette RAM {used} of {prof['palette_ram_entries']} entries ({len(p8)} PAL8 + {len(p4)} PAL4 "
                        f"palettes); use a shared encoder palette and configure the game bank")
    return s


def check_budget(budget: dict, results: list[dict], plat: str) -> list[str]:
    errors: list[str] = []
    prof = platform(plat)
    by_stem = {stem_without_tag(Path(r["file"])): r for r in results}
    for t in budget.get("textures", []):
        r = by_stem.get(t["name"])
        if r is None:
            errors.append(f"budget texture '{t['name']}' has no file")
            continue
        if r.get("format") != t["format"].lower():
            errors.append(f"'{t['name']}' is {r.get('format')}; the budget says {t['format']}")
        if r.get("size") != t["size"]:
            errors.append(f"'{t['name']}' is {r.get('size')}; the budget says {t['size']}")
        for axis, mode in (t.get("tile") or {}).items():
            if mode not in prof["tile_modes"]:
                errors.append(f"'{t['name']}' tile {axis}={mode} doesn't exist on {prof['name']} "
                              f"({', '.join(prof['tile_modes'])})")
    known = {t["name"] for t in budget.get("textures", [])}
    for stem in by_stem:
        if stem not in known:
            errors.append(f"'{stem}' isn't in the budget")
    return errors


def cheat_sheet(plat: str, mips: bool) -> str:
    sizes = [(32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)]
    head = "| Format | " + " | ".join(f"{w}x{h}" for w, h in sizes) + " |"
    lines = [f"{platform(plat)['name']} texture bytes{' with full mips' if mips else ''} "
             f"(VQ codebooks included; palette RAM separate; budget {kib(platform(plat)['texture_budget_bytes'])})",
             "", head, "|" + "---|" * (len(sizes) + 1)]
    for fmt in FORMATS[plat].values():
        lines.append(f"| {fmt.tag} | " + " | ".join(kib(texture_bytes(plat, fmt, w, h, mips)) for w, h in sizes) + " |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--platform")
    ap.add_argument("--budget", type=Path)
    ap.add_argument("--target", choices=["hardware", "style"])
    ap.add_argument("--budget-bytes", type=int, help="override the platform texture budget for this set")
    ap.add_argument("--mips", action="store_true", help="count full mip chains (budget entries override per texture)")
    ap.add_argument("--allow-npot", action="store_true")
    ap.add_argument("--pal-format", help="palette entry format, e.g. argb4444 on dc (default per platform)")
    ap.add_argument("--plan", nargs=2, metavar=("WxH", "FMT"))
    ap.add_argument("--cheat-sheet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.budget_bytes is not None and args.budget_bytes <= 0:
        ap.error("--budget-bytes must be positive")
    budget = json.loads(args.budget.read_text()) if args.budget else None
    if budget and budget.get("platform"):
        platform_key(budget["platform"])
    plat_name = args.platform or (budget or {}).get("platform")
    if not plat_name:
        ap.error("pass --platform dc or a --budget that names one")
    plat = platform_key(plat_name)
    target = args.target or (budget or {}).get("target", "hardware")
    if target not in ("hardware", "style"):
        ap.error("budget target must be hardware or style")

    if args.cheat_sheet:
        print(cheat_sheet(plat, args.mips))
        return 0
    if args.plan:
        w, h = parse_size(args.plan[0])
        fmt = get_format(plat, args.plan[1])
        errors, warnings = dimension_checks(w, h, fmt, platform(plat), args.mips, args.allow_npot)
        if errors:
            ap.error("; ".join(errors))
        n = texture_bytes(plat, fmt, w, h, args.mips)
        cap = args.budget_bytes or platform(plat)["texture_budget_bytes"]
        print(f"{w}x{h} {fmt.tag}{' +mips' if args.mips else ''}: estimated {kib(n)} ({100 * n / cap:.1f}% of {kib(cap)})")
        for warning in warnings:
            print(f"   WARN: {warning}")
        return 0
    if not args.paths:
        ap.error("pass textures or folders to validate")

    mips_for = {t["name"]: bool(t.get("mips")) for t in (budget or {}).get("textures", [])}
    results = []
    for f in collect(args.paths):
        mips = mips_for.get(stem_without_tag(f), args.mips)
        results.append(validate(f, plat, mips=mips, allow_npot=args.allow_npot, pal_format=args.pal_format))
    if not results:
        ap.error("no PNG textures found")
    summary = check_set(results, plat, target, args.budget_bytes)
    if budget:
        summary["errors"] += check_budget(budget, results, plat)

    failed = any(r["errors"] for r in results) or bool(summary["errors"])
    if args.json:
        for r in results:
            r.pop("palette", None)
        print(json.dumps({"platform": plat, "target": target, "textures": results, "set": summary}, indent=2))
        return 1 if failed else 0

    for r in results:
        verdict = "FAIL" if r["errors"] else "PASS"
        extra = ""
        print(f"[{verdict}] {r['file']}  size={r.get('size')} format={r.get('format')} "
              f"colors={r.get('colors')} bytes={kib(r.get('bytes', 0))}{extra}")
        for e in r["errors"]:
            print(f"   ERROR: {e}")
        for wmsg in r["warnings"]:
            print(f"   WARN:  {wmsg}")
    pct = 100 * summary["total_bytes"] / summary["budget_bytes"]
    print(f"\nEstimated texture VRAM ({platform(plat)['name']}, target {target}): "
          f"{kib(summary['total_bytes'])} of {kib(summary['budget_bytes'])} ({pct:.1f}%)")
    if "palette_entries" in summary:
        print(f"Estimated palette RAM: {summary['palette_entries']} of {platform(plat)['palette_ram_entries']} entries")
    for e in summary["errors"]:
        print(f"   ERROR: {e}")
    for wmsg in summary["warnings"]:
        print(f"   WARN:  {wmsg}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
