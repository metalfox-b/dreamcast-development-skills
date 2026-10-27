---
name: sixthgen-asset
description: Workflow for an original sixth-gen asset (character, NPC, prop, level piece or effect) for Dreamcast, PS2, GameCube or Xbox, from brief to a hardware or in-engine capture. Use when making or reviewing a sixth-gen asset, or faking an expensive effect (mirror, halo, bloom, lens flare, fog) for one.
---

# sixthgen-asset

Takes an original asset from brief to a **capture** on its **platform**. [sixthgen-texture](../sixthgen-texture/SKILL.md) and [sixthgen-model-check](../sixthgen-model-check/SKILL.md) do the checkable parts. Use the requested balance of agent work and artist hand-offs. The effects described here use geometry to approximate expensive rendering techniques.

Every design follows the [originality guardrail](../sixthgen-reference/originality.md). Platform facts come from [platforms.md](../sixthgen-reference/platforms.md); everything engine-specific (export route, texture conversion, scale, run, capture, repo rules) comes from the project's **project profile**. Read both first. If the project has no profile, use the template at the end of platforms.md to write one in the project before step 1.

The budget's `target` picks the finish line: **hardware** ends with the asset running on the console; **style** ends with an in-engine capture plus the 480p **preview**.

Tools: Blender 4.x, Python 3.9+ with Pillow (numpy for VQ previews), and the project's SDK.

## Steps

1. **Brief → budget.**
   - Ask only what's missing:
     - the platform (default Dreamcast) and the project
     - the `target`: hardware or style
     - kind: character, NPC, prop, level piece or effect
     - one or two lines of design, and any effects it carries (a lamp, a mirror, glass)
   - Write `<asset>.budget.json` from the [budget.md](../sixthgen-reference/budget.md) defaults. For PS2, GameCube and Xbox, say the defaults are Dreamcast numbers until the platform has its own.
   - Put the asset folder where the project profile says art lives.
   - Done when: the budget file exists and reflects the requested constraints.

2. **Design.** Use the supplied turnaround sketch or develop a written design within the requested scope. The agent writes design notes (silhouette, 3–5 color blocks, which detail is geometry and which is texture, where light falls) and checks them against the originality guardrail.
   - Done when: an approved front and side reference exists.

3. **Blockout and topology.** Prepare the blockout and topology within the requested scope:
   - a .blend at the profile's scale and axes, with the budget's tri split as a checklist in the text editor
   - an armature for characters (12–24 deform bones)
   - for level pieces, the profile's naming for collision and triggers: Blender is the level editor
   Model in quads, triangulate at export, keep hard edges deliberate.
   - Done when: `check_model.py` reports zero **build** findings and triangles within budget.

4. **UVs.** Lay out mirror halves and tiling strips as appropriate for the asset. Mirror only where the platform has it (not PS2). Textured parts map only to budget textures; `untextured` parts get none.
   - Done when: `check_model.py` reports no texture or `no-uvs` findings.

5. **Textures.** Run `sixthgen-texture` for every budget texture, steps 1–6 (step 7 comes at export).
   - Done when: every budget texture is `AUTHENTIC`, previewed, has a `SOURCES.md` row, and the set's **VRAM tally** fits.

6. **Vertex colors**, the step that makes it read as sixth-gen.
   - Bake a base layer (`sixthgen-model-check` step 4) → paint or refine it as requested, and it ends in the layer the exporter reads, within `color_channels`.
   - Done when: `check_model.py` reports no vertex-color findings and the shading has been reviewed.

7. **Effects.** For each entry in the budget's `effects`, build the matching **fake** from [effects.md](../sixthgen-reference/effects.md) (mirror by duplication, halo and bloom from Gouraud polygons, lens-flare quad chain, fog table, cross-card trees). No recipe fits → design one for the project from the same idea: geometry and vertex color first, translucency last.
   - Done when: every effect names its recipe, and `check_model.py` reports no `translucent-share` or `multi-texture` finding.

8. **Materials.** One color texture × vertex color per material. A two-texture look on DC is a second polygon layer or one baked texture; on PS2 a second pass; on GameCube the TEV; on Xbox a second stage. No PBR maps. Cutouts use punch-through alpha; blends only where the effect needs them.
   - Done when: materials are within budget and `check_model.py` passes.

9. **Rig.** One bone per vertex unless the budget says otherwise.
   - Done when: `check_model.py` reports no skinning findings.

10. **Export.** Follow the project profile's export route: the exporter, then `sixthgen-texture` step 7 to convert textures, then the build. No exporter yet → **hand-off**: it is engine work (Elias Daler puts it at half or more of development time); record the decision in the profile.
    - Done when: the engine loads the asset with no errors, and the project repo shows nothing the profile forbids.

11. **Test, capture and review.** Branch on `target`:
    - *hardware* → run it on the console through the profile's loader (Broadband Adapter, SD/Swiss, ISO), and **hand-off** for the capture through the scaler if the agent can't reach it. Emulators are for iteration only: they hide crashes and render differently (Flycast, Dolphin, PCSX2 all have known gaps). Read the on-device debug numbers (VRAM, pools, frame time) if the engine shows them.
    - *style* → run the engine as the profile says, open it in the built-in browser if it's a web build, and take the capture at 480p or the closest setting.
    - Both: preview each texture with `preview_480.py`, then review the capture and previews against both checklists in [authenticity.md](../sixthgen-reference/authenticity.md#review-checklist-looks-modern-mistakes).
    - Done when: the capture and previews have been reviewed against the brief. Blender renders are never presented as results.

## Reference pointers
- Budget fields and defaults → [budget.md](../sixthgen-reference/budget.md)
- Platform limits, tax, swaps and project profiles → [platforms.md](../sixthgen-reference/platforms.md)
- Effect recipes → [effects.md](../sixthgen-reference/effects.md)
- Style rules and review checklists → [authenticity.md](../sixthgen-reference/authenticity.md)
- Who the techniques come from → [techniques.md](../sixthgen-reference/techniques.md)
