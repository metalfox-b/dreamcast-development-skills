---
name: dreamcast-dev
description: Develop, debug, profile, or validate native Sega Dreamcast homebrew games. Use for KallistiOS, PVR rendering, SH-4 gameplay code, controller or audio integration, builds, emulator checks, and real-console testing.
---

# Dreamcast game development

Build for the actual Dreamcast when hardware is the target. Treat a PC preview, an emulator run, and a real-console run as separate results. Use the project's existing engine, SDK, build system, and asset formats; for a new project, KallistiOS is a common homebrew SDK. Read [development notes](../dreamcast-reference/development.md) for the build, profiling, and hardware-test workflow.

1. Inspect the project and its instructions. Identify the KOS and compiler versions, renderer, loader, video mode, asset pipeline, build command, and target hardware. Record unknowns in the project's profile using [platforms.md](../dreamcast-reference/platforms.md#project-profile). Do not assume a cross compiler, emulator, or connected console exists.
2. Implement the requested game or engine change using the project's existing architecture. For a new native project, use the SDK's official examples and API docs as starting points. Account for the SH-4 CPU, PVR texture and draw behavior, memory, controller input, audio, and storage as relevant to the change. Use [sources.md](../dreamcast-reference/sources.md) for direct references.
3. For new art, use [dreamcast-asset](../dreamcast-asset/SKILL.md); use [dreamcast-model-check](../dreamcast-model-check/SKILL.md) and [dreamcast-texture](../dreamcast-texture/SKILL.md) for the measurable parts. Integrate the actual converted files using the game's loader. A prepared PNG is not encoded PVR texture data.
4. Run focused tests, then build with the project's configured Dreamcast toolchain. Check the build result and output architecture. Exercise the game in an emulator when available; verify the affected interaction, not just that the process opens.
5. Test on the actual console when access and an appropriate loader are available. Record build revision, hardware, video mode, scene, input, frame behavior, available VRAM, and observed result. Where the SDK supports them, use `pvr_get_stats()` and `pvr_mem_available()` in the running scene. See [development.md](../dreamcast-reference/development.md).

Report exactly which steps passed. If a cross compiler, loader, emulator, or console is unavailable, leave that step unverified. Do not present a texture-script pass, an ELF file, or an emulator screenshot as proof of real-hardware behavior.
