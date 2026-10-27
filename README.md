# Sixth-Gen Asset Skills

Three agent skills for creating and checking original assets in the style of Dreamcast, PlayStation 2, GameCube, and the original Xbox.

- **sixthgen-asset**: plan an asset, set a budget, and follow it through modeling, texturing, effects, export, and capture.
- **sixthgen-model-check**: check a Blender model against a budget and bake a starting vertex-color layer.
- **sixthgen-texture**: plan formats and memory use, quantize images, validate textures, and preview them at 480p.
- **sixthgen-reference**: shared platform notes, budget schema, style guidance, sources, and effect recipes. All three skills need this folder beside them.

The hardware target calls for a real-console check. The style target uses the same constraints as guidance for an engine capture. Budget numbers are starting points, not guarantees of hardware performance: measure and adjust them for the project. The Python tools produce and validate PNGs; hardware texture encoding and model export require project-specific tools.

## Install

Clone or download this repository, open a terminal in its folder, and install all four folders together. For Codex:

```sh
python3 install.py --target "$HOME/.codex/skills"
```

For Claude Code:

```sh
python3 install.py --target "$HOME/.claude/skills"
```

The installer stops if any destination already exists, so it will not overwrite existing skills. Restart the agent or start a new session if necessary for it to discover the skills. You can also copy the four folders manually into another compatible agent's skills directory, keeping them as siblings.

## Requirements

- Python 3.9 or later.
- Pillow for the texture scripts; NumPy is also needed for vector-quantization previews. Install them in your preferred Python environment with `python3 -m pip install Pillow numpy`.
- Blender 4.1 or later for model checking and the vertex-color bake.
- An appropriate exporter, texture converter, and development tools for the target engine or console.

Run the included checks from the repository root:

```sh
python3 sixthgen-model-check/scripts/test_rules.py
python3 sixthgen-texture/scripts/test_sixfmt.py
```

The model rules and format tests run without Blender or Pillow. See each `SKILL.md` for workflow and command details, and [the source notes](sixthgen-reference/techniques.md) for technical references and credits.

## License

The files in this repository are provided under the [MIT License](LICENSE). Referenced third-party projects, documentation, trademarks, and artwork remain subject to their own rights and licenses.
