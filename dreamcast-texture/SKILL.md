---
name: dreamcast-texture
description: Prepare, quantize, validate, preview, and plan memory for Sega Dreamcast textures. Use for PVR RGB565, ARGB1555, ARGB4444, PAL4, PAL8, VQ, palette banks, and pvrtex conversion.
---

# Dreamcast textures

The scripts prepare and check PNG source images; they do not write Dreamcast texture binaries. Read [platforms.md](../dreamcast-reference/platforms.md#texture-planning) and the project's loader profile. The Dreamcast's PVR texture formats and flags are documented by [KallistiOS](https://kos-docs.dreamcast.wiki/group__pvr__txr__fmts.html).

From this skill directory:

1. **Plan.** Choose an appropriate format and dimensions, and record the planned set in the [asset budget](../dreamcast-reference/budget.md). For an estimate:
   ```sh
   python3 scripts/validate_textures.py --platform dc --plan 256x256 vq565 --mips
   ```
   The default 6 MiB texture budget is a planning estimate. Use `--budget-bytes` for the game's measured available budget. The texture and palette tallies exclude some container, alignment, loader, and runtime overhead.
2. **Prepare.** Obtain original or appropriately licensed source art and record its provenance. Quantize to a named PNG:
   ```sh
   python3 scripts/quantize_texture.py source.png face.pal8.png --size 64x128
   python3 scripts/quantize_texture.py source.png wall.vq565.png --size 256x256
   ```
   `--lock FILE` preserves chosen colors, `--dither ordered` applies ordered dithering, and `--half-mirror x` prepares symmetric art. VQ-tagged PNGs contain base-format pixels; VQ compression occurs in the encoder. `--palette-from` limits the PNG colors but alone does not guarantee shared hardware palette indices. The helper quantizes paletted PNG alpha to transparent or opaque; other palette-alpha workflows need an appropriate converter.
3. **Validate and preview.**
   ```sh
   python3 scripts/validate_textures.py --platform dc --budget ASSET.budget.json textures/
   python3 scripts/preview_480.py wall.vq565.png --vq
   ```
   Hardware is the default target. An explicit `style` target warns on aggregate memory overruns. `[PASS]` means the PNG passed these checks; it is not an encoded or hardware-tested asset. The 480p preview is an approximation and VQ preview requires NumPy. Validate actual mip chains and palette assignments after encoding.
4. **Convert.** Use the exact options and container expected by the project's loader. For example, with KOS `pvrtex`:
   ```sh
   pvrtex -i wall.vq565.png -o wall.dt -f rgb565 -c 256
   pvrtex -i face.pal8.png -o face.dt -f pal8bpp
   ```
   The paletted conversion also writes a `.pal` file. Use a shared palette with `pvrtex -P` where the game expects a shared bank, and confirm the encoded indices and game palette setup. The `.dt` container is not automatically understood by every loader. `--allow-npot` allows valid non-power-of-two direct or VQ strided inputs; the encoder and runtime must agree on stride, and strided mipmaps are not supported by this helper.
5. **Run and review.** Load the converted texture in the actual game, inspect it in a representative scene, and measure runtime memory. Report host-side conversion, emulator behavior, and real-console behavior separately.

## Card hulls and exact comparison

```sh
python3 scripts/fit_card_hull.py foliage.png --vertices 8 --threshold 0 --out foliage.hull.json
python3 scripts/fit_card_hull.py smoke.png --grid 4x4 --shared --out smoke.hull.json
python3 scripts/compare_images.py before.png after.png --out difference.png --meta device=console --meta video=VGA
```

Card hulls cover whole pixels whose alpha is strictly above the threshold. The original Andrew monotone-chain implementation starts from pixel corners and expands during reduction, never cutting into the occupied hull. The vertex target defaults to 8, with a minimum of 3; empty frames have no vertices or triangles. If reduction stalls, a conservative bounding rectangle is used when the budget permits. A triangle that cannot cover the pixels within image bounds fails clearly; pad the source or increase the limit. JSON contains frame-local pixel vertices, UVs with U right and V down from the top left, fan triangles, polygon and full-quad areas, and saved fraction. Flipbook order runs left to right, then downward. Apply the frame's atlas offset and scale to the local UVs; `--shared` covers every frame with one polygon. Check winding against the engine's culling convention. Bilinear filtering can sample beyond the threshold silhouette; choose a conservative threshold or add padding for the project's filtering. Idea credit: gsimone's diet-sprite; algorithm reference: Project Nayuki. No source code was copied.

The image comparison requires equal dimensions and never resizes. Its unamplified RGB difference PNG and JSON record zero-tolerance decoded-byte errors, input SHA-256 hashes and repeated `--meta key=value` evidence. Alpha is excluded unless `--include-alpha` is set; then errors include alpha and a separate `.alpha.png` shows its unamplified difference. `exact` means zero differing selected bytes; it does not establish hardware accuracy. Use aligned captures with matching settings and record differences in device or capture chain. Method idea: gsimone's typegpu-crt-shaders.

## Display simulations and scene moods

`preview_480.py --display vga` is the unchanged default: a sharp 640x480 frame saved at 2x. Opt-in `--display svideo` or `--display composite` separates luma and chroma, softens chroma horizontally more than luma, and adds light scanlines. These are display simulations, not calibrated signal emulation. Optional `--shadow-mask` uses a Lottes-style aperture grille. The image carries a visible DISPLAY SIMULATION label and a `.svideo-480i-sim.png` or `.composite-480i-sim.png` suffix (`.svideo-sim.png` or `.composite-sim.png` with `--no-interlaced`), including with `--out`. `validate_textures.py` skips every `-sim.png` file. Never bake simulations into assets or use them as captures. No LUTs or Hyllian math are used.

S-video and composite simulations are 480i by default: each line mixes 1-2-1 with its neighbours, approximating the vertical smoothing ("flicker filter") that KallistiOS enables for interlaced non-VGA modes and disables on VGA. Use `--no-interlaced` for a progressive TV mode; `--interlaced` is still accepted and keeps the default. VGA never gets the smoothing and rejects both flags. Thin one-pixel lines and 1-pixel text soften or vanish under it; check HUD text and fine texture detail that way. With `--fb16`, `--no-dither` snaps to RGB565 without dither, so you can judge banding for a game that turns framebuffer dithering off.

Validate the [example scene mood](../dreamcast-reference/mood-preset.example.json) with `python3 scripts/validate_mood_preset.py ../dreamcast-reference/mood-preset.example.json`. The [recipe](../dreamcast-reference/effects.md#scene-mood-presets) maps only to fog, vertex colors, sky geometry or textures, and optional shared palette-bank swaps. The validator rejects unknown keys and post-effect controls; an engine must still implement and verify the preset.
