"""
Inject Alchemy Main & Sub 4-slot Searchable Options into interface.json.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTERFACE_PATH = PROJECT_ROOT / "assets" / "interface.json"
CATALOG_PATH = PROJECT_ROOT / "assets" / "resource" / "alchemy_materials_catalog.json"

POPULAR_MAINS = ["小齿轮", "柴薪", "普通木头", "柳安木", "普通木材", "铁矿", "铜矿", "麻线"]
POPULAR_SUBS = ["馒头", "草菇", "普通石块", "页岩", "蘑菇", "香菇", "纯水", "白兔毛", "熟皮"]


def main():
    with open(INTERFACE_PATH, "r", encoding="utf-8") as f:
        interface = json.load(f)

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        raw_cases = json.load(f)

    # Reorder cases: None first, then Popular items, then rest sorted by level
    none_case = raw_cases[0]
    other_cases = raw_cases[1:]

    # Map name -> case
    case_map = {c["name"]: c for c in other_cases}

    def build_ordered_cases(popular_list):
        res = [none_case]
        added = set()
        for p in popular_list:
            if p in case_map:
                res.append(case_map[p])
                added.add(p)
        for c in other_cases:
            if c["name"] not in added:
                res.append(c)
        # Format case for interface.schema: remove item_id/template from case root
        cleaned = []
        for c in res:
            entry = {
                "name": c["name"],
                "label": c["label"],
                "description": c.get("description", "")
            }
            if "icon" in c:
                entry["icon"] = c["icon"]
            cleaned.append(entry)
        return cleaned

    main_cases = build_ordered_cases(POPULAR_MAINS)
    sub_cases = build_ordered_cases(POPULAR_SUBS)

    # 4 Main Material Slots
    main_options = {
        "AlchemyMainMaterial1": {
            "type": "select",
            "label": "主材料第 1 顺位 (首选)",
            "description": "首选投入的主材料。支持在下拉框直接输入搜索名称 (如「小齿轮」) 或物等代码 (如「1木」「1铁」)，选中自动回填",
            "default_case": "小齿轮",
            "cases": main_cases
        },
        "AlchemyMainMaterial2": {
            "type": "select",
            "label": "主材料第 2 顺位 (备选 1)",
            "description": "第 1 顺位耗尽时使用的备选主材。支持搜索名称或物等代码",
            "default_case": "柴薪",
            "cases": main_cases
        },
        "AlchemyMainMaterial3": {
            "type": "select",
            "label": "主材料第 3 顺位 (备选 2)",
            "description": "第 2 顺位耗尽时使用的备选主材。支持搜索名称或物等代码",
            "default_case": "None",
            "cases": main_cases
        },
        "AlchemyMainMaterial4": {
            "type": "select",
            "label": "主材料第 4 顺位 (备选 3)",
            "description": "第 3 顺位耗尽时使用的备选主材。支持搜索名称或物等代码",
            "default_case": "None",
            "cases": main_cases
        }
    }

    # 4 Sub Material Slots
    sub_options = {
        "AlchemySubMaterial1": {
            "type": "select",
            "label": "副材料第 1 顺位 (首选)",
            "description": "首选投入的副材料。支持在下拉框直接输入搜索名称 (如「馒头」) 或物等代码 (如「1草」「1石」)，选中自动回填",
            "default_case": "馒头",
            "cases": sub_cases
        },
        "AlchemySubMaterial2": {
            "type": "select",
            "label": "副材料第 2 顺位 (备选 1)",
            "description": "第 1 顺位耗尽时使用的备选副材。支持搜索名称或物等代码",
            "default_case": "草菇",
            "cases": sub_cases
        },
        "AlchemySubMaterial3": {
            "type": "select",
            "label": "副材料第 3 顺位 (备选 2)",
            "description": "第 2 顺位耗尽时使用的备选副材。支持搜索名称或物等代码",
            "default_case": "普通石块",
            "cases": sub_cases
        },
        "AlchemySubMaterial4": {
            "type": "select",
            "label": "副材料第 4 顺位 (备选 3)",
            "description": "第 3 顺位耗尽时使用的备选副材。支持搜索名称或物等代码",
            "default_case": "None",
            "cases": sub_cases
        }
    }

    # Merge into option dictionary
    if "option" not in interface:
        interface["option"] = {}

    interface["option"].update(main_options)
    interface["option"].update(sub_options)

    # Attach to 连续炼金 task
    for t in interface.get("task", []):
        if t.get("name") == "连续炼金":
            t["option"] = [
                "AlchemyMainMaterial1",
                "AlchemyMainMaterial2",
                "AlchemyMainMaterial3",
                "AlchemyMainMaterial4",
                "AlchemySubMaterial1",
                "AlchemySubMaterial2",
                "AlchemySubMaterial3",
                "AlchemySubMaterial4"
            ]

    with open(INTERFACE_PATH, "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)

    print("Successfully injected 8 searchable material slots into interface.json!")


if __name__ == "__main__":
    main()
