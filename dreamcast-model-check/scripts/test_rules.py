#!/usr/bin/env python3
"""Test Dreamcast model rules without Blender."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from model_rules import format_report, run_checks

PLATFORM = json.loads((Path(__file__).resolve().parents[2] / "dreamcast-reference" / "platforms.json").read_text())["dc"]
GOOD = {
    "objects": [{
        "name": "Body", "transform_applied": True, "tris": 1200, "verts": 640, "export_verts": 820, "degenerate": 0,
        "uv_layers": 1, "color_layers": [{"name": "Col", "domain": "CORNER", "flat": False}],
        "materials": [{"name": "skin", "translucent": False,
                       "images": [{"name": "npc_face.pal8.png", "size": [64, 128], "input": "Base Color"}]}],
        "translucent_tris": 0, "armature": "Rig", "max_influences": 1,
        "multi_bone_vertices": 0, "unweighted_vertices": 0,
    }],
    "bones": 16,
}
BUDGET = {"asset": "npc", "platform": "dc", "target": "hardware", "tris": 1500, "verts": 2000, "bones": 18,
          "materials": 3, "textures": [{"name": "npc_face", "size": "64x128", "format": "pal8"}]}


def codes(report, kind):
    return {finding["code"] for finding in report[kind]}


class Rules(unittest.TestCase):
    def check(self, model=GOOD, budget=BUDGET):
        return run_checks(model, budget, PLATFORM)

    def mutate(self, **changes):
        model = copy.deepcopy(GOOD)
        model["objects"][0].update(changes)
        return model

    def test_good_model_passes(self):
        report = self.check()
        self.assertEqual(report["build"], [])
        self.assertEqual(report["style"], [])

    def test_missing_meshes_fail(self):
        self.assertIn("no-meshes", codes(self.check({"objects": [], "bones": 0}), "build"))

    def test_skinning_is_a_recommendation_without_project_limit(self):
        report = self.check(self.mutate(max_influences=2, multi_bone_vertices=40))
        self.assertNotIn("multi-bone-vertices", codes(report, "build"))
        self.assertIn("multi-bone-guidance", codes(report, "style"))

    def test_explicit_skinning_limit_and_histogram(self):
        model = self.mutate(max_influences=3, multi_bone_vertices=40, influence_histogram={"1": 600, "2": 30, "3": 10})
        report = self.check(model, dict(BUDGET, bone_influences=2))
        finding = next(f for f in report["build"] if f["code"] == "multi-bone-vertices")
        self.assertEqual(finding["count"], 10)
        self.assertNotIn("multi-bone-vertices", codes(self.check(model, dict(BUDGET, bone_influences=3)), "build"))

    def test_explicit_budgets_fail_hardware_but_warn_style(self):
        model = self.mutate(export_verts=2100, tris=1600)
        hardware = self.check(model)
        self.assertTrue({"over-tri-budget", "over-vert-budget"} <= codes(hardware, "build"))
        style = self.check(model, dict(BUDGET, target="style"))
        self.assertTrue({"over-tri-budget", "over-vert-budget"} <= codes(style, "style"))
        self.assertIn("FAIL (style)", format_report(style, strict=True))

    def test_zero_is_an_explicit_budget(self):
        report = self.check(GOOD, dict(BUDGET, tris=0, bones=0, materials=0))
        self.assertTrue({"over-tri-budget", "over-bone-budget", "over-material-budget"} <= codes(report, "build"))

    def test_vertex_color_guidance(self):
        self.assertIn("no-vertex-colors", codes(self.check(self.mutate(color_layers=[])), "style"))
        flat = [{"name": "Col", "domain": "CORNER", "flat": True}]
        self.assertIn("flat-vertex-colors", codes(self.check(self.mutate(color_layers=flat)), "style"))
        three = [{"name": f"C{i}", "domain": "CORNER", "flat": False} for i in range(3)]
        self.assertIn("color-channels", codes(self.check(self.mutate(color_layers=three)), "style"))

    def test_split_heavy_is_a_style_finding(self):
        report = self.check(self.mutate(export_verts=1400))
        self.assertIn("split-heavy", codes(report, "style"))

    def test_multi_texture_is_exporter_guidance(self):
        mats = [{"name": "ground", "translucent": False, "images": [
            {"name": "one.pal8.png", "size": [64, 128], "input": "Base Color"},
            {"name": "two.pal8.png", "size": [64, 128], "input": "Base Color"}]}]
        budget = dict(BUDGET, textures=[{"name": n, "size": "64x128", "format": "pal8"} for n in ("one", "two")])
        report = self.check(self.mutate(materials=mats), budget)
        self.assertIn("multi-texture", codes(report, "style"))
        self.assertNotIn("multi-texture", codes(report, "build"))
        mats[0]["images"][1]["name"] = "one.pal8.png"
        self.assertNotIn("multi-texture", codes(self.check(self.mutate(materials=mats), budget), "style"))

    def test_textures_against_budget(self):
        mats = [{"name": "m", "translucent": False, "images": [
            {"name": "other.pal8.png", "size": [64, 64], "input": "Base Color"}]}]
        self.assertIn("texture-not-in-budget", codes(self.check(self.mutate(materials=mats)), "build"))
        mats[0]["images"][0] = {"name": "npc_face.pal8.png", "size": [60, 128], "input": "Base Color"}
        self.assertTrue({"texture-size", "texture-npot"} <= codes(self.check(self.mutate(materials=mats)), "build"))

    def test_dots_in_texture_names_are_preserved(self):
        model = self.mutate(materials=[{"name": "m", "translucent": False, "images": [
            {"name": "npc.face.pal8.png", "size": [64, 128], "input": "Base Color"}]}])
        budget = dict(BUDGET, textures=[{"name": "npc.face", "size": "64x128", "format": "pal8"}])
        self.assertNotIn("texture-not-in-budget", codes(self.check(model, budget), "build"))

    def test_translucency_has_no_fabricated_default(self):
        model = self.mutate(translucent_tris=600)
        self.assertNotIn("translucent-share", codes(self.check(model), "style"))
        self.assertIn("translucent-share", codes(self.check(model, dict(BUDGET, translucent_share=0.15)), "style"))
        self.assertIn("translucent-share", codes(self.check(model, dict(BUDGET, translucent_share=0)), "style"))
        self.assertIn("invalid-translucent-share", codes(self.check(model, dict(BUDGET, translucent_share=1.5)), "build"))

    def test_transform_and_degenerate(self):
        report = self.check(self.mutate(transform_applied=False, degenerate=3))
        self.assertTrue({"transform-not-applied", "degenerate"} <= codes(report, "build"))


if __name__ == "__main__":
    unittest.main()
