"""Sixth-gen model rules, free of bpy so they can be tested without Blender.

check_model.py extracts this from a .blend and calls run_checks():

{
  "objects": [{
    "name": str, "transform_applied": bool,
    "tris": int, "verts": int, "export_verts": int, "degenerate": int,
    "uv_layers": int,
    "color_layers": [{"name": str, "domain": "CORNER"|"POINT", "flat": bool}],
    "materials": [{"name": str, "translucent": bool,
                   "images": [{"name": str, "size": [w, h], "input": "Base Color"|...}]}],
    "translucent_tris": int,
    "armature": str | None, "max_influences": int,
    "multi_bone_vertices": int, "unweighted_vertices": int
  }],
  "bones": int
}

export_verts counts vertices as the console sees them: one per unique
(position, normal, UV, color) corner, so every hard edge and seam adds some.
"""
from __future__ import annotations

COLOR_INPUTS = {"Base Color", "Alpha", "Color"}
MODERN_INPUTS = {"Normal", "Roughness", "Metallic", "Specular IOR Level", "Specular", "Emission Color",
                 "Emission", "Coat Weight", "Coat Normal", "Sheen Weight", "Subsurface Weight", "Displacement"}
SPLIT_RATIO = 1.8  # inference: export verts per position above this means many hard edges or seams
SPLIT_MIN_VERTS = 50  # small props (a cube is 24 corners on 8 positions) are exempt


def _finding(code: str, message: str, obj: str | None = None, count: int | None = None) -> dict:
    f = {"code": code, "message": message}
    if obj:
        f["object"] = obj
    if count is not None:
        f["count"] = count
    return f


def _is_pot(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def _stem(name: str) -> str:
    """npc_face.pal8.png -> npc_face"""
    parts = name.split(".")
    return parts[0] if parts else name


def run_checks(model: dict, budget: dict, plat: dict) -> dict:
    build: list[dict] = []
    style: list[dict] = []
    objects = model.get("objects", [])
    budget_tex = {t["name"]: t for t in budget.get("textures", [])}
    influences = budget.get("bone_influences", plat.get("bone_influences", 1))
    channels = budget.get("color_channels", plat.get("color_channels", 2))
    max_tex = plat.get("max_textures_per_polygon", 1)

    total_tris = sum(o["tris"] for o in objects)
    total_export = sum(o["export_verts"] for o in objects)
    materials = {m["name"]: m for o in objects for m in o["materials"]}

    for o in objects:
        n = o["name"]
        # --- build
        if not o.get("transform_applied", True):
            build.append(_finding("transform-not-applied", "rotation or scale not applied (Ctrl+A)", n))
        if o.get("degenerate"):
            build.append(_finding("degenerate", "zero-area faces", n, o["degenerate"]))
        if o.get("armature"):
            if o.get("unweighted_vertices"):
                build.append(_finding("unweighted-vertices", "vertices with no bone weight", n, o["unweighted_vertices"]))
            if o.get("max_influences", 0) > influences:
                build.append(_finding("multi-bone-vertices", f"vertices weighted to more than {influences} bone(s); "
                                      "sixth-gen skinning is one joint per vertex", n, o["multi_bone_vertices"]))
        for m in o["materials"]:
            color_images = [i for i in m["images"] if i.get("input") in COLOR_INPUTS or i.get("input") is None]
            if len(color_images) > max_tex:
                if plat.get("multipass"):
                    style.append(_finding("multipass", f"material '{m['name']}' blends {len(color_images)} textures: "
                                          "one extra pass each on the GS (cheap fill, more VRAM)", n))
                else:
                    build.append(_finding("multi-texture", f"material '{m['name']}' blends {len(color_images)} textures; "
                                          f"{plat['name']} allows {max_tex} per polygon. Layer polygons or bake one texture", n))
            modern = sorted({i["input"] for i in m["images"] if i.get("input") in MODERN_INPUTS})
            if modern:
                style.append(_finding("modern-material", f"material '{m['name']}' drives {', '.join(modern)} with a texture; "
                                      "sixth-gen shading lives in vertex colors and the color texture", n))
            if m["images"] and not o.get("uv_layers"):
                style.append(_finding("no-uvs", f"textured material '{m['name']}' on a mesh with no UV map", n))
            for img in m["images"]:
                stem = _stem(img["name"])
                spec = budget_tex.get(stem)
                w, h = img["size"]
                if spec is None:
                    build.append(_finding("texture-not-in-budget", f"texture '{img['name']}' isn't in the budget", n))
                    continue
                if f"{w}x{h}" != spec["size"]:
                    build.append(_finding("texture-size", f"'{stem}' is {w}x{h}; the budget says {spec['size']}", n))
                if not (_is_pot(w) and _is_pot(h)) and not spec.get("npot"):
                    build.append(_finding("texture-npot", f"'{stem}' is {w}x{h}, not power-of-two", n))
        # --- style
        layers = o.get("color_layers", [])
        if not layers:
            style.append(_finding("no-vertex-colors", "no color attribute: lighting lives in vertex colors", n))
        elif all(c["flat"] for c in layers):
            style.append(_finding("flat-vertex-colors", "color attributes are a single flat color (unpainted)", n))
        if len(layers) > channels:
            style.append(_finding("color-channels", f"{len(layers)} color layers; the budget allows {channels} "
                                  "(each costs memory per vertex)", n, len(layers)))
        if o["verts"] >= SPLIT_MIN_VERTS and o["export_verts"] / o["verts"] > SPLIT_RATIO:
            style.append(_finding("split-heavy", f"{o['export_verts']} export verts from {o['verts']} positions: hard edges, "
                                  "UV seams and color seams each duplicate vertices. Weld and keep hard edges deliberate", n))

    if budget.get("tris") and total_tris > budget["tris"]:
        style.append(_finding("over-tri-budget", f"{total_tris} triangles; the budget is {budget['tris']}", count=total_tris))
    if budget.get("verts") and total_export > budget["verts"]:
        style.append(_finding("over-vert-budget", f"{total_export} export verts; the budget is {budget['verts']}",
                              count=total_export))
    if budget.get("materials") and len(materials) > budget["materials"]:
        style.append(_finding("over-material-budget", f"{len(materials)} materials; the budget is {budget['materials']}",
                              count=len(materials)))
    if budget.get("bones") is not None and model.get("bones", 0) > budget["bones"]:
        style.append(_finding("over-bone-budget", f"{model['bones']} deform bones; the budget is {budget['bones']}",
                              count=model["bones"]))
    share = plat.get("translucent_share")
    translucent = sum(o.get("translucent_tris", 0) for o in objects)
    if share and total_tris and translucent / total_tris > share:
        style.append(_finding("translucent-share", f"{translucent} of {total_tris} triangles are translucent "
                              f"({100 * translucent / total_tris:.0f}%); ration transparency on {plat['name']} "
                              f"(guide: {100 * share:.0f}%). Use punch-through cutouts where you can", count=translucent))

    return {"platform": plat["name"], "target": budget.get("target", "style"),
            "totals": {"tris": total_tris, "export_verts": total_export, "materials": len(materials),
                       "bones": model.get("bones", 0), "translucent_tris": translucent},
            "build": build, "style": style}


def format_report(report: dict) -> str:
    t = report["totals"]
    lines = [f"{report['platform']} model check (target {report['target']}): {t['tris']} tris, "
             f"{t['export_verts']} export verts, {t['materials']} materials, {t['bones']} bones"]
    for kind in ("build", "style"):
        for f in report[kind]:
            where = f" [{f['object']}]" if f.get("object") else ""
            count = f" ({f['count']})" if f.get("count") is not None and str(f["count"]) not in f["message"] else ""
            lines.append(f"  {kind.upper():5} {f['code']}{where}: {f['message']}{count}")
    verdict = "FAIL (build)" if report["build"] else ("PASS with style findings" if report["style"] else "PASS")
    lines.append(f"Verdict: {verdict}")
    return "\n".join(lines)
