"""
Build 1-3 level alchemy material catalog, generate recognition templates,
and configure search-enabled options in interface.json.
"""

import json
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ITEMDATA_PATH = Path(r"D:\飘流幻境新世界\pln-recode\runs\2026-08-25-101358\parsed\itemdata.json")
ICONS_DIR = Path(r"D:\飘流幻境新世界\pln-recode\tools\item-icons\output\icons")

MATERIAL_ABBR_MAP = {
    "木材": "木",
    "木": "木",
    "蔬菜": "草",
    "草": "草",
    "花类纤维": "花",
    "叶类纤维": "叶",
    "草类纤维": "草",
    "纤维": "纤",
    "石头": "石",
    "铜": "铜",
    "铁": "铁",
    "纯水": "水",
    "水": "水",
    "兽皮": "皮",
    "兽毛": "毛",
    "兽骨": "骨",
    "头骨": "骨",
    "鸟类羽毛": "羽",
    "羽毛": "羽",
    "甲壳": "壳",
    "粮食": "粮",
    "机械": "机",
    "贵金属": "金",
    "金": "金",
    "银": "银",
    "铝": "铝",
    "铅": "铅",
    "锡": "锡",
    "钢铁": "钢",
    "钛": "钛",
    "玉": "玉",
    "黏土": "土",
}


def make_template(src_icon: Path, dst_template: Path):
    """Generate 71x55 green-masked recognition template."""
    img = Image.open(src_icon).convert("RGBA").resize((71, 70), Image.Resampling.LANCZOS)
    green = Image.new("RGB", (71, 70), (0, 255, 0))
    green.paste(img, mask=img.getchannel("A"))
    dst_template.parent.mkdir(parents=True, exist_ok=True)
    # Crop bottom number area to keep top 71x55
    green.crop((0, 0, 71, 55)).save(dst_template, "PNG")


def make_ui_icon(src_icon: Path, dst_icon: Path):
    """Generate 32x32 UI icon."""
    img = Image.open(src_icon).convert("RGBA").resize((32, 32), Image.Resampling.LANCZOS)
    dst_icon.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst_icon, "PNG")


def main():
    print("Loading itemdata...")
    with open(ITEMDATA_PATH, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)

    items = data.get("items", [])
    print(f"Loaded {len(items)} total items.")

    materials_dir = PROJECT_ROOT / "assets" / "resource" / "image" / "alchemy" / "materials"
    icons_dir = PROJECT_ROOT / "assets" / "resource" / "image" / "alchemy" / "icons"
    materials_dir.mkdir(parents=True, exist_ok=True)
    icons_dir.mkdir(parents=True, exist_ok=True)

    # Filter: 1 <= level <= 3, can_be_alchemy_result == True, has material
    # Exclude test items and furniture
    filtered = []
    seen_names = set()

    for it in items:
        lvl = it.get("level", 0)
        name = str(it.get("name", "")).strip()
        mat = str(it.get("material", "")).strip()
        can_res = it.get("can_be_alchemy_result", False)
        icon_id = str(it.get("icon_id", "")).strip()
        category = str(it.get("category", "")).strip()
        item_type = str(it.get("type", "")).strip()

        if (
            1 <= lvl <= 3
            and can_res
            and mat
            and "(未" not in name
            and "(测试" not in name
            and "家具" not in category
            and "任务" not in category
            and "装备" not in item_type
            and "装备" not in category
            and icon_id
        ):
            src_icon = ICONS_DIR / f"s{icon_id}.png"
            if src_icon.exists() and name not in seen_names:
                seen_names.add(name)
                filtered.append({
                    "id": it.get("id"),
                    "name": name,
                    "level": lvl,
                    "material": mat,
                    "icon_id": icon_id,
                    "src_icon": src_icon
                })

    # Sort by level ascending, then material, then name
    filtered.sort(key=lambda x: (x["level"], x["material"], x["name"]))
    print(f"Filtered {len(filtered)} valid Lv 1..3 craftable materials.")

    # Generate images
    cases = [
        {
            "name": "None",
            "label": "无 (不启用此顺位)",
            "description": "留空不启用此顺位材料"
        }
    ]

    for it in filtered:
        item_id = it["id"]
        icon_id = it["icon_id"]
        name = it["name"]
        lvl = it["level"]
        mat = it["material"]
        abbr = MATERIAL_ABBR_MAP.get(mat, mat[:1])
        code = f"{lvl}{abbr}"

        # Generate template and ui icon
        dst_tmpl = materials_dir / f"{item_id}.png"
        dst_icon = icons_dir / f"{icon_id}.png"
        
        make_template(it["src_icon"], dst_tmpl)
        make_ui_icon(it["src_icon"], dst_icon)

        # Build case entry
        label = f"{name} (Lv{lvl} {mat}) [{code}]"
        rel_icon_path = f"resource/image/alchemy/icons/{icon_id}.png"
        rel_tmpl_path = f"alchemy/materials/{item_id}.png"

        cases.append({
            "name": name,
            "label": label,
            "description": f"物等: Lv{lvl} | 材质: {mat} | 代码: {code}",
            "icon": rel_icon_path,
            "item_id": item_id,
            "template": rel_tmpl_path
        })

    # Save catalog definition
    catalog_json = PROJECT_ROOT / "assets" / "resource" / "alchemy_materials_catalog.json"
    with open(catalog_json, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(cases)-1} templates & catalog at {catalog_json}")


if __name__ == "__main__":
    main()
