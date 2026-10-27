# Native Dreamcast development

## Toolchain and build

Use the game's existing framework and build. For a new homebrew project, [KallistiOS](https://github.com/KallistiOS/KallistiOS) provides a Dreamcast SDK, cross-toolchain setup, and examples. Its [build documentation](https://github.com/KallistiOS/KallistiOS/blob/master/doc/README.md) describes configuring and sourcing the environment before building. Pin the SDK, compiler, ports, and asset converters in the project; verify their versions in the build environment.

Start with a small, observable change in the existing game or an SDK example. Build with the project's actual command and check that it produces the intended Dreamcast binary. A successful compile establishes only that the toolchain produced output; the emulator and console runs below are separate evidence. Do not silently replace a user's engine, SDK, ROM inputs, or build profile.

## Rendering, memory, and assets

- Choose the existing PVR or graphics abstraction deliberately. Respect the renderer's opaque, cutout, and translucent ordering, texture formats, alignment, and clipping. The official KOS examples include PVR rendering, palettes, and render-to-texture.
- The SH-4 performs game code and, depending on the engine, transformation, lighting, and skinning. Measure the scene rather than deriving a frame-rate promise from an asset's triangle count.
- Plan for the actual scene's texture memory. [KOS PVR allocation](https://kos-docs.dreamcast.wiki/group__pvr__mem__mgmt.html) exposes `pvr_mem_available()` and 32-byte-aligned allocations; [PVR profiling](https://kos-docs.dreamcast.wiki/group__pvr__stats.html) exposes rendering statistics. Record when measurements were taken and what was already loaded.
- Run the relevant Dreamcast asset checks, encode textures with the selected converter, and confirm the game's loader understands the file container, data layout, palette, and mipmaps. Compare the actual loaded asset and runtime allocations with estimates.
- Keep gameplay timing, input, audio, and save or storage behavior aligned with the game's target frame rate and device support. Use KOS's own input, sound, and filesystem examples when applicable. Treat platform-specific middleware and SDK components under their own licenses.

## Verification ladder

1. **Host tools:** run focused tests for the changed code or asset pipeline; confirm the expected files and errors. Texture previews are approximations.
2. **Cross-build:** build using the pinned Dreamcast environment. Record the binary and revision; do not imply it ran.
3. **Emulator:** launch the intended build, load the asset or scene, and exercise the requested interaction. Record the emulator and settings. An emulator result does not establish hardware correctness or performance.
4. **Real console:** use the project's supported loader or media, controller, and display. Record the console and video mode, revision, scene, observable interaction, frame behavior, available VRAM, and any audio or storage result relevant to the task. Repeat representative busy scenes. Record failures and missing access rather than substituting an emulator.

For visual acceptance, capture the actual game on the target device when possible. A generated texture preview or desktop render can guide iteration but does not establish the final appearance or frame rate on the console.
