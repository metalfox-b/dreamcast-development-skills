#!/usr/bin/env python3
"""Exercise Dreamcast PNG preparation and, when installed, pvrtex conversion."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

SCRIPTS = Path(__file__).resolve().parent
PVRTEX = os.environ.get("PVRTEX") or shutil.which("pvrtex")


class TextureWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dreamcast-texture-test-")
        self.root = Path(self.tmp.name)
        self.src = self.root / "source.png"
        image = Image.new("RGBA", (64, 64))
        image.putdata([((x * 4) % 256, (y * 4) % 256, ((x + y) * 2) % 256, 255)
                       for y in range(64) for x in range(64)])
        image.save(self.src)

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, name, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / name), *(str(a) for a in args)],
                              text=True, capture_output=True)

    def prepare(self, tag):
        path = self.root / f"sample.{tag}.png"
        result = self.run_script("quantize_texture.py", self.src, path, "--size", "64x64")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(path.is_file())
        return path

    def test_quantize_and_validate_hardware_budget(self):
        path = self.prepare("pal8")
        result = self.run_script("validate_textures.py", "--platform", "dc", path, "--budget-bytes", "1", "--json")
        self.assertNotEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertEqual(report["target"], "hardware")
        self.assertTrue(report["set"]["errors"])
        result = self.run_script("validate_textures.py", "--platform", "dc", path, "--budget-bytes", "1",
                                 "--target", "style", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["set"]["warnings"])

    def test_empty_directory_cannot_pass(self):
        empty = self.root / "empty"
        empty.mkdir()
        result = self.run_script("validate_textures.py", "--platform", "dc", empty)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no PNG textures found", result.stderr)

    def test_other_platform_is_rejected(self):
        path = self.prepare("rgb565")
        result = self.run_script("validate_textures.py", "--platform", "other", path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Dreamcast only", result.stdout + result.stderr)

    def test_prepared_vq_png_is_not_encoded_texture(self):
        path = self.prepare("vq565")
        with Image.open(path) as image:
            self.assertEqual(image.size, (64, 64))
        result = self.run_script("validate_textures.py", "--platform", "dc", path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotEqual(path.read_bytes()[:4], b"DcTx")

    @unittest.skipUnless(PVRTEX, "pvrtex not available; set PVRTEX to run native conversion checks")
    def test_pvrtex_conversion_and_decode(self):
        for tag, format_name, flags in (("rgb565", "rgb565", ()), ("vq565", "rgb565", ("-c", "256"))):
            with self.subTest(format=tag):
                path = self.prepare(tag)
                encoded = self.root / f"{tag}.dt"
                preview = self.root / f"{tag}-decoded.png"
                converted = subprocess.run([PVRTEX, "-i", str(path), "-o", str(encoded), "-f", format_name, *flags],
                                           text=True, capture_output=True)
                self.assertEqual(converted.returncode, 0, converted.stdout + converted.stderr)
                self.assertGreater(encoded.stat().st_size, 32)
                decoded = subprocess.run([PVRTEX, "-i", str(encoded), "-p", str(preview)], text=True, capture_output=True)
                self.assertEqual(decoded.returncode, 0, decoded.stdout + decoded.stderr)
                with Image.open(preview) as image:
                    self.assertEqual(image.size, (64, 64))

    @unittest.skipUnless(importlib.util.find_spec("numpy"), "NumPy is required for VQ preview")
    def test_vq_preview_is_generated(self):
        path = self.prepare("vq565")
        preview = self.root / "preview.png"
        result = self.run_script("preview_480.py", path, "--vq", "--out", preview)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with Image.open(preview) as image:
            self.assertEqual(image.size, (1280, 960))

    def test_budget_platform_cannot_be_overridden(self):
        path = self.prepare("rgb565")
        budget = self.root / "budget.json"
        budget.write_text(json.dumps({"platform": "other", "target": "hardware", "textures": []}))
        result = self.run_script("validate_textures.py", "--platform", "dc", "--budget", budget, path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Dreamcast only", result.stdout + result.stderr)

    def test_strided_vq_png_and_mipmap_validation(self):
        path = self.root / "stride.vq565.png"
        result = self.run_script("quantize_texture.py", self.src, path, "--size", "96x64", "--allow-npot")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.run_script("validate_textures.py", "--platform", "dc", path, "--allow-npot")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.run_script("validate_textures.py", "--platform", "dc", path, "--allow-npot", "--mips")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot have mipmaps", result.stdout)
        result = self.run_script("validate_textures.py", "--platform", "dc", "--plan", "7x7", "rgb565")
        self.assertNotEqual(result.returncode, 0)

    @unittest.skipUnless(PVRTEX, "pvrtex not available; set PVRTEX to run native conversion checks")
    def test_pvrtex_compressed_strided_texture(self):
        path = self.root / "stride.vq565.png"
        prepared = self.run_script("quantize_texture.py", self.src, path, "--size", "96x64", "--allow-npot")
        self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
        encoded = self.root / "stride.dt"
        result = subprocess.run([PVRTEX, "-i", str(path), "-o", str(encoded), "-f", "rgb565", "-s", "-c", "256"],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(encoded.is_file())

    @unittest.skipUnless(PVRTEX, "pvrtex not available; set PVRTEX to run native conversion checks")
    def test_pvrtex_paletted_output_has_a_palette(self):
        path = self.prepare("pal8")
        encoded = self.root / "pal8.dt"
        result = subprocess.run([PVRTEX, "-i", str(path), "-o", str(encoded), "-f", "pal8bpp"],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(encoded.is_file())
        palette = Path(str(encoded) + ".pal")
        self.assertTrue(palette.is_file())
        shared = self.root / "shared.dt"
        preview = self.root / "shared-preview.png"
        result = subprocess.run([PVRTEX, "-i", str(path), "-o", str(shared), "-f", "pal8bpp", "-P", str(palette)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = subprocess.run([PVRTEX, "-i", str(shared), "-P", str(palette), "-p", str(preview)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with Image.open(preview) as image:
            self.assertEqual(image.size, (64, 64))


if __name__ == "__main__":
    unittest.main()
