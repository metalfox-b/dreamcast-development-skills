"""Shared sixth-gen texture rules: formats per platform, storage bytes, color snapping.

Single source of truth for validate_textures.py, quantize_texture.py and
preview_480.py. Platform numbers (budgets, size limits, tile modes) live in
../../sixthgen-reference/platforms.json. Format facts follow the KallistiOS
and dreamcast.wiki docs (DC), PS2Tek/PS2Docs (PS2), libogc/YAGCD (GC) and
xboxdevwiki XPR (Xbox); see ../../sixthgen-reference/platforms.md.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

PLATFORMS_JSON = Path(__file__).resolve().parents[2] / "sixthgen-reference" / "platforms.json"
VQ_CODEBOOK_BYTES = 2048  # 256 codewords x 2x2 texels x 16 bit
PLATFORM_ALIASES = {"dreamcast": "dc", "playstation2": "ps2", "gamecube": "gc", "wii": "gc", "ogxbox": "xbox"}


@dataclass(frozen=True)
class Fmt:
    tag: str
    kind: str                 # "pal" | "direct" | "gray" | "vq" | "block" | "rgb5a3"
    bpp: float                # stored bits per texel, before tiling or padding
    rgb_bits: tuple = (8, 8, 8)
    alpha_bits: int = 0       # 0 = opaque only
    max_colors: int = 0       # palette formats
    base: str = ""            # vq/block: the direct format the source pixels must satisfy
    block: int = 1            # block formats need dimensions in multiples of this
    pal_entry: str = ""       # palette formats: default palette entry format


def _d(tag, bpp, rgb, a):
    return Fmt(tag, "direct", bpp, rgb, a)


FORMATS: dict[str, dict[str, Fmt]] = {
    "dc": {f.tag: f for f in [
        Fmt("pal4", "pal", 4, max_colors=16, pal_entry="argb1555"),
        Fmt("pal8", "pal", 8, max_colors=256, pal_entry="argb1555"),
        _d("rgb565", 16, (5, 6, 5), 0),
        _d("argb1555", 16, (5, 5, 5), 1),
        _d("argb4444", 16, (4, 4, 4), 4),
        Fmt("vq565", "vq", 2, (5, 6, 5), 0, base="rgb565"),
        Fmt("vq1555", "vq", 2, (5, 5, 5), 1, base="argb1555"),
        Fmt("vq4444", "vq", 2, (4, 4, 4), 4, base="argb4444"),
    ]},
    "ps2": {f.tag: f for f in [
        Fmt("psmt4", "pal", 4, max_colors=16, pal_entry="psmct32"),
        Fmt("psmt8", "pal", 8, max_colors=256, pal_entry="psmct32"),
        _d("psmct16", 16, (5, 5, 5), 1),
        _d("psmct24", 32, (8, 8, 8), 0),
        _d("psmct32", 32, (8, 8, 8), 8),
    ]},
    "gc": {f.tag: f for f in [
        Fmt("i4", "gray", 4, (4, 4, 4), 0),
        Fmt("i8", "gray", 8, (8, 8, 8), 0),
        Fmt("ia4", "gray", 8, (4, 4, 4), 4),
        Fmt("ia8", "gray", 16, (8, 8, 8), 8),
        _d("rgb565", 16, (5, 6, 5), 0),
        Fmt("rgb5a3", "rgb5a3", 16, (5, 5, 5), 3),
        _d("rgba8", 32, (8, 8, 8), 8),
        Fmt("ci4", "pal", 4, max_colors=16, pal_entry="rgb5a3"),
        Fmt("ci8", "pal", 8, max_colors=256, pal_entry="rgb5a3"),
        Fmt("cmpr", "block", 4, (5, 6, 5), 1, base="rgb565", block=4),
    ]},
    "xbox": {f.tag: f for f in [
        Fmt("p8", "pal", 8, max_colors=256, pal_entry="a8r8g8b8"),
        _d("r5g6b5", 16, (5, 6, 5), 0),
        _d("a1r5g5b5", 16, (5, 5, 5), 1),
        _d("a4r4g4b4", 16, (4, 4, 4), 4),
        _d("a8r8g8b8", 32, (8, 8, 8), 8),
        Fmt("dxt1", "block", 4, (5, 6, 5), 1, base="r5g6b5", block=4),
        Fmt("dxt3", "block", 8, (5, 6, 5), 4, base="r5g6b5", block=4),
        Fmt("dxt5", "block", 8, (5, 6, 5), 8, base="r5g6b5", block=4),
    ]},
}

# Palette entry formats: color/alpha depth of each palette entry
PAL_ENTRIES = {
    "argb1555": ((5, 5, 5), 1), "rgb565": ((5, 6, 5), 0), "argb4444": ((4, 4, 4), 4), "argb8888": ((8, 8, 8), 8),
    "psmct32": ((8, 8, 8), 8), "psmct16": ((5, 5, 5), 1),
    "rgb5a3": ((5, 5, 5), 3), "ia8": ((8, 8, 8), 8),
    "a8r8g8b8": ((8, 8, 8), 8),
}

# PS2 GS block (256 B) and page (8 KB) dimensions per pixel storage mode
PS2_BLOCK = {"psmct32": (8, 8), "psmct24": (8, 8), "psmct16": (16, 8), "psmt8": (16, 16), "psmt4": (32, 16)}
PS2_PAGE = {"psmct32": (64, 32), "psmct24": (64, 32), "psmct16": (64, 64), "psmt8": (128, 64), "psmt4": (128, 128)}
# GameCube 32-byte tiles (RGBA8 tiles are 64 B: AR and GB halves)
GC_TILE = {"i4": (8, 8), "i8": (8, 4), "ia4": (8, 4), "ia8": (4, 4), "rgb565": (4, 4), "rgb5a3": (4, 4),
           "rgba8": (4, 4), "ci4": (8, 8), "ci8": (8, 4), "cmpr": (8, 8)}


def platform_key(name: str) -> str:
    key = name.lower().replace(" ", "").replace("-", "")
    key = PLATFORM_ALIASES.get(key, key)
    if key not in FORMATS:
        raise SystemExit(f"unknown platform '{name}' (use dc, ps2, gc or xbox)")
    return key


def load_platforms() -> dict:
    return json.loads(PLATFORMS_JSON.read_text())


def platform(name: str) -> dict:
    return load_platforms()[platform_key(name)]


def get_format(plat: str, tag: str) -> Fmt:
    fmts = FORMATS[platform_key(plat)]
    if tag.lower() not in fmts:
        raise SystemExit(f"{tag} is not a {platform_key(plat)} format (one of: {', '.join(fmts)})")
    return fmts[tag.lower()]


def format_from_name(path: str | Path, plat: str) -> Fmt | None:
    """npc_face.pal8.png -> pal8 (for the given platform)"""
    fmts = FORMATS[platform_key(plat)]
    m = re.search(r"\.([a-z0-9]+)\.png$", str(path), re.IGNORECASE)
    return fmts.get(m.group(1).lower()) if m else None


def stem_without_tag(path: Path) -> str:
    m = re.match(r"(.+)\.[a-z0-9]+\.png$", path.name, re.IGNORECASE)
    return m.group(1) if m else path.stem


def parse_size(s: str) -> tuple[int, int]:
    w, h = s.lower().split("x")
    return int(w), int(h)


def is_pot(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def snap(v: int, bits: int) -> int:
    """Nearest 8-bit value representable with `bits` bits."""
    if bits >= 8:
        return v
    m = (1 << bits) - 1
    return round(round(v * m / 255) * 255 / m)


def representable(v: int, bits: int) -> bool:
    return abs(v - snap(v, bits)) <= 1


def pal_entry_depth(fmt: Fmt, pal_format: str | None = None) -> tuple[tuple, int]:
    return PAL_ENTRIES[(pal_format or fmt.pal_entry).lower()]


def mip_levels(w: int, h: int) -> list[tuple[int, int]]:
    levels = [(w, h)]
    while w > 1 or h > 1:
        w, h = max(1, w // 2), max(1, h // 2)
        levels.append((w, h))
    return levels


def _level_bytes(plat: str, fmt: Fmt, w: int, h: int) -> int:
    if plat == "dc":
        return (w * h) // 4 if fmt.kind == "vq" else math.ceil(w * h * fmt.bpp / 8)
    if plat == "ps2":
        bw, bh = PS2_BLOCK[fmt.tag]
        return math.ceil(w / bw) * math.ceil(h / bh) * 256
    if plat == "gc":
        tw, th = GC_TILE[fmt.tag]
        return math.ceil(w / tw) * math.ceil(h / th) * (64 if fmt.tag == "rgba8" else 32)
    if fmt.kind == "block":
        return math.ceil(w / 4) * math.ceil(h / 4) * (8 if fmt.tag == "dxt1" else 16)
    return math.ceil(w * h * fmt.bpp / 8)


def palette_bytes(plat: str, fmt: Fmt) -> int:
    """Bytes a texture's own palette takes in video memory. DC palettes live in
    the separate palette RAM (see palette_entries), so they cost no VRAM."""
    if fmt.kind != "pal" or plat == "dc":
        return 0
    if plat == "ps2":
        return 1024 if fmt.max_colors == 256 else 256  # 32-bit CLUT; a 16-entry CLUT still takes a 256 B block
    if plat == "gc":
        return fmt.max_colors * 2
    return fmt.max_colors * 4


def texture_bytes(plat: str, fmt: Fmt, w: int, h: int, mips: bool = False) -> int:
    """Video-memory bytes for one texture, palette and VQ codebook included."""
    plat = platform_key(plat)
    levels = mip_levels(w, h) if mips else [(w, h)]
    total = sum(_level_bytes(plat, fmt, lw, lh) for lw, lh in levels)
    if fmt.kind == "vq":
        total += VQ_CODEBOOK_BYTES
    return total + palette_bytes(plat, fmt)


def ps2_pages(fmt: Fmt, w: int, h: int) -> int:
    pw, ph = PS2_PAGE[fmt.tag]
    return math.ceil(w / pw) * math.ceil(h / ph)


def dc_palette_entries(palettes8: int, palettes4: int) -> int:
    """DC palette RAM entries used: PAL8 banks are 256-aligned, PAL4 banks 16-aligned,
    so the banks pack as long as the total fits in 1024."""
    return palettes8 * 256 + palettes4 * 16


def kib(n: int) -> str:
    return f"{n / 1024:.1f} KB" if n < 1024 * 1024 else f"{n / 1048576:.2f} MB"


def lock_file_for(out: Path) -> Path:
    return out.with_name(stem_without_tag(out) + ".lock.txt")


def read_lock_file(path: Path) -> list[tuple[int, int, int]]:
    colors = []
    for line in path.read_text().splitlines():
        m = re.match(r"\s*#?([0-9a-fA-F]{6})\b", line)
        if m:
            h = m.group(1)
            colors.append((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))
    return colors


def luminance(r: int, g: int, b: int) -> int:
    return round(0.299 * r + 0.587 * g + 0.114 * b)
