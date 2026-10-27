# Dreamcast effect recipes

Choose effects for the game and test them with the actual renderer. The original practitioner posts linked below were identified in the research; some may require sign-in. The recipes are interpretations, not hardware guarantees.

## Mirror

Duplicate the visible scene across the mirror plane and render it as geometry; account for winding, culling, and depth. This trades extra geometry for avoiding a render-to-texture allocation. Render-to-texture is also possible on the PVR when the project can afford it. [Practitioner example](https://x.com/EliasDaler/status/2102774838188220526).

## Halo and bloom

Paint a light falloff into nearby vertex colors, then use a small fan or ring of translucent Gouraud-shaded polygons where needed. Restrict screen coverage and inspect overlapping translucent layers on hardware. [Halo example](https://x.com/EliasDaler/status/2108889722668069012); [Gouraud bloom example](https://x.com/EliasDaler/status/2084814994739167645).

## Lens flare

Use a chain of small textured quads along the line from the projected light toward the screen center. The exact placement is a design choice and should respond to visibility. [Practitioner example](https://x.com/rogerioperdiz/status/2093738691063656702).

## Fog

Use the PVR fog table or supported per-vertex fog to blend distant geometry into the horizon. Expose the color and distances during tuning; test on hardware. [KOS fog API](https://kos-docs.dreamcast.wiki/group__pvr__fog.html); [practitioner example](https://x.com/EliasDaler/status/2107289196821942690).

## Vertex-color paintings and skies

A small triangulated mesh with painted vertex colors can carry an abstract image or a gradient sky without a texture. Use this where the look suits the project and review interpolation in the running game. [Practitioner example](https://x.com/EliasDaler/status/2104550107777740868).

## Foliage and shadows

Crossed quads with an alpha-cutout texture can represent distant foliage. Baked vertex colors, small projected geometry, or shadow volumes are different tradeoffs; select and profile the method that fits the game. Texture alpha and translucent screen overlap must be tested in the renderer.

## City and building kits

Reuse a small atlas and repeated geometry for walls, windows, and modular buildings. Include silhouette variation and fog or distance treatment where the design calls for it; keep resource use visible in the project's debug display.
