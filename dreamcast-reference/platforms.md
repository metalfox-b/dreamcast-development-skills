# Dreamcast hardware and project profiles

The Dreamcast uses an SH-4 CPU and PowerVR2 graphics. KallistiOS (KOS) is a homebrew development SDK; its [PVR texture-format reference](https://kos-docs.dreamcast.wiki/group__pvr__txr__fmts.html), [VRAM allocator](https://kos-docs.dreamcast.wiki/group__pvr__mem__mgmt.html), and [profiling API](https://kos-docs.dreamcast.wiki/group__pvr__stats.html) document the interfaces used here. [Sources](sources.md) also links the specific practitioner reports behind the artistic guidance.

## Texture planning

- The normal console has 8 MiB of PVR RAM shared by the framebuffers and other graphics allocations. The scripts start with a **6 MiB texture budget as an estimate**, not a guaranteed free amount. Measure the project's actual pool with `pvr_mem_available()` after initialization and fixed allocations but before allocating the textures in the tally, then pass the appropriate `--budget-bytes`. If measuring later, account for textures already resident. Allow for loader, mipmap, alignment, and allocation overhead.
- `rgb565`, `argb1555`, and `argb4444` describe direct 16-bit color. `pal4` and `pal8` use globally shared palette RAM. `vq565`, `vq1555`, and `vq4444` refer to VQ-compressed textures and a base color format. The scripts prepare and check PNG pixels; a converter such as `pvrtex` creates the encoded data.
- Palette RAM contains 1,024 entries shared across banks. A color-set estimate cannot prove two encoded textures use the same indices or bank. A game must set the palette format and bank consistently with the encoder's palette output.
- The scripts support power-of-two texture dimensions from 8 to 1,024, with 512 as a practical review threshold rather than a hardware limit. `--allow-npot` permits a constrained direct or VQ strided path: width must be a multiple of 32, height must be a power of two, and mipmaps are disallowed. The stride is shared global state; verify it against the project's loader and draw order. Rectangular mipmap behavior is flagged for verification.
- `platforms.json` is an editable starting profile shared by the scripts, not a certification. YUV and bump-map formats exist in the PVR API but are not implemented by these PNG helpers.

## Geometry and rendering

- PVR texture formats describe one texture per polygon pass. A material that combines multiple images needs a supported extra pass, layered geometry, or a baked texture; inspect the exporter's behavior.
- CPU work, visible geometry, texture memory, translucent screen coverage, and draw calls interact. There is no universal triangle limit or safe percentage of translucent triangles. Set project-specific budgets and measure in representative scenes on the console.
- One joint per vertex is a reported common practice, **not a Dreamcast hardware limit**. Multi-bone skinning can be implemented in software if the engine supports it; weigh its cost on the SH-4 and set an explicit limit only when the exporter or project requires one. See the [source notes](sources.md#skinning-and-geometry).
- Vertex colors, baked lighting, texture reuse, and simple geometry-based effects are useful style and performance techniques, not automatic proof that an asset will run at a given frame rate.

### Era contrast

PS2 and GameCube full-frame recipes do not transfer directly to Dreamcast: resizing and re-blending the frame for bloom, depth of field, accumulation blur or full-screen grading needs render-to-texture storage taken from the texture pool, followed by full-screen translucent quads with substantial translucent fill cost. These are not default Dreamcast recipes. Additive glow sprites or halo quads, and modifier-volume shadows or light volumes, are authentic alternatives when supported by the renderer; profile them. This distinction is informed by gsimone's [frame-processing post](https://x.com/ggsimm/status/2117347384070164890) and [fill discussion](https://x.com/ggsimm/status/2117342373747298342), not measured performance figures for this project.

## Project profile

Keep this information with the project. Do not add private project details to the shared skill package.

```text
Project:
Toolchain lock path and verification result:
KOS version / compiler / engine:
Target video mode and frame-rate goal:
Asset directory and source ownership:
Model exporter, output format, and runtime loader:
Texture converter, exact options, palette format, and loader:
Units, axes, collision, and animation conventions:
RAM / VRAM budgets and where they were measured:
Build command and expected output:
Emulator launch method:
Physical hardware loader, capture, and test procedure:
Known limitations and verification status:
```

Copy [toolchain.lock.json](toolchain.lock.json) into the project and replace its placeholder paths. `files` maps paths relative to the lock to SHA-256 values; include SDK/build identity files, compiler, converters, exporter, inputs and generated assets as appropriate. `versions` and `commits` hold supplied assertions; `generated_assets` records input/output relationships and exact options. Run `python3 path/to/dreamcast-dev/scripts/toolchain_lock.py record toolchain.lock.json --version compiler=VERSION --commit KOS=COMMIT`, then `verify toolchain.lock.json` before rebuilding. Verification checks file contents, not the truth of supplied version strings or reproducibility of a build. Missing or changed files fail. Lock-file idea credit: gsimone's typegpu-crt-shaders.
