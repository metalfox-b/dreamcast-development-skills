"""Dreamcast model rules, free of bpy so they can be tested without Blender.

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
    """Strip a PNG suffix and recognized format tag while retaining dots in names."""
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    lower = base.lower()
    for tag in ("pal4", "pal8", "rgb565", "argb1555", "argb4444", "vq565", "vq1555", "vq4444"):
        suffix = f".{tag}.png"
        if lower.endswith(suffix):
            return base[:-len(suffix)]
    return base[:-4] if lower.endswith(".png") else base


def run_checks(model: dict, budget: dict, plat: dict) -> dict:
    build: list[dict] = []
    style: list[dict] = []
    objects = model.get("objects", [])
    budget_tex = {t["name"]: t for t in budget.get("textures", [])}
    influences = budget.get("bone_influences")
    channels = budget.get("color_channels", plat.get("color_channels", 2))
    max_tex = plat.get("max_textures_per_polygon", 1)
    target = budget.get("target", "hardware")
    budget_findings = build if target == "hardware" else style
    if not objects:
        build.append(_finding("no-meshes", "no mesh objects were found or selected"))

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
            maximum = o.get("max_influences", 0)
            histogram = o.get("influence_histogram")
            if influences is not None and maximum > influences:
                count = (sum(number for amount, number in histogram.items() if int(amount) > influences)
                         if histogram is not None else None)
                build.append(_finding("multi-bone-vertices", f"weights exceed the project limit of {influences} bone(s) per vertex", n, count))
            elif influences is None and maximum > 1:
                style.append(_finding("multi-bone-guidance", "multiple bone influences increase CPU skinning cost; "
                                      "confirm the exporter supports them and profile the target", n,
                                      o.get("multi_bone_vertices")))
        for m in o["materials"]:
            color_images = [i for i in m["images"] if i.get("input") in COLOR_INPUTS or i.get("input") is None]
            image_names = {i["name"] for i in color_images}
            if len(image_names) > max_tex:
                style.append(_finding("multi-texture", f"material '{m['name']}' uses {len(image_names)} color textures; "
                                      "the PVR uses one texture per polygon pass. Confirm extra passes or bake a texture", n))
            modern = sorted({i["input"] for i in m["images"] if i.get("input") in MODERN_INPUTS})
            if modern:
                style.append(_finding("modern-material", f"material '{m['name']}' drives {', '.join(modern)} with a texture; "
                                      "Dreamcast shading often uses vertex colors and a color texture", n))
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

    if budget.get("tris") is not None and total_tris > budget["tris"]:
        budget_findings.append(_finding("over-tri-budget", f"{total_tris} triangles; the budget is {budget['tris']}", count=total_tris))
    if budget.get("verts") is not None and total_export > budget["verts"]:
        budget_findings.append(_finding("over-vert-budget", f"{total_export} export verts; the budget is {budget['verts']}",
                              count=total_export))
    if budget.get("materials") is not None and len(materials) > budget["materials"]:
        budget_findings.append(_finding("over-material-budget", f"{len(materials)} materials; the budget is {budget['materials']}",
                              count=len(materials)))
    if budget.get("bones") is not None and model.get("bones", 0) > budget["bones"]:
        budget_findings.append(_finding("over-bone-budget", f"{model['bones']} deform bones; the budget is {budget['bones']}",
                              count=model["bones"]))
    share = budget.get("translucent_share")
    translucent = sum(o.get("translucent_tris", 0) for o in objects)
    if share is not None and (isinstance(share, bool) or not isinstance(share, (int, float)) or not 0 <= share <= 1):
        build.append(_finding("invalid-translucent-share", "translucent_share must be between 0 and 1"))
    elif share is not None and total_tris and translucent / total_tris > share:
        style.append(_finding("translucent-share", f"{translucent} of {total_tris} triangles are translucent "
                              f"({100 * translucent / total_tris:.0f}%); ration transparency on {plat['name']} "
                              f"(guide: {100 * share:.0f}%). Use punch-through cutouts where you can", count=translucent))

    return {"platform": plat["name"], "target": target,
            "totals": {"tris": total_tris, "export_verts": total_export, "materials": len(materials),
                       "bones": model.get("bones", 0), "translucent_tris": translucent},
            "build": build, "style": style}


def format_report(report: dict, strict: bool = False) -> str:
    t = report["totals"]
    lines = [f"{report['platform']} model check (target {report['target']}): {t['tris']} tris, "
             f"{t['export_verts']} export verts, {t['materials']} materials, {t['bones']} bones"]
    for kind in ("build", "style"):
        for f in report[kind]:
            where = f" [{f['object']}]" if f.get("object") else ""
            count = f" ({f['count']})" if f.get("count") is not None and str(f["count"]) not in f["message"] else ""
            lines.append(f"  {kind.upper():5} {f['code']}{where}: {f['message']}{count}")
    verdict = ("FAIL (build)" if report["build"] else
               "FAIL (style)" if strict and report["style"] else
               "PASS with style findings" if report["style"] else "PASS")
    lines.append(f"Verdict: {verdict}")
    return "\n".join(lines)
