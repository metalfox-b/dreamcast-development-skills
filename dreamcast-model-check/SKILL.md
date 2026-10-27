---
name: dreamcast-model-check
description: Check a Blender model against a Dreamcast project budget or bake a starting vertex-color layer. Use for triangle and estimated export-vertex counts, materials, skin weights, textures, and Dreamcast-style review.
---

# Dreamcast model check

The Blender script checks an evaluated mesh against the project's [budget](../dreamcast-reference/budget.md). It estimates vertex splits from positions, normals, UVs, and the active corner-color layer; the actual exporter may split or pack vertices differently. Rules live in the Blender-independent `scripts/model_rules.py`.

From this skill directory, run:

```sh
blender -b MODEL.blend --python scripts/check_model.py -- --budget ASSET.budget.json --json report.json
```

A hardware target fails for explicit triangle, vertex, bone, material, or skin-influence budget overruns and other build findings. A style target reports the aggregate model budgets as style findings. `--strict` makes all style findings fail as well; `--objects A,B` limits the selection. A missing mesh fails. Run the texture validator separately: this script checks referenced names, dimensions, and basic UV rules, not encoded PVR data.

A multi-bone vertex is **not automatically a hardware failure**. If `bone_influences` is absent, the checker offers a CPU-cost and exporter-compatibility reminder. If the project sets `bone_influences`, exceeding that explicit limit is a build finding. One bone per vertex is a common practice cited in [sources.md](../dreamcast-reference/sources.md#skinning-and-geometry), not a universal rule.

For a starting vertex-color pass:

```sh
blender -b MODEL.blend --python scripts/bake_vertex_colors.py -- --output OUT.blend
```

The bake uses ambient-occlusion rays and stylized lighting; it is a starting layer, not a final art review. Apply vertex-count-changing modifiers first, and ensure the exporter reads the resulting layer. `--force` permits overwriting an existing layer.

Inspect the actual exported asset in the game and profile the target scene. Passing this checker does not prove exporter compatibility or Dreamcast performance.
