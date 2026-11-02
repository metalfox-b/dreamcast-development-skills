# Dreamcast visual review

These are design and performance prompts, not a promise of hardware performance. Use them alongside the project's brief and real captures.

## Lighting and materials

- Consider baked or painted vertex-color lighting for static assets. Use dynamic lighting where the game needs it and the CPU budget permits it. Choose color-attribute layers that the exporter actually reads.
- Design material graphs for the game's renderer. Where a desktop material relies on shader effects the runtime does not implement, bake or rework them. Multiple textures can need additional PVR passes or layers.
- Use vertex-color gradients and untextured geometry where they serve the design. Keep hard edges deliberate; UV, normal, and color seams can duplicate export vertices.

## Textures and effects

- Author for the intended on-screen size. Try VQ on large noisy images, palettes for crisp limited-color art, and direct 16-bit formats where compression damages features. Review what the actual encoder produces.
- Plan palette banks globally. Reuse requires matching encoded indices and the palette selected by the game, not just visually similar PNGs.
- Prefer simple effects when they produce the requested look. [Effects](effects.md) provides sourced recipes for mirrors, halos, fog, and more. Measure translucent *screen coverage and overlap* in the game.

## Capture review

- [ ] The target device, video mode, and intended frame rate are recorded.
- [ ] The asset's silhouette, color, and key texture details read in an in-game capture.
- [ ] Texture filtering, cutout edges, mipmaps, palette selection, and any VQ artifacts are checked at actual display size.
- [ ] Animation, geometry, collision, and material behavior match the project brief.
- [ ] Busy scenes stay within the project's measured CPU, frame-time, RAM, and VRAM budgets.
- [ ] Emulation and hardware results are labeled separately; a Blender render or 480p texture preview is not a console capture.

- [ ] Record exact image differences with `dreamcast-texture/scripts/compare_images.py` for VQ preview versus pvrtex-decoded output, emulator versus console capture, and before/after asset changes. Keep dimensions and alignment equal, record hashes, versions and capture settings, and explain capture-chain differences.
- [ ] Review videos with `dreamcast-dev/scripts/capture_contact_sheet.py capture.mkv --out review`. Inspect `report.md`, `transitions.csv` and `contact-sheet.png` for NO CHANGE, TINY CHANGE (under 0.05 percent of pixels), and possible one-frame pops. Motion, intentional holds and capture noise can also trigger flags; inspect the video in context. Missing ffmpeg or ffprobe is a reported skip.
- [ ] Optional `preview_480.py --display svideo|composite` outputs are labeled display simulations. Never bake these into assets or use them as captures. VGA remains the sharp default; no simulation proves the console's display output.
