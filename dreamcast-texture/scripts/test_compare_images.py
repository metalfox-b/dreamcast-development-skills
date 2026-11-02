#!/usr/bin/env python3
"""Exercise exact image errors, evidence and alpha handling."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from compare_images import compare


class ImageComparison(unittest.TestCase):
    def test_counts_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root/'a.png', root/'b.png'
            image = Image.new('RGBA', (2, 2), (10, 20, 30, 255))
            image.save(a)
            record, _ = compare(a, a)
            self.assertTrue(record['exact'])
            self.assertEqual(record['differing_bytes'], 0)
            image.putpixel((1, 1), (13, 20, 25, 200))
            image.save(b)
            out = root/'diff.png'
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('compare_images.py')),
                                     str(a), str(b), '--out', str(out), '--meta', 'capture=console=VGA'],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(out.with_suffix('.json').read_text())
            self.assertFalse(record['exact'])
            self.assertEqual(record['differing_pixels'], 1)
            self.assertEqual(record['differing_rgb_bytes'], 2)
            self.assertEqual(record['mean_error'], 8/12)
            self.assertEqual(record['max_error'], 5)
            self.assertEqual(record['inputs'][0]['sha256'], hashlib.sha256(a.read_bytes()).hexdigest())
            self.assertEqual(record['meta'], {'capture': 'console=VGA'})
            with Image.open(out) as diff:
                self.assertEqual(diff.getpixel((1, 1)), (3, 0, 5))
            alpha, _ = compare(a, b, True)
            self.assertEqual(alpha['differing_bytes'], 3)
            self.assertEqual(alpha['max_error'], 55)
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('compare_images.py')),
                                     str(a), str(b), '--out', str(out), '--include-alpha'],
                                    capture_output=True)
            self.assertEqual(result.returncode, 0)
            with Image.open(root/'diff.alpha.png') as alpha_diff:
                self.assertEqual(alpha_diff.getpixel((1, 1)), 55)
            with Image.open(a) as original:
                image = original.copy()
            image.putpixel((0, 0), (10, 20, 30, 0))
            image.save(b)
            self.assertTrue(compare(a, b)[0]['exact'])
            self.assertFalse(compare(a, b, True)[0]['exact'])
            Image.new('RGB', (1, 1)).save(b)
            with self.assertRaisesRegex(ValueError, 'sizes differ'):
                compare(a, b)
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('compare_images.py')),
                                     str(a), str(b), '--out', str(out)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
