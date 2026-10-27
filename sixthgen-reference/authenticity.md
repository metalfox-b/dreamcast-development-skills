# Authenticity: sixth-gen limits as style rules

An asset is **authentic** when it reads as a 1999–2005 console asset made by hand for that machine: vertex-color light, small textures in the platform's own formats, effects faked with geometry. `validate_textures.py` and `check_model.py` enforce the checkable rules; this file holds the rest and the review checklist. Platform numbers are in [platforms.md](platforms.md).

## Light lives in vertex colors

- Bake once, then paint: AO and sun into a base layer (`../sixthgen-model-check/scripts/bake_vertex_colors.py`), hand-painted accents on top. Elias Daler computes static light once at level load; Shenmue's lighting is about 90% vertex color.
- 1–2 color channels per mesh. Each channel costs 4 bytes per vertex; Rogério Perdiz would put AO, alpha, specular, color variation and baked light all in vertex colors if it were free, but at 25k visible tris each channel is ~60 KB.
- Vertex color alone can carry art: Elias's painting is ~46 vertex-colored verts and no texture, which never pixelates up close and costs no VRAM. Gradient skies work the same way.
- Dynamic light is for the few things that move through changing light (Ninja Dynamics lights his jet per vertex on PS2). Everything static is baked.

## Textures

- Author at the final size and format, then dither to the limit. Never shrink a high-res texture through a posterize shader.
- 128²–256² for most surfaces; the extra room over N64 goes into texture detail that reads (a fabric weave on a chair, legible signage), not into size for its own sake. Shenmue's 256² posters look fine.
- Pick the format for the content: VQ for noise, palettes for flat color, 16-bit direct for gradients VQ smears. On DC, plan palette banks: the 1024 entries are shared by every texture.
- Bilinear filtering is the default look. Design features 2+ texels wide so they survive it; preview at the on-screen size (`preview_480.py`).
- Tiling atlases and repeat beat unique textures for buildings and terrain. Ninja Dynamics assembles buildings from random fragments of one base texture.

## Geometry

- Model in quads (easier to work with, per Rogério), triangulate at export.
- Hard edges duplicate vertices (adjacent faces need different normals). Keep them where the form is hard, smooth everywhere else, weld seams. Fewer splits also means longer triangle strips on DC (1.5–2× faster for Elias). Frogbull55's GTA3 DC bus dropped far more vertices than triangles, a sign of welding.
- Put silhouette detail into geometry and paint small detail into the texture.
- Remove hidden faces. Reuse geometry: the Soul Blaze team draws shared geometry twice to save memory.
- Graybox carelessly first on DC: the budget allows it, then optimize to budget.
- One bone per vertex.

## Effects

Fake every expensive effect with cheap geometry; recipes are in [effects.md](effects.md). Translucency is rationed on DC and cheap on PS2.

## Review checklist: "looks modern" mistakes

Review the **capture** (on the console for `hardware`, in the engine for `style`) and the **preview** against each line:

- [ ] Normal, roughness, metallic or specular maps, or any PBR material (`modern-material`).
- [ ] Real-time shadows or shading where baked vertex color would do. Shadows are expensive on DC: Soul Blaze's shadow volumes hold it at 30 fps ("perhaps 40" without them).
- [ ] Textures above 256² on ordinary surfaces, or detail finer than 2 texels.
- [ ] A posterize/dither shader over a high-res texture instead of a texture authored for the format.
- [ ] Two textures blended on one DC polygon (`multi-texture`).
- [ ] Large translucent overdraw on DC (`translucent-share`): halos and glass as small as possible, cutouts where possible.
- [ ] Render-to-texture mirrors or reflections where a mirrored duplicate would do.
- [ ] Bloom or glow from post-processing instead of Gouraud polygons.
- [ ] Hard edges everywhere (`split-heavy`) or smoothing that melts hard forms.
- [ ] Flat, unpainted vertex colors (`flat-vertex-colors`).
- [ ] UI or text outside the CRT overscan safe area (meesedev fixed this on real hardware).

## Review checklist: "still looks N64"

Sixth-gen isn't N64 with more polygons. Check for leftovers:

- [ ] 32²–64² blurry textures where 128²–256² would now carry real detail.
- [ ] 400–800 tri heroes with blocky silhouettes where 1–2k tris allow rounded forms.
- [ ] Two-texture N64 blends (e.g. the 2-layer ground) ported to DC; use layered polygons or bake.
- [ ] Props left in flat color with no baked light. At sixth gen every static mesh gets baked vertex light.

## What transfers from the N64 skills

Common transferable practices:

- **Directly**: vertex colors carry the shading; Rare-style random tinting; colored distance fog; painted textures; no hidden faces; mirrored UVs (DC, GC, Xbox; not PS2); real-hardware testing culture; the originality guardrail.
- **With changes**: CI4/CI8 thinking maps to PAL4/PAL8 (DC, global palette), PSMT4/PSMT8 (PS2), CI4/CI8 (GC), P8 (Xbox). The 4 KB TMEM ceiling becomes a total VRAM tally, so textures grow from 32–64² to 128–256². Hero budgets grow from 400–800 to 1–2.7k tris.
- **Not at all**: Fast64 and Tiny3D are N64-only; N64 3-point filtering is now bilinear; TMEM fit tables don't apply.
