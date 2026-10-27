"""Check a Blender model against a sixth-gen budget and platform (runs inside Blender).

Usage:
  blender -b MODEL.blend --python check_model.py -- --budget ASSET.budget.json
          [--platform dc] [--objects A,B] [--json report.json] [--strict]

Counts come from the evaluated meshes (modifiers applied), the way an
exporter sees them. Exit 1 on any build finding; --strict also fails on style.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

from model_rules import format_report, run_checks  # noqa: E402

PLATFORMS_JSON = Path(__file__).resolve().parents[2] / "sixthgen-reference" / "platforms.json"


def script_args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def armature_of(ob):
    if ob.parent and ob.parent.type == "ARMATURE":
        return ob.parent
    for mod in ob.modifiers:
        if mod.type == "ARMATURE" and mod.object:
            return mod.object
    return None


def socket_reached(node, depth: int = 0) -> str | None:
    """Follow an image node's links downstream to the first shader input it feeds."""
    if depth > 8:
        return None
    for out in node.outputs:
        for link in out.links:
            to = link.to_node
            if to.type == "BSDF_PRINCIPLED" or to.type.endswith("_SHADER") or to.type == "EMISSION":
                return link.to_socket.name
            if to.type == "NORMAL_MAP" or to.type == "BUMP":
                return "Normal"
            if to.type == "DISPLACEMENT":
                return "Displacement"
            found = socket_reached(to, depth + 1)
            if found:
                return found
    return None


def material_info(mat) -> dict:
    images = []
    if mat and mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image and any(o.links for o in node.outputs):
                images.append({"name": node.image.name, "size": list(node.image.size), "input": socket_reached(node)})
    translucent = False
    if mat:
        method = getattr(mat, "surface_render_method", None)  # Blender 4.2+
        translucent = method == "BLENDED" if method else getattr(mat, "blend_method", "OPAQUE") == "BLEND"
    return {"name": mat.name if mat else "(none)", "translucent": translucent, "images": images}


def color_layers(me) -> list[dict]:
    out = []
    for attr in me.color_attributes:
        values = set()
        for i, d in enumerate(attr.data):
            values.add(tuple(round(c, 3) for c in d.color))
            if len(values) > 1 or i > 20000:
                break
        out.append({"name": attr.name, "domain": attr.domain, "flat": len(values) <= 1})
    return out


def export_vert_count(me) -> int:
    normals = getattr(me, "corner_normals", None)  # Blender 4.1+
    if normals is None:
        me.calc_normals_split()
    uvs = [layer.data for layer in me.uv_layers]
    col = me.color_attributes.active_color
    corner_col = col.data if col is not None and col.domain == "CORNER" else None
    keys = set()
    for loop in me.loops:
        n = normals[loop.index].vector if normals is not None else loop.normal
        key = (loop.vertex_index, round(n.x, 3), round(n.y, 3), round(n.z, 3))
        key += tuple(round(v, 5) for uv in uvs for v in uv[loop.index].uv)
        if corner_col is not None:
            key += tuple(round(c, 3) for c in corner_col[loop.index].color)
        keys.add(key)
    return len(keys)


def skin_info(ob, arm) -> dict:
    bones = {b.name for b in arm.data.bones if b.use_deform}
    groups = {g.index: g.name for g in ob.vertex_groups if g.name in bones}
    counts = [sum(1 for g in v.groups if g.group in groups and g.weight > 1e-4) for v in ob.data.vertices]
    return {"armature": arm.name, "max_influences": max(counts, default=0),
            "multi_bone_vertices": sum(1 for c in counts if c > 1),
            "unweighted_vertices": sum(1 for c in counts if c == 0)}


def extract(names: set[str] | None) -> dict:
    deps = bpy.context.evaluated_depsgraph_get()
    objects, armatures = [], set()
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or (names and ob.name not in names):
            continue
        ev = ob.evaluated_get(deps)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        tri_mat = [t.material_index for t in me.loop_triangles]
        mats = [material_info(s.material) for s in ob.material_slots] or [material_info(None)]
        translucent_idx = {i for i, m in enumerate(mats) if m["translucent"]}
        rot = ob.rotation_quaternion if ob.rotation_mode == "QUATERNION" else ob.rotation_euler.to_quaternion()
        info = {
            "name": ob.name,
            "transform_applied": all(abs(s - 1) < 1e-4 for s in ob.scale) and abs(abs(rot.w) - 1) < 1e-5,
            "tris": len(tri_mat),
            "verts": len(me.vertices),
            "export_verts": export_vert_count(me),
            "degenerate": sum(1 for p in me.polygons if p.area < 1e-10),
            "uv_layers": len(me.uv_layers),
            "color_layers": color_layers(me),
            "materials": [m for m in mats if m["name"] != "(none)"],
            "translucent_tris": sum(1 for i in tri_mat if i in translucent_idx),
            "armature": None, "max_influences": 0, "multi_bone_vertices": 0, "unweighted_vertices": 0,
        }
        arm = armature_of(ob)
        if arm:
            info.update(skin_info(ob, arm))
            armatures.add(arm)
        ev.to_mesh_clear()
        objects.append(info)
    bones = sum(sum(1 for b in a.data.bones if b.use_deform) for a in armatures)
    return {"blender": bpy.app.version_string, "objects": objects, "bones": bones}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=Path, required=True)
    ap.add_argument("--platform")
    ap.add_argument("--objects")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(script_args())

    budget = json.loads(args.budget.read_text())
    key = (args.platform or budget.get("platform") or "").lower().replace(" ", "").replace("-", "")
    key = {"dreamcast": "dc", "playstation2": "ps2", "gamecube": "gc", "wii": "gc", "ogxbox": "xbox"}.get(key, key)
    platforms = json.loads(PLATFORMS_JSON.read_text())
    if key not in platforms or key.startswith("_"):
        print(f"unknown platform '{key}': set \"platform\" in the budget (dc, ps2, gc, xbox)")
        return 2
    model = extract(set(args.objects.split(",")) if args.objects else None)
    report = run_checks(model, budget, platforms[key])
    print(format_report(report))
    if args.json:
        args.json.write_text(json.dumps({"model": model, "report": report}, indent=2))
    return 1 if report["build"] or (args.strict and report["style"]) else 0


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
