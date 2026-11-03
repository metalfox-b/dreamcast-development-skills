#!/usr/bin/env python3
"""Wang-tile autotiling lookups and Dreamcast tile-sheet planning.

usage: autotile.py table {corner,edge,blob}
       autotile.py map GRID.txt --set {corner,edge,blob} [--outside-filled]
       autotile.py plan --set {corner,edge,blob} --tile PX --format FMT
                        [--gutter PX] [--mips] [--pairs N]

Bits: corner TL=1 TR=2 BL=4 BR=8; edge N=1 E=2 S=4 W=8; blob N=1 NE=2 E=4
SE=8 S=16 SW=32 W=64 NW=128, where a diagonal counts only when both edges
beside it match, leaving 47 blob tiles. A corner set is drawn on a dual grid
offset by half a tile, so a W x H terrain map produces (W+1) x (H+1) tiles.
GRID.txt uses '#' for the filled terrain and any other character for empty.

`plan` finds the smallest power-of-two sheet (8 to 1024 px per side) holding
the set's tiles and estimates its memory with the plugin's texture sizes.
Twiddled Dreamcast textures need power-of-two sides; mipmapping an atlas
blends neighbouring tiles, so plan point-sampled sheets or add gutters.
Original implementation; method credit in dreamcast-reference/autotiling.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dcfmt import get_format, kib, platform, texture_bytes  # noqa: E402

N, NE, E, SE, S, SW, W, NW = 1, 2, 4, 8, 16, 32, 64, 128
DIAGONALS = ((NE, N, E), (SE, S, E), (SW, S, W), (NW, N, W))


def corner_index(tl: bool, tr: bool, bl: bool, br: bool) -> int:
    return tl * 1 + tr * 2 + bl * 4 + br * 8


def edge_index(n: bool, e: bool, s: bool, w: bool) -> int:
    return n * 1 + e * 2 + s * 4 + w * 8


def blob_reduce(mask: int) -> int:
    """Drop each diagonal bit that is not backed by both neighbouring edges."""
    if not 0 <= mask <= 255:
        raise ValueError("blob mask must be 0..255")
    for diagonal, a, b in DIAGONALS:
        if mask & diagonal and not (mask & a and mask & b):
            mask &= ~diagonal
    return mask


def blob_masks() -> list[int]:
    return sorted({blob_reduce(m) for m in range(256)})


def blob_table() -> dict[int, int]:
    """Every raw 8-neighbour mask mapped to a sheet index 0..46."""
    order = {m: i for i, m in enumerate(blob_masks())}
    return {m: order[blob_reduce(m)] for m in range(256)}


def rotate_corner(index: int) -> int:
    """Rotate a corner tile 90 degrees clockwise: TL->TR->BR->BL->TL."""
    tl, tr, bl, br = (bool(index & b) for b in (1, 2, 4, 8))
    return corner_index(bl, tl, br, tr)


def corner_classes() -> list[list[int]]:
    """Group the 16 corner tiles into shapes that are rotations of each other."""
    seen, classes = set(), []
    for i in range(16):
        if i in seen:
            continue
        group, j = [], i
        while j not in group:
            group.append(j)
            j = rotate_corner(j)
        seen.update(group)
        classes.append(sorted(group))
    return classes


TILE_COUNTS = {"corner": 16, "edge": 16, "blob": 47}


def autotile(grid: list[list[bool]], kind: str, outside: bool = False) -> list[list[int]]:
    h, w = len(grid), len(grid[0]) if grid else 0

    def at(x, y):
        return grid[y][x] if 0 <= x < w and 0 <= y < h else outside

    if kind == "corner":
        return [[corner_index(at(x - 1, y - 1), at(x, y - 1), at(x - 1, y), at(x, y))
                 for x in range(w + 1)] for y in range(h + 1)]
    if kind == "edge":
        return [[edge_index(at(x, y - 1), at(x + 1, y), at(x, y + 1), at(x - 1, y)) if grid[y][x] else -1
                 for x in range(w)] for y in range(h)]
    if kind == "blob":
        table = blob_table()
        offsets = ((0, -1, N), (1, -1, NE), (1, 0, E), (1, 1, SE), (0, 1, S), (-1, 1, SW), (-1, 0, W), (-1, -1, NW))
        return [[table[sum(bit for dx, dy, bit in offsets if at(x + dx, y + dy))] if grid[y][x] else -1
                 for x in range(w)] for y in range(h)]
    raise ValueError(f"unknown tile set {kind!r}")


def plan_sheet(tiles: int, tile_px: int, gutter: int = 0, max_side: int | None = None) -> tuple[int, int, int]:
    """Smallest-area power-of-two sheet (width, height, columns) for tiles of tile_px plus gutters."""
    max_side = max_side or platform("dc")["max_texture"]
    cell = tile_px + 2 * gutter
    sides = [1 << p for p in range(3, 11) if (1 << p) <= max_side]
    best = None
    for sw in sides:
        for sh in sides:
            cols, rows = sw // cell, sh // cell
            if cols and rows and cols * rows >= tiles:
                key = (sw * sh, abs(sw - sh), -sw)
                if best is None or key < best[0]:
                    best = (key, sw, sh, cols)
    if best is None:
        raise ValueError(f"{tiles} tiles of {cell} px do not fit in a {max_side} px sheet")
    return best[1], best[2], best[3]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("table")
    t.add_argument("kind", choices=TILE_COUNTS)
    m = sub.add_parser("map")
    m.add_argument("grid", type=Path)
    m.add_argument("--set", dest="kind", choices=TILE_COUNTS, required=True)
    m.add_argument("--outside-filled", action="store_true")
    p = sub.add_parser("plan")
    p.add_argument("--set", dest="kind", choices=TILE_COUNTS, required=True)
    p.add_argument("--tile", type=int, required=True)
    p.add_argument("--format", required=True)
    p.add_argument("--gutter", type=int, default=0)
    p.add_argument("--mips", action="store_true")
    p.add_argument("--pairs", type=int, default=1, help="terrain pairs, one tile set each")
    args = ap.parse_args()

    if args.cmd == "table":
        if args.kind == "blob":
            print(json.dumps({"masks": blob_masks(), "raw_to_tile": blob_table()}))
        else:
            print(json.dumps({"tiles": TILE_COUNTS[args.kind], "rotation_classes": corner_classes()}))
        return 0
    if args.cmd == "map":
        rows = [line.rstrip("\n") for line in args.grid.read_text().splitlines() if line.strip()]
        width = max(map(len, rows))
        grid = [[c == "#" for c in row.ljust(width)] for row in rows]
        for row in autotile(grid, args.kind, args.outside_filled):
            print(" ".join(f"{v:2d}" for v in row))
        return 0
    if args.tile < 1 or args.gutter < 0 or args.pairs < 1:
        ap.error("--tile and --pairs must be positive and --gutter nonnegative")
    fmt = get_format("dc", args.format)
    tiles = TILE_COUNTS[args.kind] * args.pairs
    try:
        sw, sh, cols = plan_sheet(tiles, args.tile, args.gutter)
    except ValueError as exc:
        ap.error(str(exc))
    size = texture_bytes("dc", fmt, sw, sh, args.mips)
    budget = platform("dc")["texture_budget_bytes"]
    print(f"{tiles} {args.kind} tiles of {args.tile} px (gutter {args.gutter}): {sw}x{sh} {fmt.tag}, "
          f"{cols} columns, {kib(size)} ({size / budget:.1%} of the {kib(budget)} planning budget)")
    if args.mips:
        print("warning: mipmaps blend neighbouring atlas tiles; gutters only delay it at small levels, so check distant views or skip mips")
    return 0


if __name__ == "__main__":
    sys.exit(main())
