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
