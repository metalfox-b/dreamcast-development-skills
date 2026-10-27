#!/usr/bin/env python3
"""Tests for model_rules.py without Blender. Run: python3 test_rules.py"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from model_rules import run_checks

PLATFORMS = json.loads((Path(__file__).resolve().parents[2] / "sixthgen-reference" / "platforms.json").read_text())

GOOD = {
    "objects": [{
        "name": "Body", "transform_applied": True, "tris": 1200, "verts": 640, "export_verts": 820, "degenerate": 0,
        "uv_layers": 1, "color_layers": [{"name": "Col", "domain": "CORNER", "flat": False}],
        "materials": [{"name": "skin", "translucent": False,
                       "images": [{"name": "npc_face.pal8.png", "size": [64, 128], "input": "Base Color"}]}],
        "translucent_tris": 0, "armature": "Rig", "max_influences": 1, "multi_bone_vertices": 0,
        "unweighted_vertices": 0,
    }],
    "bones": 16,
}
BUDGET = {"asset": "npc", "platform": "dc", "target": "hardware", "tris": 1500, "verts": 2000, "bones": 18,
          "materials": 3, "textures": [{"name": "npc_face", "size": "64x128", "format": "pal8"}]}


def codes(report, kind):
    return {f["code"] for f in report[kind]}


class Rules(unittest.TestCase):
    def check(self, model=GOOD, budget=BUDGET, plat="dc"):
        return run_checks(model, budget, PLATFORMS[plat])

    def mutate(self, **changes):
        m = copy.deepcopy(GOOD)
        m["objects"][0].update(changes)
        return m

    def test_good_model_passes(self):
        r = self.check()
        self.assertEqual(r["build"], [])
        self.assertEqual(r["style"], [])

    def test_two_textures_fail_on_dc_but_not_gc(self):
        mats = [{"name": "ground", "translucent": False, "images": [
            {"name": "npc_face.pal8.png", "size": [64, 128], "input": "Base Color"},
            {"name": "npc_face.pal8.png", "size": [64, 128], "input": "Base Color"}]}]
        m = self.mutate(materials=mats)
        self.assertIn("multi-texture", codes(self.check(m), "build"))
        self.assertNotIn("multi-texture", codes(self.check(m, plat="gc"), "build"))
        self.assertIn("multipass", codes(self.check(m, plat="ps2"), "style"))

    def test_skinning_is_one_bone_per_vertex(self):
        r = self.check(self.mutate(max_influences=2, multi_bone_vertices=40))
        self.assertIn("multi-bone-vertices", codes(r, "build"))
        r = self.check(self.mutate(max_influences=2, multi_bone_vertices=40), dict(BUDGET, bone_influences=2))
        self.assertNotIn("multi-bone-vertices", codes(r, "build"))

    def test_vertex_color_rules(self):
        self.assertIn("no-vertex-colors", codes(self.check(self.mutate(color_layers=[])), "style"))
        flat = [{"name": "Col", "domain": "CORNER", "flat": True}]
        self.assertIn("flat-vertex-colors", codes(self.check(self.mutate(color_layers=flat)), "style"))
        three = [{"name": f"C{i}", "domain": "CORNER", "flat": False} for i in range(3)]
        self.assertIn("color-channels", codes(self.check(self.mutate(color_layers=three)), "style"))

    def test_split_heavy_and_budgets(self):
        r = self.check(self.mutate(export_verts=1400, tris=1600))
        self.assertIn("split-heavy", codes(r, "style"))
        self.assertIn("over-tri-budget", codes(r, "style"))

    def test_modern_material(self):
        mats = [{"name": "pbr", "translucent": False, "images": [
            {"name": "npc_face.pal8.png", "size": [64, 128], "input": "Base Color"},
            {"name": "npc_face.pal8.png", "size": [64, 128], "input": "Normal"}]}]
        r = self.check(self.mutate(materials=mats))
        self.assertIn("modern-material", codes(r, "style"))
        self.assertNotIn("multi-texture", codes(r, "build"))

    def test_textures_against_budget(self):
        mats = [{"name": "m", "translucent": False, "images": [
            {"name": "other.pal8.png", "size": [64, 64], "input": "Base Color"}]}]
        self.assertIn("texture-not-in-budget", codes(self.check(self.mutate(materials=mats)), "build"))
        mats[0]["images"][0] = {"name": "npc_face.pal8.png", "size": [60, 128], "input": "Base Color"}
        r = self.check(self.mutate(materials=mats))
        self.assertTrue({"texture-size", "texture-npot"} <= codes(r, "build"))

    def test_translucency_is_rationed_on_dc_only(self):
        m = self.mutate(translucent_tris=600)
        self.assertIn("translucent-share", codes(self.check(m), "style"))
        self.assertNotIn("translucent-share", codes(self.check(m, plat="ps2"), "style"))

    def test_transform_and_degenerate(self):
        r = self.check(self.mutate(transform_applied=False, degenerate=3))
        self.assertTrue({"transform-not-applied", "degenerate"} <= codes(r, "build"))


if __name__ == "__main__":
    unittest.main()
