---
name: sixthgen-model-check
description: Check a Blender model against a sixth-gen budget for Dreamcast, PS2, GameCube or Xbox. Use when checking a .blend's triangle or vertex count, vertex colors, skinning, textures or materials against a platform, or when baking vertex-color lighting for one.
---

# sixthgen-model-check

Headless Blender checks so a model is **authentic** for its **platform** and ready for the project's exporter. Counts come from the evaluated mesh (modifiers applied), including **export verts**: one per unique position + normal + UV + color, the number the console actually transforms.

Findings come in two kinds:
- **build**: the platform or a typical exporter breaks: unapplied transforms, zero-area faces, more bones per vertex than the budget allows, unweighted vertices on a skinned mesh, more textures blended on one polygon than the platform draws (more than one on DC), textures missing from the budget, wrong size or not power-of-two.
- **style**: works but won't read as sixth-gen, or wastes the budget: over the tri, export-vert, material or bone budget, **split-heavy** meshes (hard edges and seams duplicating vertices), missing or unpainted vertex colors, too many color layers, PBR maps (`modern-material`), translucency over the DC ration, multipass blends on PS2.

The budget's `target` doesn't change the findings; it changes how findings should be handled. On **hardware** targets every style finding over a budget is fixed, not accepted.

Scripts run in Blender 4.x (no add-on needed). The rules live in the bpy-free `model_rules.py`; `python3 scripts/test_rules.py` tests them without Blender. Platform numbers come from [platforms.json](../sixthgen-reference/platforms.json).

## Steps

1. **Load the budget and platform.** Read `<asset>.budget.json`; the platform's tax and limits are in [platforms.md](../sixthgen-reference/platforms.md).
   - Done when: a budget file exists with `platform` and `target`. If there isn't one, stop and have `sixthgen-asset` write it.

2. **Run the check.**
   `blender -b MODEL.blend --python scripts/check_model.py -- --budget ASSET.budget.json [--json report.json] [--strict]`
   - Exit 1 on any **build** finding; `--strict` also fails on **style**. `--objects A,B` limits the check; `--platform` overrides the budget's.
   - Done when: the verdict line is read and every finding is triaged in step 3.

3. **Fix or hand off**, per finding:
   - Mechanical, the agent fixes in bpy and re-runs step 2: `transform-not-applied`, `degenerate`, `modern-material` (rewire to color texture × vertex color, unlink the PBR maps), `color-channels` when the extra layers are empty or flat.
   - Texture findings (`texture-not-in-budget`, `texture-size`, `texture-npot`): run `sixthgen-texture`, or change the budget to match the agreed constraints.
   - Modeling, **hand-off** with the objects and counts from the report: `over-tri-budget`, `over-vert-budget`, `split-heavy`, `multi-texture` (layer a second polygon or bake one texture), `translucent-share` (cutouts instead of blends, smaller halos), `multi-bone-vertices`, `unweighted-vertices`, `over-bone-budget`.
   - Done when: zero **build** findings, and every **style** finding is fixed or, on a `style` target, explicitly accepted for the project.

4. **Bake vertex colors** (no painted layer yet, or a base pass is requested). The bundled bake is platform-neutral:
   `blender -b MODEL.blend --python scripts/bake_vertex_colors.py -- [--output OUT.blend] [--layer Col_Bake] [--seed N]`
   - Writes AO (warm lit, cool occluded), warm top light, root-to-tip limb darkening and soft tints. Apply Mirror/Subdivision modifiers first; `--force` to write into an existing layer.
   - Refine the bake as requested (accents, light pools, halos' falloff), then the layers merge into the one the project's exporter reads, so the mesh stays within `color_channels`.
   - Done when: step 2 reports no vertex-color findings.

## Reference pointers
- Budget fields and defaults → [budget.md](../sixthgen-reference/budget.md)
- Platform limits, tax and export routes → [platforms.md](../sixthgen-reference/platforms.md)
- Style rules and the review checklists → [authenticity.md](../sixthgen-reference/authenticity.md)
- Effect fakes behind `multi-texture` and `translucent-share` fixes → [effects.md](../sixthgen-reference/effects.md)

## Environment
- Tested on Blender 4.5.14 LTS on a generated rigged test model, with the bundled bake run on the same file. Split normals come from `corner_normals` (Blender 4.1+), `calc_normals_split` before that.

## Still to verify
- Export-vert count against a real exporter's vertex count (it may also split by strips or batch by material).
- The DC translucency guide (15% of an asset's triangles) is a starting guess; tune it from hardware captures.
- The color layer name each project's exporter reads; record it in the project profile.
