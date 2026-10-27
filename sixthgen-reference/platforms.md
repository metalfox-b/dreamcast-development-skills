# Platform profiles

One profile per console, then project profiles. The numbers the scripts use live in [platforms.json](platforms.json); this file holds the reasons, sources and the parts no script checks. Each platform's **platform tax** is the one expensive thing you design around.

Source tags: **Stated** = a creator or the docs said it. **Inference** = we chose it. Sources are listed in [techniques.md](techniques.md).

## Targets

Every budget sets `target`:
- **hardware**: real-console homebrew. The VRAM tally, palette RAM and per-polygon texture limits are build failures, and the asset is not done until it runs on the console (step 11 of `sixthgen-asset`).
- **style**: a PC build, port or emulator-only target. The same limits are style rules that make the asset read as sixth-gen; overruns are warnings, and the 480p **preview** stands in for the console.

## Dreamcast (`dc`) — the default

The research's pick for an N64-trained artist: far fewer limits than PS1 or N64, a simple architecture, still a distinct look.

- **Hardware**: SH-4 at 200 MHz doing T&L on the CPU, 16 MB RAM, **8 MB VRAM**, PowerVR2 (tile-based, hidden-surface removal, per-pixel translucency sorting).
- **Platform tax**: VRAM, then translucency. The texture budget defaults to 6 MB of the 8 (inference: framebuffers plus KOS's PVR buffers); read `pvr_mem_available()` on the device and pass it as `--budget-bytes`. Elias Daler ran out of VRAM first; the PVR also struggles with heavy translucent overdraw. It **cannot blend two textures on one polygon**: layer a second polygon or bake one texture.
- **Texture formats** (KallistiOS / dreamcast.wiki):
  | Tag | Use |
  |---|---|
  | `vq565` / `vq1555` / `vq4444` | Default for big, noisy surfaces (walls, ground, skies). Hardware-decoded, free to draw, ~7–8:1 from 256² up. Overhead is a 2 KB codebook, so not below ~64² |
  | `pal8` / `pal4` | Crisp flat-color art, faces, signage. **Palette RAM is global**: 1024 entries for every texture (PAL8 = 256-entry bank, PAL4 = 16). Share palettes with `--palette-from` |
  | `argb4444` / `argb1555` | Cutouts (1555 = hard edge, 4444 = soft) |
  | `rgb565` | Everything else that VQ smears |
  - YUV422 and BUMP exist; no recipe uses them yet.
  - Palette entry format is global too (`pvr_set_pal_format`). The scripts assume ARGB1555; pass `--pal-format` if the project uses another. VERIFY per project.
- **Sizes**: power of two (twiddled), 8 to 1024, 512 recommended max; 128²–256² for most surfaces. Strided textures may have a non-power-of-two width (a multiple of 32; height still power of two; 16-bit direct only; no mips), and the stride is one global register (TEXT_CONTROL), so every strided texture drawn at once shares one width. Mipmapped textures must be square (VERIFY). Mipmaps add about a third.
- **Budget**: hero ~1,000–2,000 tris (Elias considers his cat's 2,760 triangles too high for a Dreamcast game; Sonic Adventure's Sonic is ~1k), NPCs under 2k polys (Elias; possibly faces, so read it as triangles to be safe). Scenes: Shenmue measured ≤ ~14k on-screen verts (no frame rate stated); Soul Blaze peaks at ~24k (likely verts, set against Shenmue's figure) with ~25k visible tris (Rogério) at a locked 30 fps. Our recommendation (inference): ~10–15k visible verts for 60 fps.
- **Vertex colors** cost 4 bytes per vertex per channel: near-free for one layer, ~60 KB per channel at 25k visible tris. Keep 1–2 channels.
- **Skinning**: one joint per vertex in most DC games.
- **Triangle strips** gave Elias a 1.5–2× speed-up; weld seams so strips run long.
- **Fog**: the hardware fog table does Silent Hill-style fog in a couple of lines.
- **SDK**: KallistiOS with the raw PVR API (Elias recommends it over the GL 1.5 layer, GLdc); PVR DR for direct render. dreamSDK on Windows. SH4ZAM for SH-4 math. Textures convert with KOS's `pvrtex`.
- **Export route**: no public Blender exporter. Elias's is private; the Soul Blaze team's Spiral Engine (Blender as editor) is unreleased. Plan on a custom exporter, the largest single cost (Elias: half or more of development time). VERIFY when Spiral ships.
- **Emulators**: Flycast, Deecy (profiling, 4× capture), Redream. Flycast hid misaligned structs that crashed real hardware.
- **Hardware test**: Broadband Adapter (a must for Ninja Dynamics; Elias says you probably need one), CD-R/GD-ROM boot, capture through a scaler (Elias uses a RetroTINK 4K Pro). On-console Dear ImGui driven by DC mouse and keyboard works for debug panels.
- **Load times** to plan for: Soul Blaze takes ~10 s to the menu and ~80 s into the game from GD-ROM.

## PlayStation 2 (`ps2`)

- **Hardware**: Emotion Engine ~295 MHz with VU0/VU1, 32 MB RAM, **4 MB GS eDRAM** for framebuffers and textures, Graphics Synthesizer with very high fill rate and cheap alpha.
- **Platform tax**: VRAM ("texture-fu", per Ninja Dynamics) and microcode: 60 fps needs nearly all 3D in VU1 microcode. Translucency is cheap.
- **Texture rules** (PS2Docs ch. 10–12, PS2Tek):
  | Tag | Use |
  |---|---|
  | `psmt8` | The workhorse: 8-bit with a per-texture 256-entry CLUT |
  | `psmt4` | Small flat art, 16-entry CLUT |
  | `psmct16` | Direct color when a palette bands |
  | `psmct32` / `psmct24` | Only where nothing else works |
  - No hardware compression. Reduce to 8 bpp and dither: Ninja Dynamics' rule is to author for the limit, never posterize a high-res texture with a shader.
  - CLUT alpha: opaque is **0x80** (GS alpha runs 0–128). The converter maps PNG alpha 255 to 0x80. CLUTs and textures sit on 256-byte block boundaries in GS memory, 16-byte aligned in EE RAM for DMA.
  - **CSM1 CLUT swizzle**: a 256-entry PSMT8 CLUT stored in CSM1 layout has its entries reordered (swap index bits 3 and 4: entries 8–15 trade places with 16–23 in every 32). Skip it and colors come out scrambled. The converter does this, not the PNG.
  - **No mirror tile mode**: the GS CLAMP register offers REPEAT, CLAMP, REGION_CLAMP, REGION_REPEAT. Store symmetric art in full. (From the GS register layout, not the research; VERIFY on the first PS2 asset.)
  - Size to the on-screen footprint. A 512² texture is 128 GS pages at 32-bit, 64 at 16-bit, 32 at 8-bit.
  - Textures are double-resident (EE RAM and GS), and the largest free GS slot is what counts, not the total.
- **Budget for textures**: 4 MB minus framebuffers. The default assumes 640×448, 16-bit double buffer and 16-bit Z (~2.36 MB left); 32-bit buffers leave ~0.7 MB. Games stream textures per frame to exceed it. Pass `--budget-bytes` for the project's real layout.
- **Hardware quirks** emulators hide: large UVs wobble on the real GS, trilinear filtering shows stepped bands, a 16-bit framebuffer needs dithering (`preview_480.py --fb16`).
- **Polygon budget**: no practitioner numbers. Start from the Dreamcast budgets and raise once VU1 rendering exists. VERIFY.
- **SDK**: ps2sdk (VU1/VU0 microcode), gsKit, ps2gl. Resource: the PS2Docs handbook (`LESSONS_LEARNED.md`).
- **Export route**: custom; none surveyed. VERIFY.
- **Emulator**: PCSX2 (GS behaviour differs; see PS2Docs). Hardware test: as the project's loader allows; capture through a scaler.

## GameCube (`gc`)

- **Hardware**: Gekko ~486 MHz, hardware T&L on Flipper, 24 MB 1T-SRAM (+16 MB slow ARAM), 2 MB embedded framebuffer/Z and a 1 MB texture cache; textures stream from main RAM.
- **Platform tax**: main-RAM share. Strength: the **TEV** combines up to 8 textures per pass, so two-texture blends the DC can't do are fine here.
- **Texture formats** (libogc, YAGCD): `cmpr` (S3TC/DXT1-style 4 bpp) for color textures, `ci4`/`ci8` for flat art (TLUT in RGB5A3 by default), `i4`/`i8`/`ia4`/`ia8` for grayscale tinted in the TEV, `rgb565`, `rgb5a3` (per texel: opaque RGB555 or ARGB3444), `rgba8`. Data is in 32-byte tiles; repeat, mirror and mips need power of two.
- **Budget for textures**: 8 MB of main RAM is our starting share (inference). Polygon budgets: no practitioner numbers; TebasDev runs a 60 fps voxel engine with display lists, culling and batching. VERIFY.
- **SDK**: libogc / libogc2, devkitPPC, GRRLIB. GCubeSDK (Three.js-style, glTF via cgltf rewritten for big-endian) is a possible glTF route if it ships.
- **Export route**: none confirmed. NewoGame's Newo Shooter brief is a working minimum for a Wii (GameCube-class) engine: one triangulated OBJ with normals, ~300–600 tris, centered within −1…+1, and one PNG of the same name, ≤1024², sides a multiple of 4. VERIFY per project.
- **Emulator**: Dolphin. Lines look softer in Dolphin than on a real Wii. **Hardware test**: Swiss and SD-card loaders (meesedev's reason for picking GameCube), real CRT, design for **overscan** safe areas, long soak tests (NewoGame runs 24-hour ones).

## Original Xbox (`xbox`)

- **Hardware**: Pentium III 733 MHz, 64 MB unified DDR shared with the GPU, NV2A with vertex and pixel shaders and 4 texture stages.
- **Platform tax**: the unified 64 MB, shared with code and audio. Nobody surveyed ships original Xbox art yet, so every art number here is a VERIFY.
- **Texture formats** (xboxdevwiki XPR): `dxt1` (opaque or 1-bit alpha), `dxt3`/`dxt5` (sharp / smooth alpha), `p8` (paletted), `r5g6b5`, `a1r5g5b5`, `a4r4g4b4`, `a8r8g8b8`. Swizzled textures need power of two; linear ones may not be (no mips). Max size unverified; the scripts cap at 1024.
- **Budget for textures**: 24 MB is our starting share (inference).
- **SDK and route**: nxdk (pbkit) with nxdk-gles11 (OpenGL ES 1.1). raylib4Xbox runs raylib on nxdk + SDL2 and builds ISOs for xemu and hardware, which makes Blender → glTF/OBJ → raylib the lowest-friction route (inference). VERIFY.
- **Emulator**: xemu. Hardware test: ISO on a modded console.

## Cross-platform swaps

When one asset ships on several platforms, keep the source art and swap per platform:

| Need | DC | PS2 | GC | Xbox |
|---|---|---|---|---|
| Big noisy surface | `vq565` | `psmt8` + dither | `cmpr` | `dxt1` |
| Flat-color art | `pal4`/`pal8` (global banks) | `psmt4`/`psmt8` | `ci4`/`ci8` | `p8` |
| Hard cutout | `argb1555` | `psmt8` (CLUT alpha 0/0x80) | `rgb5a3` or `cmpr` | `dxt1` |
| Soft alpha | `argb4444` | `psmct32` or CLUT alpha | `rgb5a3` / `ia8` | `dxt5` |
| Two textures blended | layered polygons or a baked texture | multipass | TEV | texture stages |
| Mirror repeat | yes | **no** | yes | yes |

## Project profiles

A project profile says how assets get from Blender into one engine. `sixthgen-asset` reads it at step 1 and step 10. Keep project profiles with the project rather than editing this shared reference.

```
### <project-key>
- Platform(s) and target: dc, hardware
- Engine and SDK: e.g. own engine on KallistiOS (raw PVR API)
- Asset kinds: character | npc | prop | level piece | effect
- Export route: exporter (path or name), output format, where outputs go
- Texture conversion: tool and flags (e.g. pvrtex -f VQ565 ...)
- Scale and axes: game units per Blender unit, up axis
- Run: emulator command and hardware loader (BBA / SD / Swiss / ISO)
- Capture: how a capture is taken (scaler, emulator 4x, screenshot hotkey)
- Repo rules: where art lives, what must not be committed
- Status: VERIFY until one asset has gone through end to end
```
