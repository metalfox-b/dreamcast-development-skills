# Autotiling with Wang and blob tiles

Use this for tiled ground, paths, walls and other 2D or top-down layers, and for flat terrain painted onto a 3D grid. You paint terrain per cell; a bitmask of matching neighbours picks the tile, so grass meets dirt without hand placement. The method is engine-agnostic. The Dreamcast notes below are planning guidance; measure the actual scene.

## Choose a set

Wang tiles label each tile's corners or edges with a terrain. Neighbouring tiles fit when the labels they share match.

| Set | Bits that pick the tile | Tiles for two terrains | Good for |
|---|---|---|---|
| Corner | 4 corners | 16 | Ground blends such as grass to dirt |
| Edge | 4 sides | 16 | Paths, roads, pipes, fences |
| Blob | 4 sides plus 4 diagonals | 47 | Any shape, including one-tile strips and inner corners |

A blob mask has 256 raw combinations. A diagonal neighbour counts only when both sides next to it also match, which leaves 47 distinct tiles.

With n terrains, a full corner or edge set needs n^4 tiles: 81 for three and 256 for four. Instead, keep one 16-tile set for each pair of terrains that actually touch, or layer terrains: draw a base fill, then each higher terrain as its own autotiled layer on top.

**Dual grid.** Keep terrain on the world grid, but draw tiles on a grid offset by half a tile. Each drawn tile then covers the shared corner of four world cells and becomes a corner tile. Two terrains need 16 tiles, which are 6 shapes plus their rotations: the two solid fills, one corner, a straight edge, a diagonal pair and an inner corner. Collision and gameplay stay on the world grid; only drawing moves.

## Bit layout and the script

`dreamcast-texture/scripts/autotile.py` holds the lookups:

- Corner: top-left 1, top-right 2, bottom-left 4, bottom-right 8.
- Edge: north 1, east 2, south 4, west 8.
- Blob: N 1, NE 2, E 4, SE 8, S 16, SW 32, W 64, NW 128. It reduces each mask, then maps it to a sheet index from 0 to 46 in ascending mask order.

```sh
python3 scripts/autotile.py table blob            # 47 masks and the 256-entry lookup as JSON
python3 scripts/autotile.py map level.txt --set blob
python3 scripts/autotile.py plan --set blob --tile 32 --format pal4
```

`map` reads a text grid where `#` is the filled terrain and prints one tile index per cell. Empty cells print -1 for edge and blob sets. The corner set prints the dual grid, one row and column larger. Store the same table in the game as a 256-byte array. The lookup runs when a level loads or a cell changes, not every frame.

## Dreamcast fit

- **Everything is polygons.** The PVR has no tilemap or sprite layer hardware. Each visible tile is a textured quad. At 16-pixel tiles, a 640x480 screen shows 40x30 tiles, or 41x31 while scrolling, which is about 1,271 quads and 2,542 triangles for one layer. Build each layer as strips or quads and reuse vertex buffers where the renderer allows. Count each layer separately.
- **One sheet per layer.** A polygon uses one texture, so put a layer's whole set on one sheet. That avoids texture changes inside the layer.
- **Lists.** Draw solid ground in the opaque list; the PVR's per-tile hidden-surface removal makes overlapping opaque layers cheap. Overlay terrain with cutout edges belongs in the punch-through list, using PAL4 or PAL8 with a transparent index, or ARGB1555. Keep soft-edged translucent tiles rare and measure their overlap with `pvr_get_stats()`.
- **Twiddled sizes.** Twiddled textures need power-of-two sides, from 8 to 1,024 in these tools. `autotile.py plan` picks the smallest power-of-two sheet for the set and estimates its size with the plugin's format table. For example, 47 blob tiles at 32 pixels fit a 256x256 sheet of 8 columns. As PAL4 that is 32 KB of a 6 MiB planning budget; as RGB565 it is 128 KB. Strided textures allow other widths but no mipmaps; see [texture planning](platforms.md#texture-planning).
- **Formats.** Crisp pixel-art tiles usually suit PAL4 or PAL8. VQ compresses blocks of pixels, so it can smear tile borders and hard pixel edges; preview with `preview_480.py --vq` before using it on a sheet. Record every sheet in the [asset budget](budget.md).
- **Palette banks.** Give each terrain pair a PAL4 bank. Seasons or times of day can swap banks without touching the sheet, as in [scene mood presets](effects.md#scene-mood-presets). Banks share 1,024 palette entries.
- **Sampling and bleed.** Point sampling keeps pixel art sharp. Bilinear filtering and mipmaps mix in pixels from the next tile on the sheet. Add a gutter of repeated edge pixels (`plan --gutter 1`), inset UVs by half a texel, or skip mipmaps on the sheet. Gutters only delay mip bleed at small levels; check distant views in a capture.
- **Animation.** For animated water or lava, change the UVs to another frame on the same sheet. Keep the frames on one sheet so the layer stays in one texture.
- **3D ground.** On a 3D grid terrain, each quad can take its tile's UVs from the same lookup. Vertex-color blends between two textured passes are an alternative that costs extra translucent fill; compare both in the scene.

## Tools

These are free tools that can author tile sets and rule-based autotiling. They are optional and not bundled. Licenses were checked on Nov 3, 2026:

- [Tiled](https://www.mapeditor.org): Wang sets for corner, edge and mixed tiles. The editor and plugins are GPL version 2; libtiled, tmxviewer and tmxrasterizer are BSD 2-clause ([COPYING](https://github.com/mapeditor/tiled/blob/master/COPYING)). Export JSON or TMX and convert it with the project's own loader.
- [Godot 4](https://docs.godotengine.org/en/stable/tutorials/2d/using_tilesets.html): TileSet terrains with "Match Corners and Sides" and "Match Corners" modes. MIT.
- [LDtk](https://ldtk.io): auto-layer rules and presets. MIT.
- [Pixelorama](https://github.com/Orama-Interactive/Pixelorama): pixel-art editor with a tile mode for seamless drawing. MIT.
- [LibreSprite](https://github.com/LibreSprite/LibreSprite): pixel-art editor. GPL version 2.

Aseprite is paid and ships under a proprietary EULA, so it is not recommended here. A tool's license covers the tool, not tilesets, sample maps or art made by others; check each asset's own license before use.

## Credits

Idea credit: [asynkimo's Wang tiles post](https://x.com/asynkimo/status/2117697739157041432); Boris the Brave's [Classification of Tilesets](https://www.boristhebrave.com/2021/11/14/classification-of-tilesets/) and his [archive of the cr31 blob page](https://www.boristhebrave.com/permanent/24/06/cr31/stagecast/wang/blob.html); Oskar Stålberg's [Beyond Townscapers](https://www.youtube.com/watch?v=Uxeo9c-PX-w) talk and jess::codes' [dual-grid video](https://www.youtube.com/watch?v=jEWFSv3ivTg). `autotile.py` is an original implementation; no code from these sources or the tools above is included.
