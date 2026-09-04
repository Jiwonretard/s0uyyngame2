"""Pure game rules for Blueberry Smoothie Tycoon.

This module intentionally has no pygame dependency, which keeps saving and the
economy easy to test and makes future balancing straightforward.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import time
from typing import Callable


SAVE_VERSION = 1
STARTING_PLOTS = 4
MAX_PLOTS = 12
GROW_SECONDS = 24.0
REGROW_SECONDS = 17.0
HARVEST_YIELD = 4

ITEM_COSTS = {
    "seeds": 6,
    "honey": 2,
    "milk": 3,
    "ice": 1,
}

ITEM_LABELS = {
    "seeds": "씨앗",
    "honey": "꿀",
    "milk": "우유",
    "ice": "얼음",
}

SMOOTHIE_RECIPE = {
    "blueberries": 3,
    "honey": 1,
    "milk": 1,
    "ice": 1,
}

RAW_BERRY_PRICE = 3
SMOOTHIE_PRICE = 20


@dataclass
class Plot:
    planted: bool = False
    ready_at: float = 0.0
    cycle_seconds: float = GROW_SECONDS

    def is_ready(self, now: float) -> bool:
        return self.planted and now >= self.ready_at

    def remaining(self, now: float) -> float:
        if not self.planted:
            return 0.0
        return max(0.0, self.ready_at - now)

    def progress(self, now: float) -> float:
        if not self.planted or self.cycle_seconds <= 0:
            return 0.0
        return min(1.0, max(0.0, 1.0 - self.remaining(now) / self.cycle_seconds))


@dataclass
class GameState:
    money: int = 36
    blueberries: int = 0
    seeds: int = 3
    honey: int = 0
    milk: int = 0
    ice: int = 0
    smoothies: int = 0
    active_plots: int = STARTING_PLOTS
    plots: list[Plot] = field(default_factory=lambda: [Plot() for _ in range(MAX_PLOTS)])
    smoothies_sold: int = 0
    berries_sold: int = 0
    berries_harvested: int = 0
    land_purchased: int = 0
    started_at: float = field(default_factory=time.time)
    player_x: float = 360.0
    player_y: float = 380.0
    tutorial_seen: bool = False

    @classmethod
    def new(cls, now: float | None = None) -> "GameState":
        """Create a friendly starting state with one bush ready to harvest."""
        current = time.time() if now is None else now
        state = cls(started_at=current)
        state.plots[0] = Plot(planted=True, ready_at=current, cycle_seconds=GROW_SECONDS)
        return state

    @property
    def land_cost(self) -> int:
        return 45 + (self.active_plots - STARTING_PLOTS) * 25

    def inventory(self, key: str) -> int:
        return int(getattr(self, key))

    def plant(self, plot_index: int, now: float | None = None) -> tuple[bool, str]:
        current = time.time() if now is None else now
        if not 0 <= plot_index < self.active_plots:
            return False, "아직 잠긴 땅이에요. 먼저 땅을 늘려 주세요."
        plot = self.plots[plot_index]
        if plot.planted:
            if plot.is_ready(current):
                return False, "열매가 익었어요! 다시 눌러 수확해 주세요."
            return False, f"블루베리가 자라는 중이에요. {int(plot.remaining(current)) + 1}초 남았어요."
        if self.seeds < 1:
            return False, "씨앗이 없어요. 가게에서 씨앗을 사 주세요."
        self.seeds -= 1
        self.plots[plot_index] = Plot(
            planted=True,
            ready_at=current + GROW_SECONDS,
            cycle_seconds=GROW_SECONDS,
        )
        return True, "블루베리 씨앗을 심었어요!"

    def harvest(self, plot_index: int, now: float | None = None) -> tuple[bool, str]:
        current = time.time() if now is None else now
        if not 0 <= plot_index < self.active_plots:
            return False, "아직 사용할 수 없는 땅이에요."
        plot = self.plots[plot_index]
        if not plot.planted:
            return False, "빈 밭이에요. 눌러서 씨앗을 심어 주세요."
        if not plot.is_ready(current):
            return False, f"조금만 기다려 주세요. {int(plot.remaining(current)) + 1}초 남았어요."
        self.blueberries += HARVEST_YIELD
        self.berries_harvested += HARVEST_YIELD
        self.plots[plot_index] = Plot(
            planted=True,
            ready_at=current + REGROW_SECONDS,
            cycle_seconds=REGROW_SECONDS,
        )
        return True, f"싱싱한 블루베리 {HARVEST_YIELD}개를 수확했어요!"

    def use_plot(self, plot_index: int, now: float | None = None) -> tuple[bool, str]:
        current = time.time() if now is None else now
        if not 0 <= plot_index < self.active_plots:
            return False, "아직 잠긴 땅이에요. 먼저 땅을 늘려 주세요."
        plot = self.plots[plot_index]
        if not plot.planted:
            return self.plant(plot_index, current)
        return self.harvest(plot_index, current)

    def buy_item(self, key: str) -> tuple[bool, str]:
        if key not in ITEM_COSTS:
            return False, "판매하지 않는 물건이에요."
        cost = ITEM_COSTS[key]
        if self.money < cost:
            return False, f"돈이 부족해요. {cost}코인이 필요해요."
        self.money -= cost
        setattr(self, key, self.inventory(key) + 1)
        return True, f"{ITEM_LABELS[key]} 1개를 샀어요."

    def sell_blueberry(self) -> tuple[bool, str]:
        if self.blueberries < 1:
            return False, "판매할 블루베리가 없어요."
        self.blueberries -= 1
        self.money += RAW_BERRY_PRICE
        self.berries_sold += 1
        return True, f"블루베리 1개를 팔아 {RAW_BERRY_PRICE}코인을 벌었어요."

    def make_smoothie(self) -> tuple[bool, str]:
        missing: list[str] = []
        labels = {
            "blueberries": "블루베리",
            "honey": "꿀",
            "milk": "우유",
            "ice": "얼음",
        }
        for key, amount in SMOOTHIE_RECIPE.items():
            if self.inventory(key) < amount:
                missing.append(f"{labels[key]} {amount - self.inventory(key)}")
        if missing:
            return False, "재료가 부족해요: " + ", ".join(missing)
        for key, amount in SMOOTHIE_RECIPE.items():
            setattr(self, key, self.inventory(key) - amount)
        self.smoothies += 1
        return True, "보랏빛 블루베리 스무디를 만들었어요!"

    def sell_smoothie(self) -> tuple[bool, str]:
        if self.smoothies < 1:
            return False, "판매할 스무디가 없어요. 먼저 만들어 주세요."
        self.smoothies -= 1
        self.money += SMOOTHIE_PRICE
        self.smoothies_sold += 1
        return True, f"스무디 1잔 판매! {SMOOTHIE_PRICE}코인을 벌었어요."

    def buy_land(self) -> tuple[bool, str]:
        if self.active_plots >= MAX_PLOTS:
            return False, "농장을 최대로 넓혔어요!"
        cost = self.land_cost
        if self.money < cost:
            return False, f"땅을 사려면 {cost}코인이 필요해요."
        self.money -= cost
        self.active_plots += 1
        self.land_purchased += 1
        return True, f"새 밭을 샀어요! 이제 밭이 {self.active_plots}칸이에요."

    def to_dict(self) -> dict:
        data = asdict(self)
        data["save_version"] = SAVE_VERSION
        return data

    def save(self, path: str | Path) -> None:
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = save_path.with_suffix(save_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(save_path)

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        now: float | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> "GameState":
        save_path = Path(path)
        current = time.time() if now is None else now
        if not save_path.exists():
            return cls.new(current)
        try:
            raw = json.loads(save_path.read_text(encoding="utf-8"))
            if raw.get("save_version") != SAVE_VERSION:
                raise ValueError("지원하지 않는 저장 파일 버전입니다.")
            plot_data = raw.pop("plots")
            raw.pop("save_version", None)
            allowed = {field_name for field_name in cls.__dataclass_fields__}
            state = cls(**{key: value for key, value in raw.items() if key in allowed})
            state.active_plots = max(STARTING_PLOTS, min(MAX_PLOTS, int(state.active_plots)))
            state.plots = []
            for item in plot_data[:MAX_PLOTS]:
                state.plots.append(
                    Plot(
                        planted=bool(item.get("planted", False)),
                        ready_at=float(item.get("ready_at", 0.0)),
                        cycle_seconds=max(0.1, float(item.get("cycle_seconds", GROW_SECONDS))),
                    )
                )
            while len(state.plots) < MAX_PLOTS:
                state.plots.append(Plot())
            return state
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            if on_error is not None:
                on_error(exc)
            return cls.new(current)
