# Dreamcast effect recipes

Choose effects for the game and test them with the actual renderer. The original practitioner posts linked below were identified in the research; some may require sign-in. The recipes are interpretations, not hardware guarantees.

## Mirror

Duplicate the visible scene across the mirror plane and render it as geometry; account for winding, culling, and depth. This trades extra geometry for avoiding a render-to-texture allocation. Render-to-texture is also possible on the PVR when the project can afford it. [Practitioner example](https://x.com/EliasDaler/status/2102774838188220526).

## Halo and bloom

Paint a light falloff into nearby vertex colors, then use a small fan or ring of translucent Gouraud-shaded polygons where needed. Restrict screen coverage and inspect overlapping translucent layers on hardware. [Halo example](https://x.com/EliasDaler/status/2108889722668069012); [Gouraud bloom example](https://x.com/EliasDaler/status/2084814994739167645).

Use `dreamcast-texture/scripts/fit_card_hull.py` on textured halo cards to reduce empty polygon coverage. Savings matter for punch-through and translucent lists; opaque overdraw is largely handled by the PVR's per-tile hidden-surface removal. Compare `pvr_get_stats()` before and after in a busy scene. Idea credit: gsimone's diet-sprite. See [era contrast](platforms.md#era-contrast) before considering full-frame effects.

## Lens flare

Use a chain of small textured quads along the line from the projected light toward the screen center. The exact placement is a design choice and should respond to visibility. [Practitioner example](https://x.com/rogerioperdiz/status/2093738691063656702).

## Fog

Use the PVR fog table or supported per-vertex fog to blend distant geometry into the horizon. Expose the color and distances during tuning; test on hardware. [KOS fog API](https://kos-docs.dreamcast.wiki/group__pvr__fog.html); [practitioner example](https://x.com/EliasDaler/status/2107289196821942690).

## Vertex-color paintings and skies

A small triangulated mesh with painted vertex colors can carry an abstract image or a gradient sky without a texture. Use this where the look suits the project and review interpolation in the running game. [Practitioner example](https://x.com/EliasDaler/status/2104550107777740868).

## Scene mood presets

Bundle a fog-table color and density/distances (or per-vertex fog), vertex tint and ambient gradient, sky gradient as geometry or a texture, and an optional PAL4/PAL8 palette-bank swap. These controls shape geometry and palettes rather than applying a full-screen grade. See the [example preset](mood-preset.example.json) and run `dreamcast-texture/scripts/validate_mood_preset.py` on it. Colors are RGB arrays in 0..1; distances are nonnegative project units with start no greater than end, and density is a normalized 0..1 tuning value. Map it to the renderer's fog table or vertex fog calculation; it is not a direct register value. Ambient gradients and tint are vertex-color inputs; the sky mode determines geometry or texture preparation. Test interpolation and fog on console.

Palette-bank indices run from 0 to 63 for PAL4 and 0 to 3 for PAL8, sharing 1,024 entries. A valid bank number does not reserve entries or guarantee matching encoded indices; coordinate banks across the scene. No full-screen grading, LUTs or post-process keys are accepted. Idea credit: gsimone's [mood-accurate scene post](https://x.com/ggsimm/status/2117302468035928324). See [era contrast](platforms.md#era-contrast) for full-frame costs and supported geometry alternatives.

## Foliage and shadows

Crossed quads with an alpha-cutout texture can represent distant foliage. Baked vertex colors, small projected geometry, or shadow volumes are different tradeoffs; select and profile the method that fits the game. Texture alpha and translucent screen overlap must be tested in the renderer.

Fit tight cards with `dreamcast-texture/scripts/fit_card_hull.py` where useful. Savings matter for punch-through and translucent lists; opaque overdraw is largely handled by the PVR's per-tile hidden-surface removal. Verify with `pvr_get_stats()` before and after in a busy scene. Idea credit: gsimone's diet-sprite.

## City and building kits

Reuse a small atlas and repeated geometry for walls, windows, and modular buildings. Include silhouette variation and fog or distance treatment where the design calls for it; keep resource use visible in the project's debug display.
