#!/usr/bin/env python3
"""Tests for sixfmt.py against the numbers the sources state. No Pillow needed.

Run: python3 test_sixfmt.py
"""
from __future__ import annotations

import unittest

import sixfmt
from sixfmt import get_format, texture_bytes


class Storage(unittest.TestCase):
    def test_dc_vq_matches_dreamcast_wiki(self):
        # dreamcast.wiki: a 1024x1024 face is 2 MB as RGB565 and 344 KB as VQ (the figure includes mips)
        self.assertEqual(texture_bytes("dc", get_format("dc", "rgb565"), 1024, 1024), 2 * 1024 * 1024)
        vq = texture_bytes("dc", get_format("dc", "vq565"), 1024, 1024, mips=True)
        self.assertAlmostEqual(vq / 1024, 344, delta=2)
        # dcemulation: a 256x256 VQ texture with mips is about 23 KB
        self.assertAlmostEqual(texture_bytes("dc", get_format("dc", "vq565"), 256, 256, mips=True) / 1024, 23, delta=1)

    def test_dc_palettes_cost_no_vram(self):
        self.assertEqual(texture_bytes("dc", get_format("dc", "pal8"), 128, 128), 128 * 128)
        self.assertEqual(texture_bytes("dc", get_format("dc", "pal4"), 128, 128), 128 * 128 // 2)

    def test_ps2_pages_match_ps2docs(self):
        # PS2Docs: 512x512 takes 128 GS pages at 32-bit, 64 at 16-bit, 32 at 8-bit
        self.assertEqual(sixfmt.ps2_pages(get_format("ps2", "psmct32"), 512, 512), 128)
        self.assertEqual(sixfmt.ps2_pages(get_format("ps2", "psmct16"), 512, 512), 64)
        self.assertEqual(sixfmt.ps2_pages(get_format("ps2", "psmt8"), 512, 512), 32)
        self.assertEqual(texture_bytes("ps2", get_format("ps2", "psmt8"), 512, 512), 32 * 8192 + 1024)

    def test_gc_tiles(self):
        self.assertEqual(texture_bytes("gc", get_format("gc", "cmpr"), 64, 64), 64 * 64 // 2)
        self.assertEqual(texture_bytes("gc", get_format("gc", "rgba8"), 4, 4), 64)
        self.assertEqual(texture_bytes("gc", get_format("gc", "ci8"), 8, 4), 32 + 512)

    def test_xbox_dxt(self):
        self.assertEqual(texture_bytes("xbox", get_format("xbox", "dxt1"), 256, 256), 256 * 256 // 2)
        self.assertEqual(texture_bytes("xbox", get_format("xbox", "dxt5"), 256, 256), 256 * 256)

    def test_dc_palette_ram(self):
        self.assertEqual(sixfmt.dc_palette_entries(4, 0), 1024)
        self.assertEqual(sixfmt.dc_palette_entries(3, 17), 1040)


class Snapping(unittest.TestCase):
    def test_snap_is_idempotent(self):
        for bits in (3, 4, 5, 6):
            for v in range(256):
                self.assertEqual(sixfmt.snap(sixfmt.snap(v, bits), bits), sixfmt.snap(v, bits))

    def test_bit_replication_counts_as_representable(self):
        for q in range(32):
            self.assertTrue(sixfmt.representable((q << 3) | (q >> 2), 5))

    def test_tags_are_per_platform(self):
        self.assertEqual(sixfmt.format_from_name("a.rgb565.png", "dc").kind, "direct")
        self.assertEqual(sixfmt.format_from_name("a.cmpr.png", "gc").kind, "block")
        self.assertIsNone(sixfmt.format_from_name("a.cmpr.png", "dc"))
        self.assertEqual(sixfmt.platform_key("Dreamcast"), "dc")


if __name__ == "__main__":
    unittest.main()
