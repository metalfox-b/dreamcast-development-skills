#!/usr/bin/env python3
"""Lossless synthetic capture detects repeats, tiny changes and a planted flash."""
import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg or ffprobe not available')
class CaptureSheet(unittest.TestCase):
    def test_planted_flash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frames = [Image.new('RGB', (64, 64), 'black') for _ in range(7)]
            frames[2] = Image.new('RGB', (64, 64), 'white')
            for frame in frames[5:]:
                frame.putpixel((10, 10), (255, 0, 0))
            video = root/'capture.mkv'
            result = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                                     '-s', '64x64', '-r', '10', '-i', '-', '-c:v', 'ffv1', str(video)],
                                    input=b''.join(f.tobytes() for f in frames), capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            out = root/'review'
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('capture_contact_sheet.py')),
                                     str(video), '--out', str(out)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with (out/'transitions.csv').open() as source:
                records = list(csv.DictReader(source))
            self.assertEqual(len(records), 7)
            self.assertIn('ONE-FRAME POP', records[2]['flags'])
            self.assertEqual(records[2]['changed_pixels'], '4096')
            self.assertIn('NO CHANGE', records[1]['flags'])
            self.assertIn('TINY CHANGE', records[5]['flags'])
            self.assertNotIn('ONE-FRAME POP', records[5]['flags'])
            self.assertEqual(float(records[2]['time_seconds']), 0.2)
            report = (out/'report.md').read_text()
            self.assertIn('7 frames, 4 states', report)
            with Image.open(out/'contact-sheet.png') as sheet:
                self.assertEqual(sheet.size, (1024, 216))
                self.assertEqual(sheet.getpixel((256+32, 32)), (255, 255, 255))


class MissingDependencies(unittest.TestCase):
    def test_clean_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'review'
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('capture_contact_sheet.py')),
                                     'unused.mkv', '--out', str(out)], env={'PATH': ''},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('SKIP: ffmpeg and ffprobe', result.stdout)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
