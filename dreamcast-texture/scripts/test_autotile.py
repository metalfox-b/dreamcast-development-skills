#!/usr/bin/env python3
"""Behaviour checks for the autotile lookups and sheet planner."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from autotile import autotile, blob_masks, blob_reduce, blob_table, corner_classes, corner_index, edge_index, plan_sheet

SCRIPT = str(Path(__file__).with_name('autotile.py'))
# The 47 blob masks as published on the cr31 Blob page (archived by Boris the Brave).
PUBLISHED_47 = [0, 1, 4, 5, 7, 16, 17, 20, 21, 23, 28, 29, 31, 64, 65, 68, 69, 71, 80, 81, 84, 85, 87, 92, 93, 95,
                112, 113, 116, 117, 119, 124, 125, 127, 193, 197, 199, 209, 213, 215, 221, 223, 241, 245, 247, 253, 255]


class Lookups(unittest.TestCase):
    def test_four_bit_indices(self):
        self.assertEqual(corner_index(True, False, False, False), 1)
        self.assertEqual(corner_index(False, False, True, True), 12)
        self.assertEqual(edge_index(True, False, True, False), 5)
        self.assertEqual(sorted(corner_index(*(bool(i >> b & 1) for b in range(4))) for i in range(16)), list(range(16)))

    def test_blob_reduces_to_the_published_47(self):
        self.assertEqual(blob_masks(), PUBLISHED_47)
        self.assertEqual(blob_reduce(2), 0)          # NE alone has no backing edges
        self.assertEqual(blob_reduce(1 | 2), 1)      # N without E still drops NE
        self.assertEqual(blob_reduce(1 | 2 | 4), 7)  # N, NE and E keep the corner
        table = blob_table()
        self.assertEqual(len(table), 256)
        self.assertEqual(sorted(set(table.values())), list(range(47)))
        self.assertEqual((table[0], table[255], table[2]), (0, 46, 0))

    def test_corner_rotation_classes(self):
        self.assertEqual(corner_classes(), [[0], [1, 2, 4, 8], [3, 5, 10, 12], [6, 9], [7, 11, 13, 14], [15]])


class Grids(unittest.TestCase):
    def test_dual_grid_corner_map(self):
        grid = [[True, False], [False, False]]
        self.assertEqual(autotile(grid, 'corner'), [[8, 4, 0], [2, 1, 0], [0, 0, 0]])

    def test_blob_and_edge_maps(self):
        plus = [[False, True, False], [True, True, True], [False, True, False]]
        idx = {m: i for i, m in enumerate(PUBLISHED_47)}
        # Diagonals next to the plus's arms are dropped because one backing edge is empty.
        self.assertEqual(autotile(plus, 'blob'), [[-1, idx[16], -1], [idx[4], idx[85], idx[64]], [-1, idx[1], -1]])
        self.assertEqual(autotile(plus, 'edge'), [[-1, 4, -1], [2, 15, 8], [-1, 1, -1]])
        self.assertEqual(autotile([[True]], 'blob', outside=True), [[46]])


class Planning(unittest.TestCase):
    def test_power_of_two_sheets(self):
        self.assertEqual(plan_sheet(47, 32), (256, 256, 8))
        self.assertEqual(plan_sheet(16, 16), (64, 64, 4))
        self.assertEqual(plan_sheet(16, 32, gutter=2), (256, 128, 7))
        with self.assertRaises(ValueError):
            plan_sheet(47, 256)

    def test_cli(self):
        out = subprocess.run([sys.executable, SCRIPT, 'plan', '--set', 'blob', '--tile', '32', '--format', 'pal4'],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn('256x256 pal4', out.stdout)
        self.assertIn('32.0 KB', out.stdout)
        table = json.loads(subprocess.run([sys.executable, SCRIPT, 'table', 'blob'], capture_output=True, text=True).stdout)
        self.assertEqual(table['masks'], PUBLISHED_47)
        with tempfile.TemporaryDirectory() as tmp:
            grid = Path(tmp)/'g.txt'
            grid.write_text('#.\n..\n')
            rows = subprocess.run([sys.executable, SCRIPT, 'map', str(grid), '--set', 'corner'],
                                  capture_output=True, text=True).stdout.split('\n')
            self.assertEqual(rows[0].split(), ['8', '4', '0'])
        bad = subprocess.run([sys.executable, SCRIPT, 'plan', '--set', 'blob', '--tile', '300', '--format', 'pal4'],
                             capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)


if __name__ == '__main__':
    unittest.main()
