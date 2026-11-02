#!/usr/bin/env python3
"""Behavior checks for conservative hull geometry and flipbooks."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from fit_card_hull import cross, fit, pixel_corners


class CardHull(unittest.TestCase):
    def test_circle_coverage_and_savings(self):
        image = Image.new('RGBA', (64, 64))
        ImageDraw.Draw(image).ellipse((20, 20, 43, 43), fill='white')
        for count in (3, 4, 8):
            result = fit(pixel_corners(image, 0), 64, 64, count)
            poly = result['vertices_px']
            self.assertLessEqual(len(poly), count)
            self.assertGreaterEqual(len(poly), 3)
            self.assertLess(result['hull_area'], result['full_quad_area'])
            self.assertGreater(result['saved_fraction'], 0)
            for y in range(64):
                for x in range(64):
                    if image.getpixel((x, y))[3]:
                        for p in ((x, y), (x+1, y), (x+1, y+1), (x, y+1)):
                            for a, b in zip(poly, poly[1:]+poly[:1]):
                                self.assertGreaterEqual(cross(a, b, p), -1e-7)
            self.assertEqual(result['triangles'], [[0, i, i+1] for i in range(1, len(poly)-1)])
            self.assertTrue(all(0 <= v <= 1 for p in result['vertices_uv'] for v in p))

    def test_edge_pixels_are_never_clipped(self):
        image = Image.new('RGBA', (16, 16))
        for p in ((0, 0), (0, 15), (15, 15), (15, 0), (8, 8)):
            image.putpixel(p, (255, 255, 255, 255))
        result = fit(pixel_corners(image, 0), 16, 16, 8)
        self.assertEqual(result['hull_area'], 256)
        self.assertEqual(result['saved_fraction'], 0)
        self.assertEqual(len(result['vertices_px']), 4)
        self.assertEqual(set(map(tuple, result['vertices_uv'])), {(0, 0), (1, 0), (1, 1), (0, 1)})

    def test_empty_and_impossible_triangle(self):
        self.assertEqual(fit([], 8, 8, 3)['triangles'], [])
        image = Image.new('RGBA', (8, 8), 'white')
        with self.assertRaisesRegex(ValueError, 'cannot fit'):
            fit(pixel_corners(image, 0), 8, 8, 3)
        self.assertEqual(pixel_corners(image, 255), [])

    def test_flipbook_shared_and_cli_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = Image.new('RGBA', (32, 16))
            image.putpixel((2, 3), (255, 255, 255, 128))
            image.putpixel((28, 12), (255, 255, 255, 255))
            image.save(root/'frames.png')
            command = [sys.executable, str(Path(__file__).with_name('fit_card_hull.py')),
                       str(root/'frames.png'), '--grid', '2x1', '--out', str(root/'hull.json')]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((root/'hull.json').read_text())
            self.assertEqual(len(data['frames']), 2)
            self.assertEqual(data['frame_size'], [16, 16])
            result = subprocess.run(command+['--shared'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            shared = json.loads((root/'hull.json').read_text())
            poly = shared['frames'][0]['vertices_px']
            self.assertEqual(len(shared['frames']), 1)
            for p in ((2, 3), (3, 4), (12, 12), (13, 13)):
                self.assertTrue(all(cross(a, b, p) >= -1e-7 for a, b in zip(poly, poly[1:]+poly[:1])))
            for flags in (['--grid', '3x1'], ['--vertices', '2'], ['--threshold', '-1']):
                self.assertNotEqual(subprocess.run(command+flags, capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
