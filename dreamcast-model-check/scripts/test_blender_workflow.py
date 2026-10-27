#!/usr/bin/env python3
"""Exercise the checker and bake on a generated Blender model when Blender is available."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BLENDER = os.environ.get("BLENDER") or shutil.which("blender")


@unittest.skipUnless(BLENDER, "Blender not available; set BLENDER to run integration checks")
class BlenderWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="dreamcast-model-test-")
        cls.root = Path(cls.tmp.name)
        cls.blend = cls.root / "rigged.blend"
        create = cls.root / "create.py"
        create.write_text("""
import bpy
import sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add()
mesh = bpy.context.object
armdata = bpy.data.armatures.new('RigData')
arm = bpy.data.objects.new('Rig', armdata)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
mesh.select_set(False)
bpy.ops.object.mode_set(mode='EDIT')
for i, name in enumerate(('BoneA', 'BoneB')):
    bone = armdata.edit_bones.new(name)
    bone.head = (i, 0, 0)
    bone.tail = (i, 0, 1)
bpy.ops.object.mode_set(mode='OBJECT')
mesh.vertex_groups.new(name='BoneA').add(list(range(8)), 1.0, 'REPLACE')
mesh.vertex_groups.new(name='BoneB').add([0, 1], 0.5, 'REPLACE')
mesh.parent = arm
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
""")
        result = subprocess.run([BLENDER, "-b", "--factory-startup", "--python-exit-code", "1",
                                 "--python", str(create), "--", str(cls.blend)], text=True, capture_output=True)
        if result.returncode != 0 or not cls.blend.exists():
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check_model(self, budget):
        budget_file = self.root / "budget.json"
        report_file = self.root / "report.json"
        budget_file.write_text(json.dumps(budget))
        result = subprocess.run([BLENDER, "-b", "--factory-startup", str(self.blend), "--python",
                                 str(SCRIPTS / "check_model.py"), "--", "--budget", str(budget_file),
                                 "--json", str(report_file)], text=True, capture_output=True)
        self.assertTrue(report_file.exists(), result.stdout + result.stderr)
        return result, json.loads(report_file.read_text())

    def test_hardware_triangle_budget_fails_without_strict(self):
        result, report = self.check_model({"platform": "dc", "target": "hardware", "tris": 1, "textures": []})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("over-tri-budget", {f["code"] for f in report["report"]["build"]})

    def test_skinning_follows_project_limit(self):
        budget = {"platform": "dc", "target": "hardware", "tris": 100, "textures": []}
        result, report = self.check_model(budget)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        obj = report["model"]["objects"][0]
        self.assertEqual(obj["influence_histogram"]["2"], 2)
        self.assertIn("multi-bone-guidance", {f["code"] for f in report["report"]["style"]})
        result, report = self.check_model(dict(budget, bone_influences=1))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("multi-bone-vertices", {f["code"] for f in report["report"]["build"]})
        result, _ = self.check_model(dict(budget, bone_influences=2))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_vertex_color_bake(self):
        baked = self.root / "baked.blend"
        result = subprocess.run([BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", str(self.blend),
                                 "--python", str(SCRIPTS / "bake_vertex_colors.py"), "--", "--output", str(baked),
                                 "--samples", "8"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(baked.exists())
        expr = ("import bpy; mesh=next(o.data for o in bpy.context.scene.objects if o.type=='MESH'); "
                "attr=mesh.color_attributes.get('Col_Bake'); assert attr and len(attr.data)>0; print('BAKE_OK')")
        result = subprocess.run([BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", str(baked),
                                 "--python-expr", expr], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("BAKE_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
