"""Pure game rules for Blueberry Smoothie Tycoon.

This module intentionally has no pygame dependency, which keeps saving and the
economy easy to test and makes future balancing straightforward.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import random
import time
from typing import Callable


SAVE_VERSION = 2
STARTING_PLOTS = 4
MAX_PLOTS = 12
LAND_BASE_COST = 10_000
LAND_COST_STEP = 2_500
CUSTOMER_QUEUE_SIZE = 6
GROW_SECONDS = 24.0
REGROW_SECONDS = 17.0
HARVEST_YIELD = 4
BAG_STACK_SIZE = 16
BAG_COLUMNS = 4
BAG_ROWS = 4
BAG_SLOT_COUNT = BAG_COLUMNS * BAG_ROWS
BAG_ITEM_KEYS = ("blueberries", "seeds", "honey", "milk", "ice")

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

BAG_ITEM_LABELS = {
    "blueberries": "블루베리",
    **ITEM_LABELS,
}

RAW_BERRY_PRICE = 3
# Kept as the familiar reference price for older code and save files. New
# customer orders use CustomerOrder.price, which rises with every ingredient.
SMOOTHIE_PRICE = 20
SMOOTHIE_BASE_PRICE = 8
ORDER_INGREDIENT_REWARDS = {
    "blueberries": 2,
    "honey": 4,
    "milk": 5,
    "ice": 2,
}


@dataclass(eq=True)
class CustomerOrder:
    """One customer's custom smoothie request."""

    blueberries: int = 3
    honey: int = 1
    milk: int = 1
    ice: int = 1

    @classmethod
    def random(cls, rng: random.Random | None = None) -> "CustomerOrder":
        picker = rng if rng is not None else random
        return cls(
            blueberries=3,
            honey=picker.randint(0, 2),
            milk=picker.randint(1, 2),
            ice=picker.randint(1, 3),
        )

    @classmethod
    def from_dict(cls, data: dict) -> "CustomerOrder":
        return cls(
            blueberries=3,
            honey=max(0, min(2, int(data.get("honey", 1)))),
            milk=max(1, min(2, int(data.get("milk", 1)))),
            ice=max(1, min(3, int(data.get("ice", 1)))),
        )

    @property
    def recipe(self) -> dict[str, int]:
        return {
            "blueberries": self.blueberries,
            "honey": self.honey,
            "milk": self.milk,
            "ice": self.ice,
        }

    @property
    def price(self) -> int:
        return SMOOTHIE_BASE_PRICE + sum(
            self.recipe[key] * reward
            for key, reward in ORDER_INGREDIENT_REWARDS.items()
        )

    def short_text(self) -> str:
        return f"블루베리 {self.blueberries} · 꿀 {self.honey} · 우유 {self.milk} · 얼음 {self.ice}"


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
    customers_waiting: int = CUSTOMER_QUEUE_SIZE
    customer_orders: list[CustomerOrder] = field(default_factory=list)
    prepared_order: CustomerOrder | None = None
    berries_sold: int = 0
    berries_harvested: int = 0
    land_purchased: int = 0
    started_at: float = field(default_factory=time.time)
    game_elapsed_seconds: float = 0.0
    player_x: float = 360.0
    player_y: float = 380.0
    tutorial_seen: bool = False

    @classmethod
    def new(cls, now: float | None = None) -> "GameState":
        """Create a friendly starting state with one bush ready to harvest."""
        current = time.time() if now is None else now
        state = cls(started_at=current)
        state.plots[0] = Plot(planted=True, ready_at=current, cycle_seconds=GROW_SECONDS)
        state.customer_orders = [
            CustomerOrder.random() for _ in range(CUSTOMER_QUEUE_SIZE)
        ]
        return state

    @property
    def land_cost(self) -> int:
        return LAND_BASE_COST + (self.active_plots - STARTING_PLOTS) * LAND_COST_STEP

    def inventory(self, key: str) -> int:
        return int(getattr(self, key))

    def bag_stacks(self) -> list[tuple[str, int]]:
        stacks: list[tuple[str, int]] = []
        for key in BAG_ITEM_KEYS:
            remaining = max(0, self.inventory(key))
            while remaining:
                amount = min(BAG_STACK_SIZE, remaining)
                stacks.append((key, amount))
                remaining -= amount
        return stacks

    @property
    def bag_slots_used(self) -> int:
        return len(self.bag_stacks())

    def can_add_to_bag(self, key: str, amount: int = 1) -> bool:
        if key not in BAG_ITEM_KEYS or amount <= 0:
            return True
        current = max(0, self.inventory(key))
        current_stacks = (current + BAG_STACK_SIZE - 1) // BAG_STACK_SIZE
        future_stacks = (current + amount + BAG_STACK_SIZE - 1) // BAG_STACK_SIZE
        return self.bag_slots_used + future_stacks - current_stacks <= BAG_SLOT_COUNT

    def _sync_customer_orders(self) -> None:
        self.customers_waiting = max(
            0, min(CUSTOMER_QUEUE_SIZE, int(self.customers_waiting))
        )
        self.customer_orders = self.customer_orders[:self.customers_waiting]
        while len(self.customer_orders) < self.customers_waiting:
            self.customer_orders.append(CustomerOrder.random())

    @property
    def current_order(self) -> CustomerOrder | None:
        self._sync_customer_orders()
        return self.customer_orders[0] if self.customer_orders else None

    def add_customer(
        self,
        order: CustomerOrder | None = None,
        *,
        rng: random.Random | None = None,
    ) -> bool:
        self._sync_customer_orders()
        if self.customers_waiting >= CUSTOMER_QUEUE_SIZE:
            return False
        self.customer_orders.append(order or CustomerOrder.random(rng))
        self.customers_waiting += 1
        return True

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
        if not self.can_add_to_bag("blueberries", HARVEST_YIELD):
            return False, "가방이 가득 차서 수확할 수 없어요. B를 눌러 가방을 확인하세요."
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
        if not self.can_add_to_bag(key, 1):
            return False, "가방 16칸이 모두 찼어요. 재료를 사용하거나 판매해 주세요."
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

    def make_smoothie(
        self,
        selected_recipe: dict[str, int] | None = None,
    ) -> tuple[bool, str]:
        order = self.current_order
        if order is None:
            return False, "지금은 주문한 손님이 없어요. 새 손님을 잠시 기다려 주세요."
        if self.prepared_order is not None:
            return False, "이미 만든 주문 스무디가 있어요. 맨 앞 손님에게 먼저 판매해 주세요."
        labels = {
            "blueberries": "블루베리",
            "honey": "꿀",
            "milk": "우유",
            "ice": "얼음",
        }
        recipe = order.recipe if selected_recipe is None else {
            key: max(0, int(selected_recipe.get(key, 0)))
            for key in order.recipe
        }
        differences: list[str] = []
        for key, ordered_amount in order.recipe.items():
            difference = recipe[key] - ordered_amount
            if difference < 0:
                differences.append(f"{labels[key]} {abs(difference)}개 더 넣기")
            elif difference > 0:
                differences.append(f"{labels[key]} {difference}개 빼기")
        if differences:
            return False, "주문과 달라요: " + ", ".join(differences)

        missing: list[str] = []
        for key, amount in recipe.items():
            if self.inventory(key) < amount:
                missing.append(f"{labels[key]} {amount - self.inventory(key)}")
        if missing:
            return False, "재료가 부족해요: " + ", ".join(missing)
        for key, amount in recipe.items():
            setattr(self, key, self.inventory(key) - amount)
        self.smoothies += 1
        self.prepared_order = CustomerOrder(**order.recipe)
        return True, f"주문대로 스무디 완성! 판매하면 {order.price}코인을 받아요."

    def sell_smoothie(self) -> tuple[bool, str]:
        order = self.current_order
        if order is None:
            return False, "지금은 기다리는 손님이 없어요. 새 손님을 잠시 기다려 주세요."
        if self.smoothies < 1:
            return False, "판매할 주문 스무디가 없어요. 블렌더에서 먼저 만들어 주세요."
        if self.prepared_order is not None and self.prepared_order != order:
            return False, "이 스무디는 다른 주문이에요. 맨 앞 손님의 주문을 다시 확인해 주세요."
        self.smoothies -= 1
        self.customers_waiting -= 1
        self.customer_orders.pop(0)
        self.money += order.price
        self.smoothies_sold += 1
        self.prepared_order = None
        return True, f"주문 스무디 판매 성공! 재료만큼 {order.price}코인을 벌었어요."

    def buy_land(self) -> tuple[bool, str]:
        if self.active_plots >= MAX_PLOTS:
            return False, "농장을 최대로 넓혔어요!"
        cost = self.land_cost
        if self.money < cost:
            return False, f"텃밭을 사려면 {cost:,}코인이 필요해요."
        self.money -= cost
        self.active_plots += 1
        self.land_purchased += 1
        return True, f"새 텃밭을 샀어요! 이제 밭이 {self.active_plots}칸이에요."

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
            save_version = int(raw.get("save_version", 1))
            if save_version not in (1, SAVE_VERSION):
                raise ValueError("지원하지 않는 저장 파일 버전입니다.")
            plot_data = raw.pop("plots")
            order_data = raw.pop("customer_orders", [])
            prepared_order_data = raw.pop("prepared_order", None)
            raw.pop("save_version", None)
            allowed = {field_name for field_name in cls.__dataclass_fields__}
            state = cls(**{key: value for key, value in raw.items() if key in allowed})
            state.active_plots = max(STARTING_PLOTS, min(MAX_PLOTS, int(state.active_plots)))
            state.game_elapsed_seconds = max(0.0, float(state.game_elapsed_seconds))
            state.customers_waiting = max(
                0, min(CUSTOMER_QUEUE_SIZE, int(state.customers_waiting))
            )
            state.customer_orders = [
                CustomerOrder.from_dict(item)
                for item in order_data[:state.customers_waiting]
                if isinstance(item, dict)
            ]
            if isinstance(prepared_order_data, dict):
                state.prepared_order = CustomerOrder.from_dict(prepared_order_data)
            else:
                # Version 1 smoothies were generic. Preserve them as legacy
                # stock that can be served without discarding player progress.
                state.prepared_order = None
            state._sync_customer_orders()
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
