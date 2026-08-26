import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "assets" / "interface.json"


class InterfaceControllerTests(unittest.TestCase):
    def load_interface(self):
        return json.loads(INTERFACE.read_text(encoding="utf-8"))

    def test_ldplayer_adb_controller_is_listed_first_at_720p(self):
        interface = self.load_interface()

        controller_names = [c["name"] for c in interface["controller"]]
        self.assertIn("雷电模拟器（ADB）", controller_names)
        self.assertIn("雷电模拟器 14（ADB）", controller_names)
        self.assertIn("雷电模拟器 9（ADB）", controller_names)

    def test_existing_win32_controller_remains_available(self):
        interface = self.load_interface()
        win32 = next(
            controller
            for controller in interface["controller"]
            if controller["name"] == "Win32"
        )

        self.assertEqual(win32["type"], "Win32")
        self.assertEqual(win32["display_short_side"], 720)
        self.assertEqual(win32["win32"]["screencap"], "FramePool")
        self.assertEqual(win32["win32"]["mouse"], "Seize")

    def test_existing_tasks_are_available_to_both_controllers(self):
        interface = self.load_interface()

        self.assertEqual(
            {task["name"] for task in interface["task"]},
            {"连续炼金", "回收小鸡腿", "玩家对战"},
        )
        for task in interface["task"]:
            self.assertNotIn("controller", task)


if __name__ == "__main__":
    unittest.main()
