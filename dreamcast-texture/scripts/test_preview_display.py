#!/usr/bin/env python3
"""Check the original preview layout byte for byte and labeled simulations."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from preview_480 import scaled, tiled, display_simulation
from validate_textures import collect


class PreviewDisplay(unittest.TestCase):
    def test_vga_matches_original_and_simulations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/'source.png'
            image = Image.new('RGBA', (32, 32))
            image.putdata([(x*8, y*8, (x+y)*4, 255) for y in range(32) for x in range(32)])
            image.save(source)
            # Frozen pre-change default composition: the existing sampler is unchanged.
            frame = Image.new('RGB', (640, 480), (96, 96, 104))
            texture = tiled(image, ['repeat', 'repeat'], [1, 1])
            x = 32
            for size in (64, 128, 256):
                tile = scaled(texture, (size, size), False)
                frame.paste(tile, (x, (480-size)//2), tile)
                x += size+32
            baseline = root/'baseline.png'
            frame.resize((1280, 960), Image.Resampling.NEAREST).save(baseline)
            cmd = [sys.executable, str(Path(__file__).with_name('preview_480.py')), str(source)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            default = root/'source.preview.png'
            self.assertEqual(default.read_bytes(), baseline.read_bytes())
            explicit = root/'explicit.png'
            self.assertEqual(subprocess.run(cmd+['--display', 'vga', '--out', str(explicit)], capture_output=True).returncode, 0)
            self.assertEqual(explicit.read_bytes(), baseline.read_bytes())
            for mode in ('svideo', 'composite'):
                result = subprocess.run(cmd+['--display', mode], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                path = root/f'source.preview.{mode}-sim.png'
                self.assertTrue(path.exists())
                with Image.open(path) as simulation:
                    small = simulation.resize((640, 480), Image.Resampling.NEAREST)
                    # Match the actual burned label against independently drawn text.
                    label = Image.new('RGB', (232, 18), 'black')
                    ImageDraw.Draw(label).text((4, 4), 'DISPLAY SIMULATION: '+mode, fill='white')
                    self.assertEqual(small.crop((4, 4, 236, 22)).tobytes(), label.tobytes())
                self.assertEqual(default.read_bytes(), baseline.read_bytes())
                self.assertNotIn(path, collect([root]))
            result = subprocess.run(cmd+['--display', 'composite', '--out', str(root/'custom.png')], capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertTrue((root/'custom.composite-sim.png').exists())

    def test_bandwidth_and_mask_are_real_changes(self):
        frame = Image.new('RGB', (64, 32))
        frame.putdata([((255, 0, 0) if x % 2 else (0, 0, 255)) for y in range(32) for x in range(64)])
        svideo = display_simulation(frame, 'svideo')
        composite = display_simulation(frame, 'composite')
        self.assertNotEqual(svideo.crop((0, 24, 64, 32)).tobytes(), frame.crop((0, 24, 64, 32)).tobytes())
        self.assertNotEqual(composite.tobytes(), svideo.tobytes())
        masked = display_simulation(frame, 'composite', True)
        self.assertNotEqual(masked.crop((0, 24, 64, 32)).tobytes(), composite.crop((0, 24, 64, 32)).tobytes())


if __name__ == '__main__':
    unittest.main()
