"""Dreamcast texture formats and estimated resident memory sizes."""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

PLATFORMS_JSON = Path(__file__).resolve().parents[2] / "dreamcast-reference" / "platforms.json"
VQ_CODEBOOK_BYTES = 2048


@dataclass(frozen=True)
class Fmt:
    tag: str
    kind: str
    bpp: int
    rgb_bits: tuple = (8, 8, 8)
    alpha_bits: int = 0
    max_colors: int = 0
    base: str = ""
    pal_entry: str = ""


def _direct(tag, rgb, alpha):
    return Fmt(tag, "direct", 16, rgb, alpha)


FORMATS = {"dc": {f.tag: f for f in [
    Fmt("pal4", "pal", 4, max_colors=16, pal_entry="argb1555"),
    Fmt("pal8", "pal", 8, max_colors=256, pal_entry="argb1555"),
    _direct("rgb565", (5, 6, 5), 0),
    _direct("argb1555", (5, 5, 5), 1),
    _direct("argb4444", (4, 4, 4), 4),
    Fmt("vq565", "vq", 2, (5, 6, 5), 0, base="rgb565"),
    Fmt("vq1555", "vq", 2, (5, 5, 5), 1, base="argb1555"),
    Fmt("vq4444", "vq", 2, (4, 4, 4), 4, base="argb4444"),
]}}
PAL_ENTRIES = {
    "argb1555": ((5, 5, 5), 1),
    "rgb565": ((5, 6, 5), 0),
    "argb4444": ((4, 4, 4), 4),
    "argb8888": ((8, 8, 8), 8),
}


def platform_key(name: str) -> str:
    key = name.lower().replace(" ", "").replace("-", "")
    if key not in ("dc", "dreamcast"):
        raise SystemExit(f"unsupported platform '{name}': this tool supports Dreamcast only")
    return "dc"


def platform(name: str) -> dict:
    return json.loads(PLATFORMS_JSON.read_text())[platform_key(name)]


def get_format(plat: str, tag: str) -> Fmt:
    fmts = FORMATS[platform_key(plat)]
    if tag.lower() not in fmts:
        raise SystemExit(f"{tag} is not a supported Dreamcast format (choose: {', '.join(fmts)})")
    return fmts[tag.lower()]


def format_from_name(path: str | Path, plat: str) -> Fmt | None:
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
    if bits >= 8:
        return v
    maximum = (1 << bits) - 1
    return round(round(v * maximum / 255) * 255 / maximum)


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


def texture_bytes(plat: str, fmt: Fmt, w: int, h: int, mips: bool = False) -> int:
    """Estimate texture payload plus a full VQ codebook, excluding container padding.

    The Dreamcast's palette RAM is separate. Tiny mip levels and loader alignment
    may require extra padding; compare with the actual converted file and loader.
    """
    platform_key(plat)
    levels = mip_levels(w, h) if mips else [(w, h)]
    total = sum(math.ceil(lw * lh * fmt.bpp / 8) for lw, lh in levels)
    return total + (VQ_CODEBOOK_BYTES if fmt.kind == "vq" else 0)


def dc_palette_entries(palettes8: int, palettes4: int) -> int:
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
            colors.append(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    return colors
