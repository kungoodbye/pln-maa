import time
from pathlib import Path
import tempfile
import json
import unittest

from agent.arena_stats import ArenaStatsTracker, ArenaStatistics


class TestArenaStats(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tracker = ArenaStatsTracker(log_dir=Path(self.temp_dir.name))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_battle_flow_and_stats(self):
        # 1. Start battle 1
        self.tracker.on_battle_start()
        time.sleep(0.1)
        dur1 = self.tracker.on_battle_end(result="success")
        self.assertGreater(dur1, 0.05)
        self.assertEqual(self.tracker.stats.total_rounds, 1)
        self.assertEqual(self.tracker.stats.success_rounds, 1)

        # 2. Buy vitality
        self.tracker.on_buy_vitality()
        self.assertEqual(self.tracker.stats.vitality_bought_count, 1)
        self.assertEqual(self.tracker.stats.diamonds_spent, 5)

        # 3. Start battle 2 with timeout
        self.tracker.on_battle_start()
        time.sleep(0.05)
        dur2 = self.tracker.on_battle_end(result="timeout")
        self.assertEqual(self.tracker.stats.total_rounds, 2)
        self.assertEqual(self.tracker.stats.timeout_rounds, 1)

        # 4. Check generated files
        report_txt = Path(self.temp_dir.name) / "arena_battle_report.txt"
        report_json = Path(self.temp_dir.name) / "arena_stats.json"

        self.assertTrue(report_txt.exists())
        self.assertTrue(report_json.exists())

        txt_content = report_txt.read_text(encoding="utf-8")
        self.assertIn("累计对战总场次: 2 场", txt_content)
        self.assertIn("累计消耗绿钻: 5 钻", txt_content)

        data = json.loads(report_json.read_text(encoding="utf-8"))
        self.assertEqual(data["total_rounds"], 2)
        self.assertEqual(data["vitality_bought_count"], 1)


if __name__ == "__main__":
    unittest.main()
