"""Bake a base vertex-color shading layer with a lightweight stylized recipe (runs inside Blender).

Usage:
  blender -b MODEL.blend --python bake_vertex_colors.py -- [--output OUT.blend | --in-place]
          [--layer Col_Bake] [--objects A,B] [--samples 32] [--distance D] [--seed 0]
          [--lit #F0E8E0] [--shadow #8A7FA0] [--warm #FFF0D0] [--jitter 0.06] [--gradient 0.15]

Per vertex: ambient occlusion (ray cast against every baked mesh, so the arm
shadows the torso) mapped from a warm off-white to a cool purple, extra warm
light on top-facing planes, darkening from each limb's root to its tip, and
soft Rare-style random tints. This is a starting layer for an artist to paint over.

Writes a byte-color, face-corner layer (default Col_Bake). Writing into an
existing layer needs --force. Without --in-place, saves to OUT.blend
(default: MODEL_baked.blend).
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

from vcolor_math import (Recipe, hemisphere_dirs, hex_to_rgb, orient, shade,  # noqa: E402
                         srgb_to_linear)


def script_args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def armature_of(ob):
    if ob.parent and ob.parent.type == "ARMATURE":
        return ob.parent
    for mod in ob.modifiers:
        if mod.type == "ARMATURE" and mod.object:
            return mod.object
    return None


def world_rest_mesh(ob, depsgraph):
    """World-space rest-pose (verts, normals, polygons) of ob, armature modifiers off."""
    disabled = [m for m in ob.modifiers if m.type == "ARMATURE" and m.show_viewport]
    for m in disabled:
        m.show_viewport = False
    depsgraph.update()
    ev = ob.evaluated_get(depsgraph)
    me = ev.to_mesh()
    mw = ob.matrix_world
    nm = mw.to_3x3().inverted_safe().transposed()
    verts = [mw @ v.co for v in me.vertices]
    normals = [(nm @ v.normal).normalized() for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    for m in disabled:
        m.show_viewport = True
    return verts, normals, polys


def limb_position(ob, arm, vi: int, co: Vector, zmin: float, zmax: float) -> float:
    """0 at the root of the vertex's bone, 1 at its tip; without a rig, top-to-bottom."""
    if arm is not None:
        groups = sorted(ob.data.vertices[vi].groups, key=lambda g: -g.weight)
        for g in groups:
            name = ob.vertex_groups[g.group].name
            bone = arm.data.bones.get(name)
            if bone is None:
                continue
            head = arm.matrix_world @ bone.head_local
            tail = arm.matrix_world @ bone.tail_local
            axis = tail - head
            if axis.length_squared < 1e-12:
                break
            return max(0.0, min(1.0, (co - head).dot(axis) / axis.length_squared))
    return 0.0 if zmax - zmin < 1e-9 else 1 - (co.z - zmin) / (zmax - zmin)


def main() -> int:
    ap = argparse.ArgumentParser(prog="bake_vertex_colors.py")
    out = ap.add_mutually_exclusive_group()
    out.add_argument("--output")
    out.add_argument("--in-place", action="store_true")
    ap.add_argument("--layer", default="Col_Bake")
    ap.add_argument("--force", action="store_true", help="overwrite an existing layer")
    ap.add_argument("--objects")
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--distance", type=float, help="AO ray length in BU (default: 25%% of model height)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lit", default="#F0E8E0")
    ap.add_argument("--shadow", default="#8A7FA0")
    ap.add_argument("--warm", default="#FFF0D0")
    ap.add_argument("--jitter", type=float, default=0.06)
    ap.add_argument("--gradient", type=float, default=0.15)
    args = ap.parse_args(script_args())

    recipe = Recipe(lit=hex_to_rgb(args.lit), shadow=hex_to_rgb(args.shadow), warm=hex_to_rgb(args.warm),
                    jitter=args.jitter, gradient=args.gradient)
    names = set(args.objects.split(",")) if args.objects else None
    targets = [o for o in bpy.context.scene.objects if o.type == "MESH" and (not names or o.name in names)]
    if not targets:
        print("no mesh objects found")
        return 2

    for ob in targets:
        if args.layer in ob.data.color_attributes and not args.force:
            print(f"{ob.name} already has a '{args.layer}' layer; pass --force to overwrite or --layer to pick another")
            return 2

    depsgraph = bpy.context.evaluated_depsgraph_get()
    meshes = {ob.name: world_rest_mesh(ob, depsgraph) for ob in targets}
    for ob in targets:
        if len(meshes[ob.name][0]) != len(ob.data.vertices):
            print(f"{ob.name}: modifiers change the vertex count (e.g. Mirror, Subdivision) — apply them first")
            return 2

    # one BVH over every target so occlusion crosses objects
    all_verts, all_polys = [], []
    for verts, _, polys in meshes.values():
        base = len(all_verts)
        all_verts += verts
        all_polys += [tuple(base + i for i in p) for p in polys]
    bvh = BVHTree.FromPolygons(all_verts, all_polys)
    zs = [v.z for v in all_verts]
    zmin, zmax = min(zs), max(zs)
    distance = args.distance or max(1e-3, 0.25 * (zmax - zmin))
    eps = distance * 1e-3
    dirs = hemisphere_dirs(args.samples)

    for ob in targets:
        verts, normals, _ = meshes[ob.name]
        arm = armature_of(ob)
        colors = []
        for vi, (co, n) in enumerate(zip(verts, normals)):
            origin = co + n * eps
            hits = 0
            for d in dirs:
                ray = Vector(orient(d, tuple(n)))
                loc, *_ = bvh.ray_cast(origin, ray, distance)
                if loc is not None:
                    hits += 1
            ao = 1 - hits / len(dirs)
            t = limb_position(ob, arm, vi, co, zmin, zmax)
            colors.append(shade(ao, n.z, t, tuple(co), args.seed, recipe))

        me = ob.data
        layer = me.color_attributes.get(args.layer) or me.color_attributes.new(args.layer, "BYTE_COLOR", "CORNER")
        for loop in me.loops:
            r, g, b = colors[loop.vertex_index]
            if hasattr(layer.data[loop.index], "color_srgb"):
                layer.data[loop.index].color_srgb = (r, g, b, 1.0)
            else:
                layer.data[loop.index].color = (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)
        print(f"{ob.name}: baked {len(verts)} vertices into '{args.layer}'")

    if args.in_place:
        bpy.ops.wm.save_mainfile()
        print(f"saved {bpy.data.filepath}")
    else:
        path = args.output or bpy.data.filepath.replace(".blend", "_baked.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
        print(f"saved {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
