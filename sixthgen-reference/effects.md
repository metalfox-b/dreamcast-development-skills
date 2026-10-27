# Faked effects

Every expensive effect has a cheap geometric **fake**. Each recipe names its source, its **platform tax** and how to check it. Credit the technique, never copy the asset ([originality guardrail](../sixthgen-reference/originality.md)).

Translucent triangles count against the Dreamcast ration (`check_model.py` → `translucent-share`). On PS2 they're cheap in fill but every extra texture costs GS VRAM.

## Mirror (no render-to-texture)
Source: Elias Daler (Project MTP).
1. Duplicate the room across the mirror plane with Blender's Mirror modifier; mirror moving actors with scale (−1, 1, 1) in the engine.
2. Lay one semi-transparent dirt/smudge texture on the glass plane.
- Tax: the duplicated geometry's tris and verts; one translucent quad. No second render, no render-target VRAM (DC has no cubemaps).
- Check: the room + mirror copy stays inside the scene budget for that camera.
- Real render-to-texture is for a real screen (Elias's in-game CRT running DOOM), not for reflections.

## Light halo and fake bloom
Sources: Elias Daler (halo technique taken from Ridge Racer 4), his Gouraud bloom.
1. Paint the light's falloff into the surrounding vertex colors.
2. Add a fan or ring of semi-transparent, untextured triangles around the source: vertex alpha high at the center, 0 at the rim, additive or alpha blend.
3. For bloom, place the same untextured Gouraud polygons over bright areas (windows, neon).
- Tax: translucent overdraw. Keep halos small on DC.

## Lens flare
Source: Rogério Perdiz (Soul Blaze).
1. Build a chain of textured quads along a line in Blender, one small flare texture (PAL4/ARGB4444) reused at several scales.
2. Our read (not stated): the engine slides the chain along the line from the sun's screen position through the screen center.
- Tax: a few translucent quads; one small texture.

## Fog
Sources: Elias Daler (Silent Hill-style fog: two weeks on PS1, a couple of lines with the DC fog table), Ninja Dynamics (fog hiding the city's streaming edge: the research's read of his screenshots).
1. Use the hardware fog table (DC) or per-vertex fog: pick a color that matches the sky's horizon.
2. Expose fog start/end, the table, and ambient/sun/sky colors in an on-device debug panel with a "dump to code" button (Elias's workflow).
- Tax: none on DC. Pairs with draw-distance culling.

## Vertex-color paintings and skies
Source: Elias Daler.
1. A grid of ~40–50 verts inside a frame; paint the image in vertex color (Kandinsky or Hiroshi Nagai styles suit it).
2. Skies: a dome or a big painted gradient, vertex color plus at most one cloud texture (Rogério painted a new Soul Blaze sky).
- Tax: verts only; no VRAM, no pixelation up close.

## Lightning and flashes
Source: Ninja Dynamics (HyperSolar).
1. Place a duplicate, over-exposed copy of the cloud layer behind the normal one.
2. Open temporary holes (alpha or hidden polygons) in the front layer to reveal it.
- Tax: one extra textured layer for the duration.

## Trees and foliage
Sources: Ninja Dynamics (two-card cross trees), Soul Blaze (alpha-cutout grass clumps, seen in screenshots, not stated).
1. Two quads crossed at 90°, one cutout texture (ARGB1555 / CI / DXT1), edge color bled into transparent texels.
- Tax: cutouts are punch-through, much cheaper than blended translucency on DC.

## Shadows
Source: Soul Blaze uses real shadow volumes and pays for them (locked 30 fps; "perhaps 40" without). Its screenshots also show a blob-like shadow, which is the research's read, not stated.
1. Static shadows go into vertex colors (bake). Always.
2. Moving actors, cheap: a blob or projected quad under each actor, darker vertex color or one small I/PAL texture. Tax: one translucent quad per actor.
3. Moving actors, real: DC modifier-volume shadows (what Soul Blaze ships). Tax: frame rate; budget for 30 fps. They need Flycast with a real BIOS to show in emulation.

## City and building kits
Source: Ninja Dynamics (HyperSolar).
1. Extruded boxes and hexagonal prisms (stated: hexagonal buildings). Emissive window textures (untouched by vertex light) and fog at the streaming edge are the research's read of his screenshots.
2. Assemble facades from random fragments of one base texture rather than unique textures.
- Tax: his whole DC frame used ~757 KB of 8 MB VRAM, which shows how far a small tiling set goes.

## Anamorphic storage
Sources: Rogério Perdiz (FMV), PS2Docs.
1. Store a texture or video squashed on one axis (half height), stretch it back with UVs or the scaler.
- Tax: half the VRAM; detail on the squashed axis.

## Detail mapping
Source: Halo: Dreamcast Evolved by @JiltedValkyrie (highlighted by Falco Girgis).
- Our read (the technique itself wasn't described): on DC, a second, translucent polygon layer carries a small tiling detail texture over a VQ base. On GC use the TEV, on Xbox a second texture stage, on PS2 a second pass.
- Tax on DC: doubles the translucent overdraw of the surface; keep to near surfaces.

## Debug overlays that keep art in budget
Sources: NewoGame (fixed-cap pools on screen), Elias Daler (texture viewer sorted by size).
- Show each pool as used/cap (e.g. buildings 476/512, display lists 54/128) and list textures by size on the device. Not an effect, but the cheapest way to keep effects and art inside the budget on hardware.
