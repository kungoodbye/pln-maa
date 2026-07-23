# 小鸡腿资源回收循环 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox `- [ ]` syntax for tracking.

**Goal:** Add an optional MaaFramework task that repeatedly recycles full stacks of chicken legs and stops normally after three lower-inventory searches without a match.

**Architecture:** A new JSON Pipeline opens the recycle window through its fixed home-screen location, then gates every page and dialog with OCR. A green-masked chicken-leg template chooses the first visual match; four explicit search states bound the scan to the initial view plus three swipes, and page-specific completion paths restore the list to the top before the next loop.

**Tech Stack:** MaaFramework JSON Pipeline, TemplateMatch, OCR, DirectHit, Python standard-library unittest, existing JSON Schema validator.

## Global Constraints

- Use the existing 1280×720 coordinate system and Win32 controller from assets/interface.json.
- Do not modify assets/resource/pipeline/alchemy.json or its existing task entry.
- Search the starting screen plus at most three down-search swipes, then end normally.
- Click MAX, then 确定, then 回收 only after the preceding recognizer succeeds.
- Use assets/resource/image/recycle/chicken_leg.png with green_mask: true, and exclude card borders and item counts.
- Validate with: python tools/validate_schema.py --schema-dir deps/tools --resource-dirs assets/resource --interface-files assets/interface.json

---

### Task 1: Add the failing Pipeline contract test

**Files:**
- Create: tests/test_recycle_pipeline.py
- Read: assets/interface.json
- Read: assets/resource/pipeline/recycle.json
- Read: assets/resource/image/recycle/chicken_leg.png

**Interfaces:**
- Consumes: a task named 回收小鸡腿, its Recycle.OpenBin entry, and the chicken-leg asset.
- Produces: a standard-library regression test for task exposure, bounded search, selection chain, and PNG presence.

- [ ] **Step 1: Write the failing test**

Create tests/test_recycle_pipeline.py:

~~~python
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "assets" / "interface.json"
PIPELINE = ROOT / "assets" / "resource" / "pipeline" / "recycle.json"
TEMPLATE = ROOT / "assets" / "resource" / "image" / "recycle" / "chicken_leg.png"


class RecyclePipelineTests(unittest.TestCase):
    def load_pipeline(self):
        return json.loads(PIPELINE.read_text(encoding="utf-8"))

    def test_interface_exposes_the_recycle_task(self):
        interface = json.loads(INTERFACE.read_text(encoding="utf-8"))
        task = next(task for task in interface["task"] if task["name"] == "回收小鸡腿")
        self.assertEqual(task["entry"], "Recycle.OpenBin")
        self.assertFalse(task["default_check"])

    def test_search_is_bounded_to_initial_page_plus_three_swipes(self):
        pipeline = self.load_pipeline()
        self.assertEqual(
            pipeline["Recycle.SearchTop"]["next"],
            ["Recycle.FindPage1", "Recycle.ScrollDown1"],
        )
        self.assertEqual(
            pipeline["Recycle.ScrollDown1"]["next"],
            ["Recycle.FindPage2", "Recycle.ScrollDown2"],
        )
        self.assertEqual(
            pipeline["Recycle.ScrollDown2"]["next"],
            ["Recycle.FindPage3", "Recycle.ScrollDown3"],
        )
        self.assertEqual(
            pipeline["Recycle.ScrollDown3"]["next"],
            ["Recycle.FindPage4", "Recycle.NormalEndNoChicken"],
        )
        self.assertIn(
            "已完成三次下滑搜索",
            pipeline["Recycle.NormalEndNoChicken"]["focus"]["succeeded"],
        )

    def test_every_page_selects_max_confirms_and_recycles(self):
        pipeline = self.load_pipeline()
        for page in range(1, 5):
            find = pipeline[f"Recycle.FindPage{page}"]
            self.assertEqual(find["recognition"], "TemplateMatch")
            self.assertEqual(find["template"], "recycle/chicken_leg.png")
            self.assertTrue(find["green_mask"])
            self.assertEqual(find["next"], [f"Recycle.WaitQuantityPage{page}"])
            self.assertEqual(
                pipeline[f"Recycle.SelectMaxPage{page}"]["target"], [812, 325]
            )
            self.assertEqual(
                pipeline[f"Recycle.ConfirmQuantityPage{page}"]["next"],
                [f"Recycle.VerifySelectedPage{page}"],
            )
            self.assertEqual(
                pipeline[f"Recycle.ClickRecyclePage{page}"]["next"],
                [f"Recycle.WaitRewardPage{page}"],
            )

    def test_chicken_leg_template_is_a_nonempty_png(self):
        content = TEMPLATE.read_bytes()
        self.assertGreater(len(content), 8)
        self.assertEqual(content[:8], bytes.fromhex("89504e470d0a1a0a"))


if __name__ == "__main__":
    unittest.main()
~~~

- [ ] **Step 2: Run the test to verify it fails**

Run:

~~~powershell
python -m unittest discover -s tests -p "test_recycle_pipeline.py" -v
~~~

Expected: failure because the new Pipeline, task entry, and template do not yet exist.

### Task 2: Create the green-mask template and recycle Pipeline

**Files:**
- Create: assets/resource/image/recycle/chicken_leg.png
- Create: assets/resource/pipeline/recycle.json
- Modify: assets/interface.json

**Interfaces:**
- Consumes: D:/飘流幻境新世界/pln-recode/tools/item-icons/output/icons/s1008.png, the catalog-confirmed icon for item_id 41090 (小鸡腿).
- Produces: Recycle.OpenBin and all downstream Recycle.* nodes, surfaced through the optional 回收小鸡腿 task.

- [ ] **Step 1: Create the green-mask recognition asset**

Load the official transparent source icon D:/飘流幻境新世界/pln-recode/tools/item-icons/output/icons/s1008.png, resize it to 71×70 with Lanczos filtering, paste its alpha channel onto a #00ff00 RGB background, then crop to 71×55. Save it at assets/resource/image/recycle/chicken_leg.png and compare it visually with assets/resource/image/alchemy/steamed_bun.png before use.

The asset must meet this exact contract:

~~~text
path: assets/resource/image/recycle/chicken_leg.png
PNG signature: 89 50 4E 47 0D 0A 1A 0A
background: #00ff00
foreground: one orange chicken-leg icon only
~~~

- [ ] **Step 2: Add the common page-open and bounded search nodes**

Create assets/resource/pipeline/recycle.json with these nodes. Candidate order in each next array is intentional: MaaFramework tries the item node first, and proceeds to the next swipe/end node only when it cannot select a chicken leg.

~~~json
{
    "Recycle.OpenBin": {
        "recognition": "DirectHit",
        "action": "Click",
        "target": [450, 340],
        "post_delay": 600,
        "next": ["Recycle.EnsurePage"]
    },
    "Recycle.EnsurePage": {
        "recognition": "OCR",
        "roi": [55, 55, 250, 80],
        "expected": ["资源回收桶"],
        "action": "DoNothing",
        "focus": {
            "succeeded": "已确认资源回收桶页面"
        },
        "next": ["Recycle.SearchTop"]
    },
    "Recycle.SearchTop": {
        "recognition": "DirectHit",
        "action": "DoNothing",
        "next": ["Recycle.FindPage1", "Recycle.ScrollDown1"]
    },
    "Recycle.FindPage1": {
        "recognition": "TemplateMatch",
        "roi": [670, 170, 470, 430],
        "template": "recycle/chicken_leg.png",
        "threshold": 0.78,
        "method": 10001,
        "green_mask": true,
        "order_by": "Vertical",
        "index": 0,
        "action": "Click",
        "post_delay": 500,
        "next": ["Recycle.WaitQuantityPage1"]
    },
    "Recycle.ScrollDown1": {
        "recognition": "DirectHit",
        "action": "Swipe",
        "begin": [880, 570],
        "end": [880, 330],
        "duration": 500,
        "end_hold": 100,
        "post_delay": 800,
        "next": ["Recycle.FindPage2", "Recycle.ScrollDown2"]
    },
    "Recycle.FindPage2": {
        "recognition": "TemplateMatch",
        "roi": [670, 170, 470, 430],
        "template": "recycle/chicken_leg.png",
        "threshold": 0.78,
        "method": 10001,
        "green_mask": true,
        "order_by": "Vertical",
        "index": 0,
        "action": "Click",
        "post_delay": 500,
        "next": ["Recycle.WaitQuantityPage2"]
    },
    "Recycle.ScrollDown2": {
        "recognition": "DirectHit",
        "action": "Swipe",
        "begin": [880, 570],
        "end": [880, 330],
        "duration": 500,
        "end_hold": 100,
        "post_delay": 800,
        "next": ["Recycle.FindPage3", "Recycle.ScrollDown3"]
    },
    "Recycle.FindPage3": {
        "recognition": "TemplateMatch",
        "roi": [670, 170, 470, 430],
        "template": "recycle/chicken_leg.png",
        "threshold": 0.78,
        "method": 10001,
        "green_mask": true,
        "order_by": "Vertical",
        "index": 0,
        "action": "Click",
        "post_delay": 500,
        "next": ["Recycle.WaitQuantityPage3"]
    },
    "Recycle.ScrollDown3": {
        "recognition": "DirectHit",
        "action": "Swipe",
        "begin": [880, 570],
        "end": [880, 330],
        "duration": 500,
        "end_hold": 100,
        "post_delay": 800,
        "next": ["Recycle.FindPage4", "Recycle.NormalEndNoChicken"]
    },
    "Recycle.FindPage4": {
        "recognition": "TemplateMatch",
        "roi": [670, 170, 470, 430],
        "template": "recycle/chicken_leg.png",
        "threshold": 0.78,
        "method": 10001,
        "green_mask": true,
        "order_by": "Vertical",
        "index": 0,
        "action": "Click",
        "post_delay": 500,
        "next": ["Recycle.WaitQuantityPage4"]
    },
    "Recycle.NormalEndNoChicken": {
        "recognition": "DirectHit",
        "action": "DoNothing",
        "focus": {
            "succeeded": "已完成三次下滑搜索，未找到小鸡腿，任务正常结束"
        }
    }
}
~~~

- [ ] **Step 3: Add the four complete select-MAX-confirm-recycle chains**

Add these complete page-one nodes:

~~~json
"Recycle.WaitQuantityPage1": {
    "recognition": "OCR",
    "roi": [350, 80, 580, 560],
    "expected": ["输入数量"],
    "action": "DoNothing",
    "next": ["Recycle.SelectMaxPage1"]
},
"Recycle.SelectMaxPage1": {
    "recognition": "DirectHit",
    "action": "Click",
    "target": [812, 325],
    "post_delay": 300,
    "next": ["Recycle.ConfirmQuantityPage1"]
},
"Recycle.ConfirmQuantityPage1": {
    "recognition": "OCR",
    "roi": [500, 485, 280, 120],
    "expected": ["确定"],
    "action": "Click",
    "post_delay": 600,
    "next": ["Recycle.VerifySelectedPage1"]
},
"Recycle.VerifySelectedPage1": {
    "recognition": "TemplateMatch",
    "roi": [320, 280, 150, 150],
    "template": "recycle/chicken_leg.png",
    "threshold": 0.78,
    "method": 10001,
    "green_mask": true,
    "action": "DoNothing",
    "next": ["Recycle.ClickRecyclePage1"]
},
"Recycle.ClickRecyclePage1": {
    "recognition": "OCR",
    "roi": [960, 570, 250, 120],
    "expected": ["回收"],
    "action": "Click",
    "post_delay": 800,
    "next": ["Recycle.WaitRewardPage1"]
},
"Recycle.WaitRewardPage1": {
    "recognition": "OCR",
    "roi": [350, 260, 600, 180],
    "expected": ["获得"],
    "action": "DoNothing",
    "next": ["Recycle.DismissRewardPage1"]
},
"Recycle.DismissRewardPage1": {
    "recognition": "DirectHit",
    "action": "Click",
    "target": [200, 430],
    "pre_delay": 300,
    "post_delay": 600,
    "next": ["Recycle.SearchTop"]
}
~~~

Add these complete page-two nodes:

~~~json
"Recycle.WaitQuantityPage2": {
    "recognition": "OCR",
    "roi": [350, 80, 580, 560],
    "expected": ["输入数量"],
    "action": "DoNothing",
    "next": ["Recycle.SelectMaxPage2"]
},
"Recycle.SelectMaxPage2": {
    "recognition": "DirectHit",
    "action": "Click",
    "target": [812, 325],
    "post_delay": 300,
    "next": ["Recycle.ConfirmQuantityPage2"]
},
"Recycle.ConfirmQuantityPage2": {
    "recognition": "OCR",
    "roi": [500, 485, 280, 120],
    "expected": ["确定"],
    "action": "Click",
    "post_delay": 600,
    "next": ["Recycle.VerifySelectedPage2"]
},
"Recycle.VerifySelectedPage2": {
    "recognition": "TemplateMatch",
    "roi": [320, 280, 150, 150],
    "template": "recycle/chicken_leg.png",
    "threshold": 0.78,
    "method": 10001,
    "green_mask": true,
    "action": "DoNothing",
    "next": ["Recycle.ClickRecyclePage2"]
},
"Recycle.ClickRecyclePage2": {
    "recognition": "OCR",
    "roi": [960, 570, 250, 120],
    "expected": ["回收"],
    "action": "Click",
    "post_delay": 800,
    "next": ["Recycle.WaitRewardPage2"]
},
"Recycle.WaitRewardPage2": {
    "recognition": "OCR",
    "roi": [350, 260, 600, 180],
    "expected": ["获得"],
    "action": "DoNothing",
    "next": ["Recycle.DismissRewardPage2"]
},
"Recycle.DismissRewardPage2": {
    "recognition": "DirectHit",
    "action": "Click",
    "target": [200, 430],
    "pre_delay": 300,
    "post_delay": 600,
    "next": ["Recycle.RestoreTopFromPage2"]
}
~~~

Add these complete page-three nodes:

~~~json
"Recycle.WaitQuantityPage3": {
    "recognition": "OCR",
    "roi": [350, 80, 580, 560],
    "expected": ["输入数量"],
    "action": "DoNothing",
    "next": ["Recycle.SelectMaxPage3"]
},
"Recycle.SelectMaxPage3": {
    "recognition": "DirectHit",
    "action": "Click",
    "target": [812, 325],
    "post_delay": 300,
    "next": ["Recycle.ConfirmQuantityPage3"]
},
"Recycle.ConfirmQuantityPage3": {
    "recognition": "OCR",
    "roi": [500, 485, 280, 120],
    "expected": ["确定"],
    "action": "Click",
    "post_delay": 600,
    "next": ["Recycle.VerifySelectedPage3"]
},
"Recycle.VerifySelectedPage3": {
    "recognition": "TemplateMatch",
    "roi": [320, 280, 150, 150],
    "template": "recycle/chicken_leg.png",
    "threshold": 0.78,
    "method": 10001,
    "green_mask": true,
    "action": "DoNothing",
    "next": ["Recycle.ClickRecyclePage3"]
},
"Recycle.ClickRecyclePage3": {
    "recognition": "OCR",
    "roi": [960, 570, 250, 120],
    "expected": ["回收"],
    "action": "Click",
    "post_delay": 800,
    "next": ["Recycle.WaitRewardPage3"]
},
"Recycle.WaitRewardPage3": {
    "recognition": "OCR",
    "roi": [350, 260, 600, 180],
    "expected": ["获得"],
    "action": "DoNothing",
    "next": ["Recycle.DismissRewardPage3"]
},
"Recycle.DismissRewardPage3": {
    "recognition": "DirectHit",
    "action": "Click",
    "target": [200, 430],
    "pre_delay": 300,
    "post_delay": 600,
    "next": ["Recycle.RestoreTopFromPage3Step1"]
}
~~~

Add these complete page-four nodes:

~~~json
"Recycle.WaitQuantityPage4": {
    "recognition": "OCR",
    "roi": [350, 80, 580, 560],
    "expected": ["输入数量"],
    "action": "DoNothing",
    "next": ["Recycle.SelectMaxPage4"]
},
"Recycle.SelectMaxPage4": {
    "recognition": "DirectHit",
    "action": "Click",
    "target": [812, 325],
    "post_delay": 300,
    "next": ["Recycle.ConfirmQuantityPage4"]
},
"Recycle.ConfirmQuantityPage4": {
    "recognition": "OCR",
    "roi": [500, 485, 280, 120],
    "expected": ["确定"],
    "action": "Click",
    "post_delay": 600,
    "next": ["Recycle.VerifySelectedPage4"]
},
"Recycle.VerifySelectedPage4": {
    "recognition": "TemplateMatch",
    "roi": [320, 280, 150, 150],
    "template": "recycle/chicken_leg.png",
    "threshold": 0.78,
    "method": 10001,
    "green_mask": true,
    "action": "DoNothing",
    "next": ["Recycle.ClickRecyclePage4"]
},
"Recycle.ClickRecyclePage4": {
    "recognition": "OCR",
    "roi": [960, 570, 250, 120],
    "expected": ["回收"],
    "action": "Click",
    "post_delay": 800,
    "next": ["Recycle.WaitRewardPage4"]
},
"Recycle.WaitRewardPage4": {
    "recognition": "OCR",
    "roi": [350, 260, 600, 180],
    "expected": ["获得"],
    "action": "DoNothing",
    "next": ["Recycle.DismissRewardPage4"]
},
"Recycle.DismissRewardPage4": {
    "recognition": "DirectHit",
    "action": "Click",
    "target": [200, 430],
    "pre_delay": 300,
    "post_delay": 600,
    "next": ["Recycle.RestoreTopFromPage4Step1"]
}
~~~

Add the six restore nodes below. They perform the exact number of reverse swipes needed for the page on which the chicken leg was found.

~~~json
"Recycle.RestoreTopFromPage2": {
    "recognition": "DirectHit",
    "action": "Swipe",
    "begin": [880, 330],
    "end": [880, 570],
    "duration": 500,
    "end_hold": 100,
    "post_delay": 800,
    "next": ["Recycle.SearchTop"]
},
"Recycle.RestoreTopFromPage3Step1": {
    "recognition": "DirectHit",
    "action": "Swipe",
    "begin": [880, 330],
    "end": [880, 570],
    "duration": 500,
    "end_hold": 100,
    "post_delay": 800,
    "next": ["Recycle.RestoreTopFromPage3Step2"]
},
"Recycle.RestoreTopFromPage3Step2": {
    "recognition": "DirectHit",
    "action": "Swipe",
    "begin": [880, 330],
    "end": [880, 570],
    "duration": 500,
    "end_hold": 100,
    "post_delay": 800,
    "next": ["Recycle.SearchTop"]
},
"Recycle.RestoreTopFromPage4Step1": {
    "recognition": "DirectHit",
    "action": "Swipe",
    "begin": [880, 330],
    "end": [880, 570],
    "duration": 500,
    "end_hold": 100,
    "post_delay": 800,
    "next": ["Recycle.RestoreTopFromPage4Step2"]
},
"Recycle.RestoreTopFromPage4Step2": {
    "recognition": "DirectHit",
    "action": "Swipe",
    "begin": [880, 330],
    "end": [880, 570],
    "duration": 500,
    "end_hold": 100,
    "post_delay": 800,
    "next": ["Recycle.RestoreTopFromPage4Step3"]
},
"Recycle.RestoreTopFromPage4Step3": {
    "recognition": "DirectHit",
    "action": "Swipe",
    "begin": [880, 330],
    "end": [880, 570],
    "duration": 500,
    "end_hold": 100,
    "post_delay": 800,
    "next": ["Recycle.SearchTop"]
}
~~~

- [ ] **Step 4: Expose the optional task**

Append this object to the task array in assets/interface.json. Do not alter the existing task object.

~~~json
{
    "name": "回收小鸡腿",
    "entry": "Recycle.OpenBin",
    "default_check": false,
    "description": "自动打开资源回收桶，最多下滑三次回收所有小鸡腿；找不到时正常结束"
}
~~~

- [ ] **Step 5: Run the contract test**

Run:

~~~powershell
python -m unittest discover -s tests -p "test_recycle_pipeline.py" -v
~~~

Expected: all four RecyclePipelineTests pass.

### Task 3: Validate schema and preserve existing behavior

**Files:**
- Verify: assets/resource/pipeline/recycle.json
- Verify: assets/interface.json
- Verify unchanged: assets/resource/pipeline/alchemy.json
- Verify: tests/test_recycle_pipeline.py

**Interfaces:**
- Consumes: the completed Pipeline, asset, interface entry, and tests.
- Produces: schema-valid resources and a narrow reviewed feature diff.

- [ ] **Step 1: Validate all project resource JSON**

Run:

~~~powershell
python tools/validate_schema.py --schema-dir deps/tools --resource-dirs assets/resource --interface-files assets/interface.json
~~~

Expected: every resource and interface file is listed with ✓, followed by All validations passed!.

- [ ] **Step 2: Inspect the narrow diff**

Run:

~~~powershell
git diff --check
git diff -- assets/interface.json assets/resource/pipeline/recycle.json assets/resource/image/recycle/chicken_leg.png tests/test_recycle_pipeline.py
git diff --exit-code -- assets/resource/pipeline/alchemy.json
~~~

Expected: no whitespace errors; no alchemy diff; only the task, template, test, and interface addition are present.

- [ ] **Step 3: Commit the feature**

Run:

~~~powershell
git add -- assets/interface.json assets/resource/pipeline/recycle.json assets/resource/image/recycle/chicken_leg.png tests/test_recycle_pipeline.py
git commit -m "feat: add chicken leg recycle task"
~~~

Expected: one focused feature commit.
