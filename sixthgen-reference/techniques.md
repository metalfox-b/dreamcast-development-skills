# Sources and techniques, credited

Who the sixth-gen numbers and techniques come from, what is theirs, and what not to copy. The sources below provide technical background and examples; published work remains subject to its own rights. Verify project-specific decisions against the original sources and the target hardware. Use their techniques and published numbers; never their characters, models or textures ([originality guardrail](../sixthgen-reference/originality.md)).

## Practitioners

| Who | Platform | Work | What we take |
|---|---|---|---|
| Elias Daler (@EliasDaler, edw.is) | DC, PS1 | Project MTP (original) | Vertex-color lighting baked at load, VQ and the on-device texture viewer, mirrors by duplication, halos/bloom from Gouraud polys, fog table, triangle strips, budgets (cat 2,760 tris considered too high for a Dreamcast game; NPCs under 2K polys), Blender as level editor with a custom exporter. |
| Rogério Perdiz (@rogerioperdiz) + Miguel Ángel Alosete (@NekoEye), DarkPath Studio | DC | Soul Blaze | ~25k visible tris at 30 fps, ~60 KB per vertex-color channel, hard edges duplicate verts, lens-flare quad chains, quads for characters, anamorphic FMV, Shenmue ≤ ~14k verts measured in Deecy, Spiral Engine (Blender as editor, unreleased), shadow volumes (expensive) |
| Ninja Dynamics (@ninjadynamics) | PS2, DC | HyperSolar | PS2 vs DC trade-offs, VU1 for 60 fps, author for 8 bpp + dither, PS2Docs texture rules, over-exposed cloud lightning, cross trees, fragment-assembled building textures, BBA is a must |
| A Flock of Meese (@meesedev) | GC, Wii | Meese Engine (closed source; textures by Pixel Brush and LibreProg) | GameCube for SD/Swiss I/O, real CRT testing, overscan safe areas, tiling atlases |
| Owen / NewoGame (@NewoGame) | Wii | NewoZero, Newo Shooter | Engine first then art, fixed-cap debug pools, 24-hour soak tests, the Newo Shooter asset brief |
| @memorix101, @Ryzee119 | Xbox | raylib4Xbox, nxdk-gles11 | Toolchain only |
| Falco Girgis (@falco_girgis) | DC | KallistiOS lead, SH4ZAM | SH-4 CPU-side T&L trade-offs, PVR DR API |
| Rodrigo Copetti; KallistiOS/dreamcast.wiki; PS2Tek, PS2Docs, gsKit; libogc, YAGCD, Dolphin; xboxdevwiki | all | Docs | Hardware tables and texture formats |

## Gaps in the research

- Video posts (Spiral Engine tours, Elias's strips and fog) were seen as thumbnails only.
- No exporter code was available: Elias's is private, Spiral Engine unreleased, Meese Engine closed.
- No creator stated per-asset texture resolutions; image notes are estimates.
- No practitioner polygon budgets for PS2, GameCube or Xbox; Xbox max texture size unverified.
- GLdc, gsKit and ps2gl internals were reviewed at summary level only.

## Public sources

The linked material is background and attribution; it is not included in this repository and has its own terms.

- Dreamcast texture formats: [dreamcast.wiki](https://dreamcast.wiki/Texture_Formats), [KallistiOS PVR format reference](https://kos-docs.dreamcast.wiki/group__pvr__txr__fmts.html).
- PlayStation 2: [PS2Docs](https://github.com/ninjadynamics/PS2Docs), [PS2Tek texture reference](https://israpps.github.io/ps2tek/PS2/GS/Textures.html), [gsKit](https://github.com/ps2dev/gsKit).
- GameCube: [libogc texture formats](https://libogc.devkitpro.org/group__texfmt.html), [YAGCD graphics documentation](https://www.gc-forever.com/yagcd/chap17.html).
- Original Xbox: [XboxDevWiki XPR](https://xboxdevwiki.net/XPR), [nxdk-gles11](https://github.com/Ryzee119/nxdk-gles11), [raylib4Xbox](https://github.com/Memorix101/raylib4Xbox).
- Developer workflows and examples: [Elias Daler](https://edw.is/), [Soul Blaze](https://darkpath.itch.io/soul-blaze), [Ninja Dynamics](https://x.com/ninjadynamics), [A Flock of Meese](https://meese4.github.io/), [NewoGame](https://owensoft.net/project/newogame/).
- Platform architecture: [Dreamcast](https://www.copetti.org/writings/consoles/dreamcast/), [PlayStation 2](https://www.copetti.org/writings/consoles/playstation-2/), [GameCube](https://www.copetti.org/writings/consoles/gamecube/), and [Xbox](https://www.copetti.org/writings/consoles/xbox/) guides by Rodrigo Copetti.
