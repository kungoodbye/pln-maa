import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    from maa.agent.agent_server import AgentServer
    from maa.context import Context
    from maa.custom_action import CustomAction
except ImportError:
    # Allow running standalone or in tests without maa-framework installed
    class AgentServer:
        @staticmethod
        def custom_action(name: str):
            def decorator(cls):
                return cls
            return decorator

    class CustomAction:
        class RunArg:
            pass

    class Context:
        pass


@dataclass
class BattleRecord:
    round_id: int
    start_time: float
    end_time: float
    duration_sec: float
    result: str = "success"


@dataclass
class ArenaStatistics:
    total_rounds: int = 0
    success_rounds: int = 0
    timeout_rounds: int = 0
    total_duration_sec: float = 0.0
    vitality_bought_count: int = 0
    diamonds_spent: int = 0
    start_timestamp: float = field(default_factory=time.time)
    records: List[BattleRecord] = field(default_factory=list)


class ArenaStatsTracker:
    _instance: Optional["ArenaStatsTracker"] = None

    def __init__(self, log_dir: Optional[Path] = None):
        self.stats = ArenaStatistics()
        self.current_battle_start: Optional[float] = None
        self.log_dir = log_dir or Path("./logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_instance(cls) -> "ArenaStatsTracker":
        if cls._instance is None:
            cls._instance = ArenaStatsTracker()
        return cls._instance

    def on_battle_start(self):
        self.current_battle_start = time.time()
        round_no = self.stats.total_rounds + 1
        print(f"\n[玩家对战] 第 {round_no} 场战斗开始，正在战斗中...")

    def on_battle_end(self, result: str = "success") -> float:
        now = time.time()
        start_t = self.current_battle_start or now
        duration = max(0.0, now - start_t)

        self.stats.total_rounds += 1
        if result == "success":
            self.stats.success_rounds += 1
        elif result == "timeout":
            self.stats.timeout_rounds += 1

        self.stats.total_duration_sec += duration
        record = BattleRecord(
            round_id=self.stats.total_rounds,
            start_time=start_t,
            end_time=now,
            duration_sec=round(duration, 1),
            result=result,
        )
        self.stats.records.append(record)
        self.current_battle_start = None

        # Print quick progress
        avg_dur = (
            self.stats.total_duration_sec / self.stats.total_rounds
            if self.stats.total_rounds > 0
            else 0.0
        )
        print(
            f"[玩家对战] 第 {self.stats.total_rounds} 场战斗结束！"
            f"本场耗时: {duration:.1f} 秒 | 累计平均耗时: {avg_dur:.1f} 秒"
        )
        self.save_report()
        return duration

    def on_buy_vitality(self):
        self.stats.vitality_bought_count += 1
        self.stats.diamonds_spent += 5
        print(
            f"[补充活力] 累计购买 {self.stats.vitality_bought_count} 次，"
            f"累计消耗绿钻: {self.stats.diamonds_spent} 钻"
        )
        self.save_report()

    def generate_report_text(self) -> str:
        s = self.stats
        total_time = max(1.0, time.time() - s.start_timestamp)
        avg_time = s.total_duration_sec / s.total_rounds if s.total_rounds > 0 else 0.0

        min_dur = min((r.duration_sec for r in s.records), default=0.0)
        max_dur = max((r.duration_sec for r in s.records), default=0.0)

        lines = [
            "=====================================================",
            "              飘流幻境新世界 - 玩家对战统计战报       ",
            "=====================================================",
            f"累计对战总场次: {s.total_rounds} 场 (完成: {s.success_rounds} 场, 超时: {s.timeout_rounds} 场)",
            f"单场平均战斗耗时: {avg_time:.1f} 秒",
            f"最快单场耗时: {min_dur:.1f} 秒 | 最慢单场耗时: {max_dur:.1f} 秒",
            f"活力购买次数: {s.vitality_bought_count} 次 (累计消耗绿钻: {s.diamonds_spent} 钻)",
            f"任务总运行耗时: {int(total_time // 60)} 分 {int(total_time % 60)} 秒",
            "=====================================================",
        ]
        return "\n".join(lines)

    def save_report(self):
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            # Text report
            report_txt = self.log_dir / "arena_battle_report.txt"
            report_txt.write_text(self.generate_report_text(), encoding="utf-8")

            # JSON structured stats
            report_json = self.log_dir / "arena_stats.json"
            data = asdict(self.stats)
            report_json.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            print(f"Warning: Failed to save arena report: {e}")


# MaaFramework Custom Actions
@AgentServer.custom_action("ArenaStats.OnBattleStart")
class ActionBattleStart(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        ArenaStatsTracker.get_instance().on_battle_start()
        return True


@AgentServer.custom_action("ArenaStats.OnBattleEnd")
class ActionBattleEnd(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        ArenaStatsTracker.get_instance().on_battle_end(result="success")
        return True


@AgentServer.custom_action("ArenaStats.OnBattleTimeout")
class ActionBattleTimeout(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        ArenaStatsTracker.get_instance().on_battle_end(result="timeout")
        return True


@AgentServer.custom_action("ArenaStats.OnBuyVitality")
class ActionBuyVitality(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        ArenaStatsTracker.get_instance().on_buy_vitality()
        return True
