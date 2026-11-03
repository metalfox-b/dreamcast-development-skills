# Dreamcast Development Skills

Four agent skills for building native Sega Dreamcast games and creating their assets:

- **dreamcast-dev**: native game development, KallistiOS builds, profiling, emulator checks, and real-console verification.
- **dreamcast-asset**: asset briefs, budgets, modeling, textures, effects, export, and capture.
- **dreamcast-model-check**: Blender checks against a project budget and a starting vertex-color bake.
- **dreamcast-texture**: Dreamcast PNG preparation, memory estimates, previews, and conversion guidance.
- **dreamcast-reference**: shared platform notes, source citations, budgets, effect recipes, and autotiling notes used by the skills.

The package targets the Dreamcast only. It does not include a game engine, the KallistiOS SDK, a cross compiler, an emulator, or a universal model exporter. Use the project's own tools and loader. A passing host-side check or an emulator run does not prove an asset works on a physical console.

## Install

Clone or download this repository, open a terminal in its folder, and install all five folders together. For Codex:

```sh
python3 install.py --target "$HOME/.codex/skills"
```

For Claude Code:

```sh
python3 install.py --target "$HOME/.claude/skills"
```

The installer checks all destinations before copying and will not overwrite existing folders. Restart the agent or start a new session if necessary. You can also copy the five folders manually into a compatible agent's skills directory, keeping them as siblings.

## Requirements and checks

Use Python 3.9 or later; install Pillow for texture tools and NumPy for VQ previews. Blender 4.1 or later is needed for model checking and the vertex-color bake. Native game builds additionally need the project's Dreamcast SDK, compiler, exporter, and texture converter.

```sh
python3 -m pip install Pillow numpy
python3 dreamcast-model-check/scripts/test_rules.py
python3 dreamcast-texture/scripts/test_dcfmt.py
python3 dreamcast-texture/scripts/test_texture_workflow.py
python3 dreamcast-model-check/scripts/test_blender_workflow.py
```

Additional behavior checks:

```sh
python3 test_install.py
python3 dreamcast-texture/scripts/test_fit_card_hull.py
python3 dreamcast-texture/scripts/test_compare_images.py
python3 dreamcast-texture/scripts/test_preview_display.py
python3 dreamcast-texture/scripts/test_validate_mood_preset.py
python3 dreamcast-texture/scripts/test_autotile.py
python3 dreamcast-dev/scripts/test_toolchain_lock.py
python3 dreamcast-dev/scripts/test_capture_contact_sheet.py
```

Capture review uses local ffmpeg and ffprobe; its integration test skips when either is absent. The installer includes the four license and notice files in the installed reference folder.

The existing workflow tests use Blender or `pvrtex` when available; set `BLENDER` or `PVRTEX` to the executable path if needed. Missing tools are reported as skipped. The tests generate their own temporary sample assets and do not test a physical console.

See [source notes](dreamcast-reference/sources.md) for direct technical documentation and practitioner attribution. See the [Credits](dreamcast-reference/sources.md#credits) for technique ideas and upstream display references. The retained budgets are planning defaults that require project-specific measurement.

## License

Python code, including scripts, installer and tests, is under [PolyForm Noncommercial 1.0.0](LICENSE). Skills, reference material, README and other documentation are under [CC BY-NC 4.0](LICENSE-CONTENT). See [NOTICE](NOTICE) for the required copyright notice and [THIRD_PARTY.md](THIRD_PARTY.md) for third-party rights.
