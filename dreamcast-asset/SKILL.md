---
name: dreamcast-asset
description: Create or review Dreamcast-native game assets, including characters, props, level pieces, textures, vertex lighting, and inexpensive effects. Use from asset brief through export and hardware capture.
---

# Dreamcast asset workflow

Work from the project brief and the requested division of artist and agent work. Read [platforms.md](../dreamcast-reference/platforms.md), [budget.md](../dreamcast-reference/budget.md), and the project's asset profile. Use the project's real exporter and loader; if unknown, document what is missing. Follow [asset source guidance](../dreamcast-reference/originality.md).

1. **Brief and budget.** Identify the asset, visual direction, game, expected scene, target video mode, and intended hardware. Write an asset budget next to the source art. Treat supplied limits as project limits; starting ranges are estimates. `target: hardware` is the default. Use `style` only when explicitly requested and label it accordingly.
2. **Design and model.** Develop the reference and topology within the requested scope. Use the project's scale, axes, collision names, skeleton, and material conventions. Preserve editable source files. Choose where silhouette, texture, and vertex color carry detail.
3. **Check the mesh.** Run [dreamcast-model-check](../dreamcast-model-check/SKILL.md) on the evaluated model and fix build findings. Review style findings against the project; a style heuristic is not a hardware rule. Record any exporter-specific bone-influence limit instead of assuming one.
4. **Prepare textures.** Use [dreamcast-texture](../dreamcast-texture/SKILL.md) to size, quantize, estimate memory, and preview each texture. Record sources and licenses. Encode with the project's real converter, and verify the format, palette, layout, mipmaps, and loader agree.
5. **Light and add effects.** Bake or paint vertex colors as requested, making sure the exporter reads the intended layer. Use the appropriate recipes in [effects.md](../dreamcast-reference/effects.md); measure translucent overlap and costs in the actual scene.
6. **Export and integrate.** Run the project-specific model exporter, convert the textures, build the game, and load the asset in the engine. A successful PNG check, Blender render, or file conversion is not evidence of a working game asset.
7. **Review.** Inspect the asset, motion, materials, and frame behavior in an in-game capture using [authenticity.md](../dreamcast-reference/authenticity.md). For a hardware target, verify on a real console when available; report emulator and hardware results separately. If hardware is unavailable, deliver the asset and clearly mark real-device validation as outstanding.
