"""Vertex-color shading recipe (no bpy): AO + warm top light + limb gradient + subtle tints.

bake_vertex_colors.py measures AO, normals and limb position in Blender, then
calls shade() per vertex. Colors are sRGB floats 0..1.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


def hex_to_rgb(s: str) -> tuple[float, float, float]:
    s = s.strip().lstrip("#")
    return tuple(int(s[i:i + 2], 16) / 255 for i in (0, 2, 4))


@dataclass
class Recipe:
    lit: tuple = hex_to_rgb("#F0E8E0")      # warm off-white fill
    shadow: tuple = hex_to_rgb("#8A7FA0")   # cool desaturated purple, never black
    warm: tuple = hex_to_rgb("#FFF0D0")     # extra light on top-facing planes
    warm_amount: float = 0.35
    gradient: float = 0.15                  # darkening from limb root to tip
    jitter: float = 0.06                    # subtle random hue drift
    noise_scale: float = 4.0                # tint patches per Blender unit
    floor: float = 0.18                     # darkest any channel may go


def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _hash(ix: int, iy: int, iz: int, seed: int) -> float:
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 144665) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 0xFFFF * 2 - 1


def value_noise(x: float, y: float, z: float, seed: int = 0) -> float:
    """Smooth 3D value noise in -1..1: neighboring vertices get similar values,
    so tints form soft patches instead of per-vertex speckle."""
    ix, iy, iz = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - ix, y - iy, z - iz
    sx, sy, sz = (f * f * (3 - 2 * f) for f in (fx, fy, fz))
    acc = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (sx if dx else 1 - sx) * (sy if dy else 1 - sy) * (sz if dz else 1 - sz)
                acc += w * _hash(ix + dx, iy + dy, iz + dz, seed)
    return acc


def shade(ao: float, up: float, limb_t: float, pos: tuple, seed: int, r: Recipe) -> tuple[float, float, float]:
    """ao: 1 = open, 0 = fully occluded. up: normal.z (-1..1). limb_t: 0 at limb root, 1 at tip."""
    c = _lerp(r.shadow, r.lit, max(0.0, min(1.0, ao)))
    c = _lerp(c, r.warm, r.warm_amount * max(0.0, up))
    k = 1 - r.gradient * max(0.0, min(1.0, limb_t))
    c = tuple(v * k for v in c)
    # two independent noise channels push towards warm (red) or green, never both
    p = [v * r.noise_scale for v in pos]
    n1 = value_noise(*p, seed=seed)
    n2 = value_noise(*p, seed=seed + 101)
    c = (c[0] + r.jitter * n1, c[1] + r.jitter * n2, c[2] - r.jitter * 0.5 * (n1 + n2) / 2)
    return tuple(max(r.floor, min(1.0, v)) for v in c)


def srgb_to_linear(v: float) -> float:
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def hemisphere_dirs(n: int) -> list[tuple[float, float, float]]:
    """Deterministic cosine-weighted directions around +Z (Fibonacci spiral)."""
    dirs = []
    golden = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        u = (i + 0.5) / n
        rr = math.sqrt(u)
        th = i * golden
        dirs.append((rr * math.cos(th), rr * math.sin(th), math.sqrt(1 - u)))
    return dirs


def orient(d: tuple, n: tuple) -> tuple[float, float, float]:
    """Rotate direction d from +Z space onto normal n."""
    nx, ny, nz = n
    if nz < -0.9999:
        return (d[0], -d[1], -d[2])
    a = 1 / (1 + nz)
    b = -nx * ny * a
    t = (1 - nx * nx * a, b, -nx)
    bt = (b, 1 - ny * ny * a, -ny)
    return tuple(d[0] * t[i] + d[1] * bt[i] + d[2] * n[i] for i in range(3))
