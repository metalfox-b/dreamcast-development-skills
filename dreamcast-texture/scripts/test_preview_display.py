#!/usr/bin/env python3
"""Check the original preview layout byte for byte and labeled simulations."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from preview_480 import scaled, tiled, display_simulation, vertical_smooth, fb16
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
            for mode, extra, suffix, text in (('svideo', [], '-480i', ' 480i'), ('composite', [], '-480i', ' 480i'),
                                              ('composite', ['--no-interlaced'], '', '')):
                result = subprocess.run(cmd+['--display', mode]+extra, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                path = root/f'source.preview.{mode}{suffix}-sim.png'
                self.assertTrue(path.exists())
                with Image.open(path) as simulation:
                    small = simulation.resize((640, 480), Image.Resampling.NEAREST)
                    # Match the actual burned label against independently drawn text.
                    label = Image.new('RGB', (232, 18), 'black')
                    ImageDraw.Draw(label).text((4, 4), 'DISPLAY SIMULATION: '+mode+text, fill='white')
                    self.assertEqual(small.crop((4, 4, 236, 22)).tobytes(), label.tobytes())
                self.assertEqual(default.read_bytes(), baseline.read_bytes())
                self.assertNotIn(path, collect([root]))
            result = subprocess.run(cmd+['--display', 'composite', '--out', str(root/'custom.png')], capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertTrue((root/'custom.composite-480i-sim.png').exists())
            # Default-on smoothing really differs from the progressive simulation.
            with Image.open(root/'source.preview.composite-480i-sim.png') as a, Image.open(root/'source.preview.composite-sim.png') as b:
                self.assertNotEqual(a.tobytes(), b.tobytes())

    def test_bandwidth_and_mask_are_real_changes(self):
        frame = Image.new('RGB', (64, 32))
        frame.putdata([((255, 0, 0) if x % 2 else (0, 0, 255)) for y in range(32) for x in range(64)])
        svideo = display_simulation(frame, 'svideo')
        composite = display_simulation(frame, 'composite')
        self.assertNotEqual(svideo.crop((0, 24, 64, 32)).tobytes(), frame.crop((0, 24, 64, 32)).tobytes())
        self.assertNotEqual(composite.tobytes(), svideo.tobytes())
        masked = display_simulation(frame, 'composite', True)
        self.assertNotEqual(masked.crop((0, 24, 64, 32)).tobytes(), composite.crop((0, 24, 64, 32)).tobytes())


class InterlaceAndBanding(unittest.TestCase):
    def test_vertical_smooth_mixes_neighbour_lines_121(self):
        frame = Image.new('RGB', (2, 4))
        rows = [0, 200, 40, 120]
        frame.putdata([(v, v, v) for v in rows for _ in range(2)])
        out = vertical_smooth(frame)
        # Edge-clamped (above + 2*centre + below) / 4, rounded: worked by hand.
        expected = [(0+0+200+2)//4, (0+400+40+2)//4, (200+80+120+2)//4, (40+240+120+2)//4]
        self.assertEqual([out.getpixel((0, y))[0] for y in range(4)], expected)
        self.assertEqual([out.getpixel((1, y)) for y in range(4)], [(v, v, v) for v in expected])

    def test_interlaced_simulation_differs_and_is_labelled(self):
        frame = Image.new('RGB', (240, 32))
        frame.putdata([((255, 255, 255) if y % 2 else (0, 0, 0)) for y in range(32) for x in range(240)])
        progressive = display_simulation(frame, 'composite')
        interlaced = display_simulation(frame, 'composite', interlaced=True)
        # One-line stripes flatten under the flicker filter, so neighbouring rows converge.
        below_label = (0, 24, 240, 32)
        p = progressive.crop(below_label).convert('L')
        i = interlaced.crop(below_label).convert('L')
        spread = lambda img: abs(img.getpixel((120, 4)) - img.getpixel((120, 5)))
        self.assertGreater(spread(p), 150)
        self.assertLess(spread(i), 40)
        label = Image.new('RGB', (232, 18), 'black')
        ImageDraw.Draw(label).text((4, 4), 'DISPLAY SIMULATION: composite 480i', fill='white')
        self.assertEqual(interlaced.crop((4, 4, 236, 22)).tobytes(), label.tobytes())

    def test_no_dither_is_plain_rgb565_snap(self):
        frame = Image.new('RGB', (8, 8))
        frame.putdata([(x*9+y, 100+x*3, 255-y*7) for y in range(8) for x in range(8)])
        banded = fb16(frame.copy(), dither=False)
        def snap(v, bits):  # reference: nearest of the 2**bits evenly spaced levels
            top = 2**bits - 1
            return round(round(v*top/255)*255/top)
        self.assertEqual(list(banded.getdata()), [(snap(r, 5), snap(g, 6), snap(b, 5)) for r, g, b in frame.getdata()])
        self.assertNotEqual(banded.tobytes(), fb16(frame.copy()).tobytes())

    def test_cli_flag_rules_and_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/'s.png'
            Image.new('RGBA', (16, 16), (200, 80, 40, 255)).save(source)
            cmd = [sys.executable, str(Path(__file__).with_name('preview_480.py')), str(source)]
            for flag in ('--interlaced', '--no-interlaced'):
                bad = subprocess.run(cmd+['--display', 'vga', flag], capture_output=True, text=True)
                self.assertNotEqual(bad.returncode, 0)
                self.assertIn('VGA', bad.stderr)
            self.assertNotEqual(subprocess.run(cmd+['--no-dither'], capture_output=True).returncode, 0)
            ok = subprocess.run(cmd+['--display', 'svideo', '--interlaced', '--fb16', '--no-dither'], capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertTrue((root/'s.preview.svideo-480i-sim.png').exists())
            self.assertIn('without dither', ok.stdout)


if __name__ == '__main__':
    unittest.main()
