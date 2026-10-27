---
name: sixthgen-texture
description: Authentic sixth-gen textures for Dreamcast, PS2, GameCube or Xbox. Use when making, quantizing or validating a texture or palette (VQ, PAL4/PAL8, PSMT8, CMPR, DXT), choosing a texture size or format, or checking a VRAM tally.
---

# sixthgen-texture

Produces textures that are **authentic** for one **platform**: authored at the final size, in the platform's own format, inside the **VRAM tally**, with palettes planned. Hardware converters and PC renderers accept anything, so these scripts are what keep a texture sixth-gen.

The budget's `target` decides how hard the limits are: **hardware** fails on an over-budget tally or palette RAM; **style** warns. Every source follows the [originality guardrail](../sixthgen-reference/originality.md).

Scripts need Python 3.9+ and Pillow (`python3 -m pip install Pillow`); `preview_480.py --vq` also needs numpy. They import `scripts/sixfmt.py`, the single source of format rules, and read platform numbers from [platforms.json](../sixthgen-reference/platforms.json). `python3 scripts/test_sixfmt.py` checks the format math against the sources' published numbers.

## Naming

- Texture: `<name>.<fmt>.png`, e.g. `example_face.pal8.png`. Tags are per platform (`--platform dc|ps2|gc|xbox`); list them with `--cheat-sheet`.
- Lock file: `<name>.lock.txt` beside it, one `#RRGGBB` per line, for colors that must survive (eyes, logo).
- Preview: `<name>.preview.png`, written beside the texture.

## Steps

1. **Pick size + format.**
   - From the **budget** (`<asset>.budget.json`) if one exists; otherwise from the swaps table in [platforms.md](../sixthgen-reference/platforms.md#cross-platform-swaps) and the sizes in [budget.md](../sixthgen-reference/budget.md#texture-sizes).
   - Decision order: big noisy surface → the platform's compressed format (VQ, CMPR, DXT; PSMT8 + dither on PS2); flat color → palette; cutout → 1-bit alpha format; gradients that compression smears → 16-bit direct. Symmetric art → half width + mirror (not on PS2).
   - `python3 scripts/validate_textures.py --platform P --plan WxH FMT [--mips]` prints its bytes and share of the platform budget.
   - Done when: size, format, mips and tile modes are in the budget, and the planned set's total fits the platform budget.

2. **Get the source image.** Branch:
   - *Hand-painted* → create or request a source at the final size, according to the requested workflow.
   - *Photo / render* → use source material with suitable rights and record its license. Any size; step 3 box-downscales it.
   - *Procedural* (noise, gradients, simple prints) → the agent may generate it.
   - Done when: a source PNG exists and has a row in `textures/SOURCES.md`.

3. **Quantize.**
   `python3 scripts/quantize_texture.py --platform P SRC OUT.<fmt>.png --size WxH [--half-mirror x] [--colors N] [--dither ordered] [--palette-from TEX.png]`
   - Palette formats: one transparent entry, lock colors kept exact. On DC, give textures that can share colors one palette with `--palette-from`: palette RAM is 1024 entries for every texture.
   - VQ, CMPR and DXT tags write their base format's pixels (e.g. RGB565); the encoder runs at step 7.
   - Done when: it prints `[AUTHENTIC]` and no `locked color … matches no source pixels` warning.

4. **Key-feature pass** (faces, logos, signage). Open OUT at 400%+.
   - Broken features → repaint or hand off those texels, then re-run step 5 (not step 3, which would overwrite the repaint).
   - Done when: every key feature reads and it has been reviewed.

5. **Validate the set.** `python3 scripts/validate_textures.py --budget ASSET.budget.json <textures dir>`, exit 0 required. Read the **VRAM tally** line, and on DC the palette RAM line. `--json` for machine use; `--budget-bytes` when the project's framebuffer layout differs from the profile.
   - Done when: every texture is `[AUTHENTIC]`, the tally is inside the budget, and every budget texture matches its file.

6. **Preview.** `python3 scripts/preview_480.py --platform P OUT [--tile U,V --repeat U,V] [--shade TOP,BOTTOM] [--mips] [--vq] [--fb16]`
   - Shows the texture at 64/128/256 px on a 640×480 frame with hardware-style bilinear sampling. VQ tags get simulated VQ loss automatically; `--fb16` adds the dithered RGB565 framebuffer (PS2 16-bit, DC output).
   - VQ loss too visible on a key feature → switch that texture to a palette or 16-bit format and repeat from step 1.
   - Done when: key features are legible at the on-screen size, and the preview has been reviewed.

7. **Convert** (hardware targets). Run the project profile's texture conversion line ([platforms.md](../sixthgen-reference/platforms.md#project-profiles)): `pvrtex` on DC (twiddle, VQ, palette), on PS2 CLUT alpha 255 → 0x80 and the CSM1 CLUT swizzle for PSMT8, the project's GC or DXT converter otherwise. No conversion line yet → **hand-off**: select an appropriate tool and add it to the profile.
   - Done when: every converted file exists, and its size is within a few percent of its line in the tally.

## Quick reference

- Byte table (generated, never hand-edited): `python3 scripts/validate_textures.py --platform P --cheat-sheet [--mips]`
- Formats, palette rules, platform tax, swaps → [platforms.md](../sixthgen-reference/platforms.md)
- Texture style rules and review checklists → [authenticity.md](../sixthgen-reference/authenticity.md)
- Where the numbers come from → [techniques.md](../sixthgen-reference/techniques.md)

## Open

- DC palette entry format is global and set by the engine (`pvr_set_pal_format`); the scripts assume ARGB1555. Confirm on the first DC project and pass `--pal-format` if it differs.
- DC strided textures: the validator enforces width a multiple of 32 and power-of-two height, but not the single global stride; confirm with `pvrtex` and the engine before relying on `--allow-npot`.
- DC mipmapped textures must be square (warning only until confirmed).
