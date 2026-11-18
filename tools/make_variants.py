"""Writes the files that repeat once per colour, so all 17 chests stay in step.

Run from the repo root:  python3 tools/make_variants.py
Writes: BP items/<colour>_storage_chest.json, RP textures/item_texture.json,
RP entity/storage_chest.entity.json and RP texts/en_US.lang.
The colour list comes from tools/render_textures.py.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_textures import COLOURS, RP, BP  # noqa: E402


def title(name):
    return " ".join(w.capitalize() for w in name.split("_"))


def item_id(name):
    return "stc:storage_chest" if name == "undyed" else f"stc:{name}_storage_chest"


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    items = BP / "items"
    for old in items.glob("*storage_chest.json"):
        old.unlink()
    for name, _ in COLOURS:
        ident = item_id(name)
        write(items / f"{ident.split(':')[1]}.json", {
            "format_version": "1.21.90",
            "minecraft:item": {
                "description": {"identifier": ident, "menu_category": {"category": "items"}},
                "components": {
                    "stc:storage_chest": {},
                    "minecraft:icon": f"stc_{name}_storage_chest",
                    "minecraft:display_name": {"value": f"item.{ident}"},
                    "minecraft:max_stack_size": 1,
                },
            },
        })

    textures = {f"stc_{name}_storage_chest": {"textures": f"textures/items/stc_{name}_storage_chest"} for name, _ in COLOURS}
    textures["stc_guide"] = {"textures": "textures/items/stc_guide"}
    write(RP / "textures/item_texture.json", {
        "resource_pack_name": "storage_chests", "texture_name": "atlas.items", "texture_data": textures})

    write(RP / "entity/storage_chest.entity.json", {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": "stc:storage_chest",
                "materials": {"default": "entity"},
                "textures": {name: f"textures/entity/storage_chest/{name}" for name, _ in COLOURS},
                "geometry": {"default": "geometry.stc_storage_chest"},
                "render_controllers": ["controller.render.stc_storage_chest"],
            }
        },
    })

    lines = ["entity.stc:storage_chest.name=Storage Chest"]
    for name, _ in COLOURS:
        label = "Storage Chest" if name == "undyed" else f"{title(name)} Storage Chest"
        lines.append(f"item.{item_id(name)}={label}")
    lines.append("item.stc:guide=Storage Chests Guide")
    (RP / "texts").mkdir(parents=True, exist_ok=True)
    (RP / "texts/en_US.lang").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(COLOURS)} chest items, item_texture.json, the client entity and en_US.lang")


if __name__ == "__main__":
    main()
