# Third-party sources

- Timothy Lottes, CRT Lottes, public domain: `crt/shaders/crt-lottes.slang` in [libretro slang-shaders](https://github.com/libretro/slang-shaders) at commit 0b3ff0b240f82f4cb5e5d0117f8f2080e2764cf7. The optional preview mask follows its aperture-grille idea, implemented here in Python. Lottes explicitly permits use and modification.
- Hyllian, CRT Hyllian (`crt/shaders/hyllian/crt-hyllian-base.slang`, same commit), MIT: reviewed as a reference only. No Hyllian code or math is used in the shipped tools.
- KallistiOS: its PVR init source was read (as facts only) to confirm when vertical smoothing and framebuffer dither are enabled. No KOS code is included; the preview's 1-2-1 vertical mix is original Python.
- Cathode-Retro by DeadlyRedCube (Boost Software License 1.0): listed as a reference only. No code is used.
- gsimone and Project Nayuki receive idea credits in [sources](dreamcast-reference/sources.md#credits). No code or text from gsimone's repositories or Nayuki's implementation is included.

Pillow, optional NumPy, ffmpeg and ffprobe are external dependencies, not bundled here; their own licenses apply.
