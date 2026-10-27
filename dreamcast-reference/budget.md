# Dreamcast asset budget

Store an asset budget with the project. The example is a **starting point**, not a universal hardware specification. The project's engine, exporter, scene, and measured memory set the real limits.

```json
{
  "asset": "example_npc",
  "platform": "dc",
  "target": "hardware",
  "kind": "npc",
  "tris": 1500,
  "verts": 1900,
  "bones": 16,
  "materials": 3,
  "color_channels": 1,
  "textures": [
    {"name": "example_npc_face", "size": "64x128", "format": "pal8", "tile": {"u": "mirror", "v": "clamp"}},
    {"name": "example_npc_coat", "size": "128x128", "format": "vq565", "mips": true, "tile": {"u": "repeat", "v": "repeat"}}
  ],
  "untextured": ["hands", "boots"],
  "effects": ["lamp halo"]
}
```

| Field | Meaning |
|---|---|
| `platform` | `dc` or `dreamcast`. Other platforms are rejected. |
| `target` | `hardware` by default: explicit model and texture budgets fail on overrun. `style` makes aggregate triangle, vertex, bone, material, and memory budget overruns warnings; explicit exporter limits still fail. It does not certify hardware. |
| `tris`, `verts`, `bones`, `materials` | Optional project limits for evaluated triangles, estimated export vertices, deform bones, and materials. |
| `bone_influences` | Optional exporter or project limit per vertex. Omit when unknown: multi-bone weights then produce guidance rather than a build failure. |
| `color_channels` | Optional working limit; otherwise two is a review heuristic. Confirm the layer actually read by the exporter. |
| `textures` | Name, PNG size, format tag, planned mipmaps, and tile modes. `npot` identifies a project-approved strided texture for model checks. |
| `untextured`, `effects` | Documentation for the asset; the model checker does not verify these lists. |
| `translucent_share` | Optional project-specific *triangle-count* review threshold between 0 and 1. It is not a measure of screen-space overdraw or a hardware limit. |

The texture validator calculates planned mipmap memory from `mips`; it does **not** verify a mip chain inside a PNG or the converted file. Inspect the encoder output and runtime loader. Texture and palette memory are estimates until checked against the actual encoded assets and game allocations.

## Initial art ranges

For early planning only, a character might start near 1,000–2,000 triangles and ordinary textures near 128–256 pixels per side. The research gives [particular character examples](sources.md#skinning-and-geometry), not a console-wide rule. Set budgets based on the number of visible actors, scene complexity, desired frame time, rendering method, and measurements from the actual game.
