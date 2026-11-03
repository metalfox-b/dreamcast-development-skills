# Dreamcast sources and attribution

These links point to external material; its authors retain their rights. The social-post links were matched to claims in the research notes, but their text could not be independently reopened during this preparation. Posts may require sign-in or become unavailable. Treat practitioner figures as examples, not console-wide limits.

## Official KallistiOS documentation

- [KallistiOS project and examples](https://github.com/KallistiOS/KallistiOS): native Dreamcast SDK, build setup, examples for the PVR, input, audio, and other devices.
- [PVR texture formats](https://kos-docs.dreamcast.wiki/group__pvr__txr__fmts.html): RGB565, ARGB, paletted, VQ, twiddled, and stride flags.
- [PVR VRAM allocator](https://kos-docs.dreamcast.wiki/group__pvr__mem__mgmt.html): `pvr_mem_available`, allocation, and alignment.
- [PVR profiling](https://kos-docs.dreamcast.wiki/group__pvr__stats.html): render statistics and VBlank counts.
- [PVR fog](https://kos-docs.dreamcast.wiki/group__pvr__fog.html): fog-table and vertex-fog APIs.
- [PVR init and video-mode source](https://github.com/KallistiOS/KallistiOS/blob/master/kernel/arch/dreamcast/hardware/pvr/pvr_init_shutdown.c) and [video.h](https://github.com/KallistiOS/KallistiOS/blob/master/kernel/arch/dreamcast/include/dc/video.h): vertical smoothing for interlaced non-VGA modes, `PVR_Y_COEFF`, FSAA, and `vid_set_dithering`. Checked at commit d81aa3f.
- [pvrtex source and usage](https://github.com/KallistiOS/KallistiOS/tree/master/utils/pvrtex): conversion, format, VQ, mipmap, and palette options. The [KOS release notes](https://github.com/KallistiOS/KallistiOS/releases) identify it as a host-side Dreamcast texture utility.

## Skinning and geometry

- [Elias Daler on common one-joint Dreamcast skinning](https://x.com/EliasDaler/status/2095084576766898563): a reported convention, not a hardware constraint.
- [Elias Daler's character geometry example](https://x.com/EliasDaler/status/2086799733230612546) and [NPC target](https://x.com/EliasDaler/status/2098013066847715725): individual project budgets, not limits applicable to every game.
- [Elias Daler's triangle-strip example](https://x.com/EliasDaler/status/2094466274545778825): a reported speedup in one engine; profile the target project.
- [Rogério Perdiz on vertex data and visible geometry](https://x.com/rogerioperdiz/status/2094552591736930326): context for duplicated vertices and memory costs.

## Lighting, memory, and effects

- [Elias Daler on vertex lighting](https://x.com/EliasDaler/status/2099290154670203165) and [texture-memory inspection](https://x.com/EliasDaler/status/2098897439851782533).
- [Mirror geometry](https://x.com/EliasDaler/status/2102774838188220526), [halo geometry](https://x.com/EliasDaler/status/2108889722668069012), [Gouraud bloom](https://x.com/EliasDaler/status/2084814994739167645), [fog](https://x.com/EliasDaler/status/2107289196821942690), and [vertex-color paintings](https://x.com/EliasDaler/status/2104550107777740868).
- [Rogério Perdiz on lens-flare geometry](https://x.com/rogerioperdiz/status/2093738691063656702).

## Autotiling

See [autotiling](autotiling.md) for the Dreamcast tile-layer notes and `autotile.py`.

- [asynkimo on Wang tiles for tiled ground](https://x.com/asynkimo/status/2117697739157041432).
- [Boris the Brave, Classification of Tilesets](https://www.boristhebrave.com/2021/11/14/classification-of-tilesets/) and his [archive of the cr31 blob page](https://www.boristhebrave.com/permanent/24/06/cr31/stagecast/wang/blob.html), the source of the published 47-mask list used in the tests. The original cr31.co.uk pages no longer load.
- [Oskar Stålberg, Beyond Townscapers](https://www.youtube.com/watch?v=Uxeo9c-PX-w) and [jess::codes, dual-grid tiles](https://www.youtube.com/watch?v=jEWFSv3ivTg).

## Display chain and full-frame references

These were listed in gsimone's [sources gist](https://gist.github.com/gsimone/76bdcd34fd642349e24ef77cfb85bb62) for the [sixth-gen frame thread](https://x.com/ggsimm/status/2117695690373517750). They inform era contrast and the display simulations; no code was taken.

- [Charles Poynton, *A Technical Introduction to Digital Video*](https://poynton.ca/books/tidv/Poynton-1996-TechIntrDigiVide.pdf) (1996): luma and chroma bandwidth, composite artifacts.
- [FCC rules, 47 CFR 73.682](https://www.govinfo.gov/content/pkg/CFR-2014-title47-vol4/pdf/CFR-2014-title47-vol4-sec73-682.pdf): NTSC I and Q chroma bandwidths of about 1.3 and 0.5 MHz, narrower than luma.
- [Nintendo patent US 6,999,100](https://patents.google.com/patent/US6999100B1/en): GameCube copy-out with a vertical deflicker filter. GameCube only; Dreamcast uses its own PVR scaler.
- [Lengyel and others, "Real-Time Fur over Arbitrary Surfaces"](https://hhoppe.com/proj/fur/) (I3D 2001): shell fur.
- [Kenny Mitchell, "Volumetric Light Scattering as a Post-Process"](https://developer.nvidia.com/gpugems/GPUGems3/gpugems3_ch13.html), GPU Gems 3, chapter 13: the full-frame god-ray method that the Dreamcast sun-shaft recipe avoids.
- [Chris Oat, Real-Time 3D Scene Post-processing](https://www.chrisoat.com/papers/Oat-ScenePostprocessing.pdf) (GDC Europe 2003) and [Joe Demers, Depth of Field: A Survey of Techniques](https://developer.nvidia.com/gpugems/GPUGems/gpugems_ch23.html) (GPU Gems): the full-frame bloom and depth blur excluded by era contrast.
- [Cathode-Retro](https://github.com/DeadlyRedCube/Cathode-Retro) (Boost Software License 1.0): a reference only; no code used.

The 6 MiB default texture budget, suggested asset sizes, and other working budgets are project planning estimates. The source material does not establish a universal safe triangle count, universal translucency percentage, or automatic hardware certification.

## Credits

[gsimone (Gianmarco Simone)](https://github.com/gsimone), also [ggsimm](https://x.com/ggsimm), inspired the following original additions:

- Tight alpha-card hulls: [diet-sprite](https://github.com/gsimone/diet-sprite).
- Zero-tolerance image comparisons and toolchain locks: [typegpu-crt-shaders](https://github.com/gsimone/typegpu-crt-shaders), method and lock-file ideas only.
- Capture contact sheets and transition review: [contact-sheet skill](https://github.com/gsimone/skills/tree/main/skills/contact-sheet), idea only.
- Display-chain previews: [CRT post](https://x.com/ggsimm/status/2113938086807715841) and [frame-processing post](https://x.com/ggsimm/status/2117347384070164890).
- Dreamcast scene mood presets: [mood-accurate post](https://x.com/ggsimm/status/2117302468035928324).
- Display-chain facts, sun shafts, shell fur, banding previews and effect-by-effect capture review: [sixth-gen frame thread](https://x.com/ggsimm/status/2117695690373517750).
- Autotiling: [asynkimo](https://x.com/asynkimo/status/2117697739157041432), Boris the Brave and the cr31 blob page, Oskar Stålberg and jess::codes, idea only.
- Era contrast: [frame processing](https://x.com/ggsimm/status/2117347384070164890) and [fill discussion](https://x.com/ggsimm/status/2117342373747298342).

No code or text from gsimone's repositories was copied.

Timothy Lottes's public-domain CRT Lottes supplied the optional aperture-grille mask idea, implemented in Python. Hyllian's CRT Hyllian (MIT) was reviewed as a reference; no Hyllian code or math is used. See [third-party notes](../THIRD_PARTY.md). [Project Nayuki](https://www.nayuki.io/page/convex-hull-algorithm) receives idea credit as an Andrew monotone-chain algorithm reference; no code was used.
