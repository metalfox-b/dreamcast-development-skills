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
