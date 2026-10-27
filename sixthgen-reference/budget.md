# The budget file

`<asset>.budget.json` is the contract between the sixth-gen skills. `sixthgen-asset` writes it to match the agreed constraints; `validate_textures.py --budget` and `check_model.py --budget` check against it. Keep it next to the asset or where the project stores its source art.

## Fields

```json
{
  "asset": "example_npc",
  "platform": "dc",
  "target": "hardware",
  "project": "my-dc-game",
  "kind": "npc",
  "tris": 1500,
  "verts": 1900,
  "bones": 16,
  "bone_influences": 1,
  "materials": 3,
  "color_channels": 1,
  "textures": [
    {"name": "example_npc_face", "size": "64x128", "format": "pal8",  "tile": {"u": "mirror", "v": "clamp"}},
    {"name": "example_npc_coat", "size": "128x128", "format": "vq565", "mips": true, "tile": {"u": "repeat", "v": "repeat"}}
  ],
  "untextured": ["hands", "boots"],
  "effects": ["lamp halo"]
}
```

| Field | Meaning | Checked by |
|---|---|---|
| `asset` | Short name, the prefix of every texture name | — |
| `platform` | `dc`, `ps2`, `gc` or `xbox`: a profile in [platforms.md](platforms.md) | both scripts |
| `target` | `hardware` (limits fail the build, hardware test required) or `style` (limits warn, preview stands in) | both scripts, `sixthgen-asset` |
| `project` | Project profile key, for export, run and capture | `sixthgen-asset` |
| `kind` | `character`, `npc`, `prop`, `level` or `effect` | `sixthgen-asset` |
| `tris` | Maximum triangles after triangulation, modifiers applied | `check_model.py` (style) |
| `verts` | Optional maximum **export verts**: one per unique position + normal + UV + color, the count the console transforms | `check_model.py` (style) |
| `bones`, `materials` | Maximums | `check_model.py` (style) |
| `bone_influences` | Bones per vertex. Default from the platform (1) | `check_model.py` (build) |
| `color_channels` | Color attribute layers per mesh. Default 2 | `check_model.py` (style) |
| `textures` | Every texture the asset may use: name (no tag), stored size, platform format tag, optional `mips` and `npot`, tile modes per axis | both scripts |
| `untextured` | Parts drawn with vertex color only. Documentation for the modeler | — |
| `effects` | Faked effects the asset carries, each naming a recipe in [effects.md](effects.md) | `sixthgen-asset` |

Tile modes must exist on the platform (`platforms.json` → `tile_modes`): PS2 has no `mirror`.

## Defaults by kind (Dreamcast)

Ranges are calibrated from Elias Daler's and NekoEye's figures; the defaults in brackets, the lower bounds, bone counts and the effect row are our inference. PS2, GameCube and Xbox have no practitioner budgets yet: start from these and raise only after the asset runs on the target.

| Kind | Tris | Textures | Bones | Notes |
|---|---|---|---|---|
| Hero character | 1,000–2,000 (default 1,500) | 2–4, mostly 128²–256² | 12–24 | Elias considers 2,760 too high for a Dreamcast character; Sonic Adventure's Sonic is ~1k |
| NPC | 600–2,000 (default 1,200) | 1–3 | 0–16 | Elias targets under 2k |
| Prop | 50–500 (default 200) | 0–2 | 0 | Many props should be vertex color only |
| Level / scene | ~10–15k visible verts at 60 fps (inference); ~25k tris at 30 fps | tally the whole set | — | Set `tris` to the visible budget for one camera view, not the whole level |
| Effect | 4–100 | 0–1 | 0 | Mostly translucent; counts against the DC translucency ration |

Scene budget per platform: Shenmue stays under ~14k on-screen verts (measured by NekoEye in Deecy; frame rate not stated); Soul Blaze peaks at ~24k (likely verts) and ~25k visible tris at a locked 30 fps, with a higher estimate if shadows were removed. Elias's estimate of under 2K polygons for NPCs may mean faces; budgets here read it as triangles.

## Texture sizes

- Most surfaces 128²–256²; 512² only for skies and hero textures (a 1024² VQ face is still ~344 KB with mips).
- Run `validate_textures.py --platform <p> --plan WxH FMT` before painting, and `--cheat-sheet` for the full table (generated; never copy it here).
