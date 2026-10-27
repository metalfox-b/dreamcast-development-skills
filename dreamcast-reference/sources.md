# Dreamcast sources and attribution

These links point to external material; its authors retain their rights. The social-post links were matched to claims in the research notes, but their text could not be independently reopened during this preparation. Posts may require sign-in or become unavailable. Treat practitioner figures as examples, not console-wide limits.

## Official KallistiOS documentation

- [KallistiOS project and examples](https://github.com/KallistiOS/KallistiOS): native Dreamcast SDK, build setup, examples for the PVR, input, audio, and other devices.
- [PVR texture formats](https://kos-docs.dreamcast.wiki/group__pvr__txr__fmts.html): RGB565, ARGB, paletted, VQ, twiddled, and stride flags.
- [PVR VRAM allocator](https://kos-docs.dreamcast.wiki/group__pvr__mem__mgmt.html): `pvr_mem_available`, allocation, and alignment.
- [PVR profiling](https://kos-docs.dreamcast.wiki/group__pvr__stats.html): render statistics and VBlank counts.
- [PVR fog](https://kos-docs.dreamcast.wiki/group__pvr__fog.html): fog-table and vertex-fog APIs.
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

The 6 MiB default texture budget, suggested asset sizes, and other working budgets are project planning estimates. The source material does not establish a universal safe triangle count, universal translucency percentage, or automatic hardware certification.
