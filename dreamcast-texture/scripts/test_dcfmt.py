#!/usr/bin/env python3
"""Tests for Dreamcast format math without Pillow or Blender."""
import unittest

import dcfmt
from dcfmt import get_format, texture_bytes


class Storage(unittest.TestCase):
    def test_vq_estimate(self):
        fmt = get_format("dc", "vq565")
        self.assertEqual(texture_bytes("dc", fmt, 64, 64), 3072)
        self.assertAlmostEqual(texture_bytes("dc", fmt, 1024, 1024, mips=True) / 1024, 344, delta=2)
        self.assertAlmostEqual(texture_bytes("dc", fmt, 256, 256, mips=True) / 1024, 23, delta=1)

    def test_direct_and_palette_sizes(self):
        self.assertEqual(texture_bytes("dc", get_format("dc", "rgb565"), 64, 64), 8192)
        self.assertEqual(texture_bytes("dc", get_format("dc", "pal8"), 128, 128), 16384)
        self.assertEqual(texture_bytes("dc", get_format("dc", "pal4"), 128, 128), 8192)

    def test_palette_ram_is_separate(self):
        self.assertEqual(dcfmt.dc_palette_entries(4, 0), 1024)
        self.assertEqual(dcfmt.dc_palette_entries(3, 17), 1040)

    def test_small_mip_levels_are_counted(self):
        self.assertGreater(texture_bytes("dc", get_format("dc", "pal4"), 8, 8, mips=True), 32)


class Snapping(unittest.TestCase):
    def test_snap_is_idempotent(self):
        for bits in (3, 4, 5, 6):
            for value in range(256):
                self.assertEqual(dcfmt.snap(dcfmt.snap(value, bits), bits), dcfmt.snap(value, bits))

    def test_bit_replication_counts_as_representable(self):
        for value in range(32):
            self.assertTrue(dcfmt.representable((value << 3) | (value >> 2), 5))

    def test_dreamcast_aliases_and_format_tags(self):
        self.assertEqual(dcfmt.platform_key("Dreamcast"), "dc")
        self.assertEqual(dcfmt.format_from_name("a.rgb565.png", "dc").kind, "direct")
        self.assertIsNone(dcfmt.format_from_name("a.unknown.png", "dc"))
        with self.assertRaises(SystemExit):
            dcfmt.platform_key("other")


if __name__ == "__main__":
    unittest.main()
