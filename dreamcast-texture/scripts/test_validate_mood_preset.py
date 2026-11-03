#!/usr/bin/env python3
"""Real example and rejected hardware-incompatible controls."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from validate_mood_preset import validate

EXAMPLE = Path(__file__).resolve().parents[2]/'dreamcast-reference'/'mood-preset.example.json'


class MoodPreset(unittest.TestCase):
    def test_example_and_cli(self):
        data = json.loads(EXAMPLE.read_text())
        self.assertEqual(validate(data)['name'], 'Evening harbor')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'preset.json'
            path.write_text(json.dumps(data))
            cmd = [sys.executable, str(Path(__file__).with_name('validate_mood_preset.py')), str(path)]
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            data['LUT'] = 'forbidden'
            path.write_text(json.dumps(data))
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_reject_controls_colors_banks_and_distances(self):
        base = json.loads(EXAMPLE.read_text())
        for field in ('LUT', 'post_process', 'full_screen_grading', 'unknown'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate(dict(base, **{field: True}))
        for fmt, valid, invalid in [('PAL4', 63, 64), ('PAL8', 3, 4)]:
            data = copy.deepcopy(base)
            data['palette_swap'] = {'format': fmt, 'bank': valid}
            self.assertEqual(validate(data)['palette_swap']['bank'], valid)
            for bank in (invalid, -1, True, 1.5):
                data['palette_swap']['bank'] = bank
                with self.assertRaises(ValueError):
                    validate(data)
        for field, value in [('color', [1.1, 0, 0]), ('density', float('nan')), ('start', 200)]:
            data = copy.deepcopy(base)
            data['fog'][field] = value
            with self.assertRaises(ValueError):
                validate(data)
        data = copy.deepcopy(base)
        data['sky']['LUT'] = 'bad'
        with self.assertRaises(ValueError):
            validate(data)


if __name__ == '__main__':
    unittest.main()
