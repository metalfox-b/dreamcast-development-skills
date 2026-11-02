#!/usr/bin/env python3
"""Installed skills carry exact license notices and refuse existing destinations."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import install

ROOT = Path(__file__).resolve().parent


class Installer(unittest.TestCase):
    def test_license_copy_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'skills'
            command = [sys.executable, str(ROOT/'install.py'), '--target', str(target)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in install.LICENSE_FILES:
                self.assertEqual((target/'dreamcast-reference'/name).read_bytes(), (ROOT/name).read_bytes())
            sentinel = target/'dreamcast-reference'/'NOTICE'
            sentinel.write_text('preserve me')
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(), 'preserve me')
            self.assertIn('nothing installed', result.stderr)

    def test_preflight_does_not_partially_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target/'dreamcast-texture').mkdir()
            result = subprocess.run([sys.executable, str(ROOT/'install.py'), '--target', str(target)],
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((target/'dreamcast-dev').exists())


if __name__ == '__main__':
    unittest.main()
