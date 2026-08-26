import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "assets" / "interface.json"
PIPELINE = ROOT / "assets" / "resource" / "pipeline" / "recycle.json"
TEMPLATE = ROOT / "assets" / "resource" / "image" / "recycle" / "chicken_leg.png"
SELECTED_TEMPLATE = (
    ROOT / "assets" / "resource" / "image" / "recycle" / "selected_chicken_leg.png"
)
BIN_TEMPLATE = ROOT / "assets" / "resource" / "image" / "recycle" / "recycle_bin.png"


def png_dimensions(path: Path) -> tuple[int, int]:
    content = path.read_bytes()
    if content[:8] != bytes.fromhex("89504e470d0a1a0a"):
        raise ValueError(f"{path} is not a PNG")
    return struct.unpack(">II", content[16:24])


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

    def test_successful_recycle_rechecks_the_current_page_before_swiping(self):
        pipeline = self.load_pipeline()
        self.assertEqual(
            pipeline["Recycle.DismissRewardPage1"]["next"], ["Recycle.SearchTop"]
        )
        for page in range(2, 5):
            search = pipeline[f"Recycle.SearchCurrentPage{page}"]
            self.assertEqual(
                pipeline[f"Recycle.DismissRewardPage{page}"]["next"],
                [f"Recycle.SearchCurrentPage{page}"],
            )
            self.assertEqual(search["recognition"], "DirectHit")
            self.assertEqual(search["action"], "DoNothing")
            self.assertEqual(search["next"][0], f"Recycle.FindPage{page}")
            self.assertEqual(
                search["next"][1],
                "Recycle.NormalEndNoChicken"
                if page == 4
                else f"Recycle.ScrollDown{page}",
            )
            self.assertNotIn(f"Recycle.RestoreTopFromPage{page}", pipeline)

    def test_open_bin_uses_template_matching_instead_of_a_fixed_coordinate(self):
        pipeline = self.load_pipeline()
        open_bin = pipeline["Recycle.OpenBin"]
        self.assertEqual(open_bin["recognition"], "TemplateMatch")
        self.assertEqual(open_bin["template"], "recycle/recycle_bin.png")
        self.assertEqual(open_bin["roi"], [0, 60, 1280, 600])
        self.assertEqual(open_bin["threshold"], 0.90)
        self.assertTrue(open_bin["green_mask"])
        self.assertEqual(open_bin["action"], "Click")
        self.assertNotIn("target", open_bin)

    def test_every_page_selects_max_confirms_and_recycles(self):
        pipeline = self.load_pipeline()
        for page in range(1, 5):
            find = pipeline[f"Recycle.FindPage{page}"]
            self.assertEqual(find["recognition"], "TemplateMatch")
            self.assertEqual(find["template"], "recycle/chicken_leg.png")
            self.assertTrue(find["green_mask"])
            self.assertEqual(find["threshold"], 0.78)
            self.assertEqual(find["next"], [f"Recycle.WaitQuantityPage{page}"])
            self.assertEqual(
                pipeline[f"Recycle.SelectMaxPage{page}"]["target"], [812, 325]
            )
            self.assertEqual(
                pipeline[f"Recycle.ConfirmQuantityPage{page}"]["next"],
                [f"Recycle.VerifySelectedPage{page}"],
            )
            self.assertEqual(
                pipeline[f"Recycle.VerifySelectedPage{page}"]["template"],
                "recycle/selected_chicken_leg.png",
            )
            self.assertEqual(
                pipeline[f"Recycle.VerifySelectedPage{page}"]["threshold"], 0.95
            )
            self.assertEqual(
                pipeline[f"Recycle.ClickRecyclePage{page}"]["next"],
                [f"Recycle.ConfirmRecyclePage{page}"],
            )
            confirm_recycle = pipeline[f"Recycle.ConfirmRecyclePage{page}"]
            self.assertEqual(confirm_recycle["recognition"], "OCR")
            self.assertEqual(confirm_recycle["roi"], [620, 430, 260, 120])
            self.assertEqual(confirm_recycle["expected"], ["确定"])
            self.assertEqual(confirm_recycle["action"], "Click")
            self.assertEqual(
                confirm_recycle["next"], [f"Recycle.WaitRewardPage{page}"]
            )

    def test_recycle_templates_match_the_game_scale(self):
        self.assertEqual(png_dimensions(TEMPLATE), (50, 38))
        self.assertEqual(png_dimensions(SELECTED_TEMPLATE), (50, 38))
        self.assertEqual(png_dimensions(BIN_TEMPLATE), (70, 75))


if __name__ == "__main__":
    unittest.main()
