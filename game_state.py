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


SAVE_VERSION = 5
LEGACY_GAME_DAY_SECONDS = 720.0
GAME_DAY_SECONDS = 24.0 * 60.0
STARTING_PLOTS = 4
MAX_PLOTS = 12
LAND_BASE_COST = 10_000
LAND_COST_STEP = 2_500
CUSTOMER_QUEUE_SIZE = 6
GROW_SECONDS = 60.0
REGROW_SECONDS = 60.0
HARVEST_YIELD = 4
BAG_STACK_SIZE = 16
BAG_COLUMNS = 4
BAG_ROWS = 4
BAG_SLOT_COUNT = BAG_COLUMNS * BAG_ROWS
BAG_ITEM_KEYS = (
    "blueberries",
    "organic_blueberries",
    "seeds",
    "fertilizer",
    "honey",
    "milk",
    "ice",
    "golden_blueberries",
    "premium_honey",
    "low_fat_milk",
    "fishing_rod",
    "carp",
    "crucian_carp",
    "bass",
    "turtle",
)

DAYS_PER_SEASON = 7
SEASONS = ("봄", "여름", "가을", "겨울")
WEATHER_LABELS = {
    "sunny": "맑음",
    "rain": "비",
    "wind": "바람",
    "heat": "무더위",
    "snow": "눈",
}
REPUTATION_THRESHOLDS = (0, 8, 25, 55, 95)
MAX_FACILITY_LEVEL = 3
FACILITY_KEYS = ("beehive", "ice_maker", "cow_barn")
STREETLIGHT_COST = 3_000
STREETLIGHT_COUNT = 7
STREETLIGHT_LAYOUT_VERSION = 2
FACILITY_CONFIG = {
    "beehive": {
        "name": "벌통",
        "product": "honey",
        "product_name": "꿀",
        "cost": 2_000,
        "upgrade_costs": (0, 3_500, 6_000),
        "unlock_rank": 1,
        "yields": (0, 2, 3, 5),
    },
    "ice_maker": {
        "name": "제빙기",
        "product": "ice",
        "product_name": "얼음",
        "cost": 4_000,
        "upgrade_costs": (0, 7_000, 11_000),
        "unlock_rank": 2,
        "yields": (0, 4, 7, 10),
    },
    "cow_barn": {
        "name": "젖소 축사",
        "product": "milk",
        "product_name": "우유",
        "cost": 7_000,
        "upgrade_costs": (0, 12_000, 18_000),
        "unlock_rank": 3,
        "yields": (0, 2, 4, 6),
    },
}

CUSTOMER_NAME_DATA_PATH = (
    Path(__file__).resolve().parent / "assets" / "korean_customer_names.json"
)
FALLBACK_SURNAMES = ("김", "이", "박", "최", "정", "강", "조", "윤")
FALLBACK_GIVEN_NAMES = (
    "서준", "민준", "도윤", "시우", "주원", "지호", "서연", "지우",
    "하윤", "민서", "수빈", "유진", "민아", "하늘", "나리", "태오",
)
LEGACY_CUSTOMER_NAME_MAP = {
    "민아": "김민아",
    "하늘": "이하늘",
    "도윤": "박도윤",
    "수빈": "최수빈",
    "유진": "정유진",
    "지호": "강지호",
    "나리": "조나리",
    "태오": "윤태오",
}
VIP_TITLES = ("블루베리 연구가", "축제 심사위원", "유명 요리사", "마을 대표")
REGULAR_RETURN_CHANCE = 0.35
HONEY_FREE_ORDER_CHANCE = 0.15
HONEY_SINGLE_ORDER_CHANCE = 0.55
HONEY_DOUBLE_ORDER_START = 0.70
WINTER_SINGLE_HONEY_CHANCE = 0.65


def load_customer_names(path: Path = CUSTOMER_NAME_DATA_PATH) -> tuple[str, ...]:
    """Build fictional full names from the bundled Korean name component data."""
    surnames = FALLBACK_SURNAMES
    given_names = FALLBACK_GIVEN_NAMES
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        loaded_surnames = tuple(
            str(value).strip() for value in raw.get("surnames", []) if str(value).strip()
        )
        loaded_given_names = tuple(
            str(value).strip() for value in raw.get("given_names", []) if str(value).strip()
        )
        if loaded_surnames and loaded_given_names:
            surnames = loaded_surnames
            given_names = loaded_given_names
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        pass
    return tuple(dict.fromkeys(
        f"{surname}{given_name}"
        for surname in surnames
        for given_name in given_names
    ))


CUSTOMER_NAMES = load_customer_names()
CUSTOMER_STORIES = (
    "농장 산책 뒤 마시는 스무디가 최고예요.",
    "오늘은 달콤하고 시원하게 부탁해요!",
    "친구에게 이 가게를 추천받고 왔어요.",
    "싱싱한 블루베리 향을 기대하고 있어요.",
)
VIP_STORIES = (
    "마을 최고의 스무디를 심사하러 왔습니다.",
    "완벽한 배합이라면 특별 평판을 드리죠.",
    "축제에 소개할 한 잔을 만들어 주세요.",
)

ITEM_COSTS = {
    "seeds": 6,
    "fertilizer": 100,
    "honey": 2,
    "milk": 3,
    "ice": 1,
}

ITEM_LABELS = {
    "seeds": "씨앗",
    "fertilizer": "비료",
    "honey": "꿀",
    "milk": "우유",
    "ice": "얼음",
}

BAG_ITEM_LABELS = {
    "blueberries": "블루베리",
    "organic_blueberries": "유기농 블루베리",
    "golden_blueberries": "황금 블루베리",
    "premium_honey": "고급 꿀",
    "low_fat_milk": "저지방 우유",
    "fishing_rod": "낚싯대",
    "carp": "잉어",
    "crucian_carp": "붕어",
    "bass": "베스",
    "turtle": "거북이",
    **ITEM_LABELS,
}

RAW_BERRY_PRICE = 3
ORGANIC_BLUEBERRY_PRICE = 8
GOLDEN_BLUEBERRY_PRICE = 200
FISHING_ROD_COST = 2_000
FISHING_ROD_MAX_DURABILITY = 40
FISH_PRICES = {
    "carp": 80,
    "crucian_carp": 65,
    "bass": 120,
    "turtle": 250,
}
FISH_CATCH_TABLE = (
    (0.34, "carp"),
    (0.68, "crucian_carp"),
    (0.92, "bass"),
    (1.00, "turtle"),
)
FURNITURE_COSTS = {
    "bed": 3_000,
    "drawer": 500,
    "desk": 1_000,
    "lantern": 300,
    "flowerpot": 100,
}
FURNITURE_LABELS = {
    "bed": "침대",
    "drawer": "서랍",
    "desk": "책상",
    "lantern": "랜턴",
    "flowerpot": "화분",
}
FURNITURE_GRID_COLUMNS = 35
FURNITURE_GRID_ROWS = 10
FURNITURE_FOOTPRINTS = {
    "bed": (5, 3),
    "drawer": (2, 2),
    "desk": (4, 2),
    "lantern": (2, 2),
    "flowerpot": (2, 2),
}
DEFAULT_FURNITURE_LAYOUT = {
    "bed": [1, 5, 0],
    "drawer": [31, 5, 0],
    "desk": [14, 6, 0],
    "lantern": [28, 6, 0],
    "flowerpot": [10, 7, 0],
}
SPECIAL_SMOOTHIE_BONUS = 100
TREE_DROP_TABLE = (
    (0.20, "blueberries"),
    (0.40, "honey"),
    (0.60, "milk"),
    (0.80, "ice"),
    (0.85, "coins"),
    (0.93, "golden_blueberries"),
    (0.96, "premium_honey"),
    (0.99, "low_fat_milk"),
    (1.00, "seeds"),
)
# Kept as a reference price for older code and save files. New customer orders
# use CustomerOrder.price, which rises with every ingredient, then receive the
# global 20% sale-price increase below.
SMOOTHIE_PRICE = 24
SMOOTHIE_PRICE_MULTIPLIER = 1.20
SMOOTHIE_BASE_PRICE = 8
ORDER_INGREDIENT_REWARDS = {
    "blueberries": 2,
    "honey": 4,
    "milk": 5,
    "ice": 2,
}


def season_for_day(day: int) -> tuple[str, int, int]:
    safe_day = max(1, int(day))
    season_index = ((safe_day - 1) // DAYS_PER_SEASON) % len(SEASONS)
    day_in_season = (safe_day - 1) % DAYS_PER_SEASON + 1
    year = (safe_day - 1) // (DAYS_PER_SEASON * len(SEASONS)) + 1
    return SEASONS[season_index], day_in_season, year


def weather_for_day(day: int) -> str:
    season, day_in_season, _year = season_for_day(day)
    patterns = {
        "봄": ("sunny", "rain", "sunny", "wind", "rain", "sunny", "sunny"),
        "여름": ("sunny", "heat", "sunny", "rain", "heat", "sunny", "sunny"),
        "가을": ("wind", "sunny", "rain", "sunny", "wind", "sunny", "rain"),
        "겨울": ("snow", "sunny", "snow", "wind", "sunny", "snow", "sunny"),
    }
    return patterns[season][day_in_season - 1]


def is_blueberry_festival(day: int) -> bool:
    season, day_in_season, _year = season_for_day(day)
    return season == "여름" and day_in_season == DAYS_PER_SEASON


def honey_amount_for_roll(roll: float, day: int = 1) -> int:
    """Choose a honey amount while keeping honey-free orders uncommon."""
    normalized = max(0.0, min(0.999999, float(roll)))
    season, _day_in_season, _year = season_for_day(day)
    if season == "겨울":
        return 1 if normalized < WINTER_SINGLE_HONEY_CHANCE else 2
    if normalized < HONEY_FREE_ORDER_CHANCE:
        return 0
    if normalized < HONEY_DOUBLE_ORDER_START:
        return 1
    return 2


def daily_goal_for_day(day: int) -> dict[str, int | str]:
    if is_blueberry_festival(day):
        return {
            "kind": "smoothies",
            "label": "축제 스무디 3잔 판매",
            "target": 3,
            "reward": 220,
            "reputation": 8,
        }
    goals = (
        ("harvest", "블루베리 8개 수확", 8, 45, 3),
        ("smoothies", "주문 스무디 2잔 판매", 2, 80, 4),
        ("earn", "판매로 60코인 벌기", 60, 55, 3),
    )
    kind, label, target, reward, reputation = goals[(max(1, day) - 1) % len(goals)]
    return {
        "kind": kind,
        "label": label,
        "target": target,
        "reward": reward,
        "reputation": reputation,
    }


def tree_drop_key_for_roll(roll: float) -> str:
    normalized = max(0.0, min(0.999999, float(roll)))
    for upper_bound, key in TREE_DROP_TABLE:
        if normalized < upper_bound:
            return key
    return "seeds"


@dataclass(eq=True)
class CustomerOrder:
    """One customer's custom smoothie request."""

    blueberries: int = 3
    honey: int = 1
    milk: int = 1
    ice: int = 1
    customer_name: str = "마을 손님"
    vip: bool = False
    regular: bool = False
    vip_title: str = ""
    story: str = "싱싱한 스무디를 부탁해요."
    wait_seconds: float = field(default=0.0, compare=False)

    @classmethod
    def random(
        cls,
        rng: random.Random | None = None,
        *,
        day: int = 1,
        vip: bool = False,
        customer_name: str | None = None,
        vip_title: str = "",
    ) -> "CustomerOrder":
        picker = rng if rng is not None else random
        season, _day_in_season, _year = season_for_day(day)
        weather = weather_for_day(day)
        ice_min = 2 if season == "여름" or weather == "heat" else 1
        return cls(
            blueberries=3,
            honey=honey_amount_for_roll(picker.random(), day),
            milk=picker.randint(1, 2),
            ice=picker.randint(ice_min, 3),
            customer_name=customer_name or picker.choice(CUSTOMER_NAMES),
            vip=vip,
            vip_title=vip_title if vip else "",
            story=picker.choice(VIP_STORIES if vip else CUSTOMER_STORIES),
        )

    @classmethod
    def from_dict(cls, data: dict) -> "CustomerOrder":
        return cls(
            blueberries=3,
            honey=max(0, min(2, int(data.get("honey", 1)))),
            milk=max(1, min(2, int(data.get("milk", 1)))),
            ice=max(1, min(3, int(data.get("ice", 1)))),
            customer_name=str(data.get("customer_name", "마을 손님"))[:24],
            vip=bool(data.get("vip", False)),
            regular=bool(data.get("regular", False)),
            vip_title=str(data.get("vip_title", ""))[:24],
            story=str(data.get("story", "싱싱한 스무디를 부탁해요."))[:60],
            wait_seconds=max(0.0, float(data.get("wait_seconds", 0.0))),
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
        base = SMOOTHIE_BASE_PRICE + sum(
            self.recipe[key] * reward
            for key, reward in ORDER_INGREDIENT_REWARDS.items()
        )
        return round(base * 1.5) if self.vip else base

    def short_text(self) -> str:
        return f"블루베리 {self.blueberries} · 꿀 {self.honey} · 우유 {self.milk} · 얼음 {self.ice}"

    @property
    def customer_label(self) -> str:
        if self.vip and self.vip_title:
            return f"{self.vip_title} {self.customer_name}"
        return self.customer_name

    @property
    def satisfaction(self) -> int:
        return max(10, min(100, 100 - int(self.wait_seconds * 1.15)))


@dataclass
class Plot:
    planted: bool = False
    ready_at: float = 0.0
    cycle_seconds: float = GROW_SECONDS
    fertilized: bool = False

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
    organic_blueberries: int = 0
    seeds: int = 3
    fertilizer: int = 0
    honey: int = 0
    milk: int = 0
    ice: int = 0
    golden_blueberries: int = 0
    premium_honey: int = 0
    low_fat_milk: int = 0
    fishing_rod: int = 0
    fishing_rod_durability: int = 0
    carp: int = 0
    crucian_carp: int = 0
    bass: int = 0
    turtle: int = 0
    smoothies: int = 0
    active_plots: int = STARTING_PLOTS
    plots: list[Plot] = field(default_factory=lambda: [Plot() for _ in range(MAX_PLOTS)])
    smoothies_sold: int = 0
    customers_waiting: int = CUSTOMER_QUEUE_SIZE
    customer_orders: list[CustomerOrder] = field(default_factory=list)
    prepared_order: CustomerOrder | None = None
    prepared_bonus: int = 0
    prepared_specials: list[str] = field(default_factory=list)
    berries_sold: int = 0
    berries_harvested: int = 0
    land_purchased: int = 0
    started_at: float = field(default_factory=time.time)
    game_elapsed_seconds: float = 0.0
    player_x: float = 360.0
    player_y: float = 380.0
    tutorial_seen: bool = False
    reputation: int = 0
    vip_customers_served: int = 0
    customer_visits: dict[str, int] = field(default_factory=dict)
    tracked_day: int = 1
    daily_berries_harvested: int = 0
    daily_blueberries_sold: int = 0
    daily_smoothies_sold: int = 0
    daily_money_earned: int = 0
    daily_money_spent: int = 0
    pending_daily_report: dict | None = None
    festival_wins: int = 0
    golden_blueberries_sold: int = 0
    trees_shaken: int = 0
    fish_caught: int = 0
    furniture_owned: list[str] = field(default_factory=list)
    furniture_layout: dict[str, list[int]] = field(default_factory=dict)
    tree_shaken_days: dict[str, int] = field(default_factory=dict)
    facility_levels: dict[str, int] = field(
        default_factory=lambda: {key: 0 for key in FACILITY_KEYS}
    )
    facility_ready_days: dict[str, int] = field(
        default_factory=lambda: {key: 0 for key in FACILITY_KEYS}
    )
    streetlights_installed: list[bool] = field(
        default_factory=lambda: [False] * STREETLIGHT_COUNT
    )

    @classmethod
    def new(cls, now: float | None = None) -> "GameState":
        """Create a friendly starting state with one bush ready to harvest."""
        current = time.time() if now is None else now
        state = cls(started_at=current)
        state.plots[0] = Plot(planted=True, ready_at=current, cycle_seconds=GROW_SECONDS)
        state.customer_orders = []
        state._sync_customer_orders()
        return state

    @property
    def land_cost(self) -> int:
        return LAND_BASE_COST + (self.active_plots - STARTING_PLOTS) * LAND_COST_STEP

    def inventory(self, key: str) -> int:
        return int(getattr(self, key))

    @property
    def current_day(self) -> int:
        return int(max(0.0, self.game_elapsed_seconds) // GAME_DAY_SECONDS) + 1

    @property
    def farm_rank(self) -> int:
        rank = 1
        for index, threshold in enumerate(REPUTATION_THRESHOLDS, start=1):
            if self.reputation >= threshold:
                rank = index
        return min(len(REPUTATION_THRESHOLDS), rank)

    @property
    def next_rank_target(self) -> int | None:
        if self.farm_rank >= len(REPUTATION_THRESHOLDS):
            return None
        return REPUTATION_THRESHOLDS[self.farm_rank]

    @property
    def season(self) -> str:
        return season_for_day(self.current_day)[0]

    @property
    def weather(self) -> str:
        return weather_for_day(self.current_day)

    def make_customer_order(
        self,
        rng: random.Random | None = None,
        *,
        exclude_names: set[str] | None = None,
    ) -> CustomerOrder:
        picker = rng if rng is not None else random
        excluded = exclude_names or set()
        vip_chance = 0.0
        if self.farm_rank >= 2:
            vip_chance = 0.22 + (self.farm_rank - 2) * 0.07
        vip = is_blueberry_festival(self.current_day) or picker.random() < vip_chance
        returning_names = [
            name
            for name, visits in self.customer_visits.items()
            if visits > 0 and name in CUSTOMER_NAMES and name not in excluded
        ]
        returning = bool(returning_names) and picker.random() < REGULAR_RETURN_CHANCE
        if returning:
            customer_name = picker.choice(returning_names)
        else:
            available_names = [name for name in CUSTOMER_NAMES if name not in excluded]
            customer_name = picker.choice(available_names or list(CUSTOMER_NAMES))
        vip_title = picker.choice(VIP_TITLES) if vip else ""
        order = CustomerOrder.random(
            picker,
            day=self.current_day,
            vip=vip,
            customer_name=customer_name,
            vip_title=vip_title,
        )
        order.regular = returning or self.customer_visits.get(order.customer_name, 0) > 0
        if order.regular:
            order.story = "또 왔어요! 지난번처럼 맛있게 만들어 주세요."
        return order

    def harvest_yield_for_day(self, day: int | None = None) -> int:
        selected_day = self.current_day if day is None else max(1, int(day))
        season, _day_in_season, _year = season_for_day(selected_day)
        amount = HARVEST_YIELD
        if season == "가을":
            amount += 1
        if weather_for_day(selected_day) == "rain":
            amount += 1
        return amount

    def crop_seconds_for_day(self, base_seconds: float, day: int | None = None) -> float:
        selected_day = self.current_day if day is None else max(1, int(day))
        weather = weather_for_day(selected_day)
        multiplier = {
            "rain": 0.72,
            "wind": 0.88,
            "sunny": 1.0,
            "heat": 1.12,
            "snow": 1.22,
        }[weather]
        return max(1.0, base_seconds * multiplier)

    def raw_blueberry_price(self, day: int | None = None) -> int:
        selected_day = self.current_day if day is None else max(1, int(day))
        season, _day_in_season, _year = season_for_day(selected_day)
        return RAW_BERRY_PRICE + (2 if season == "겨울" else 0)

    def smoothie_sale_price(
        self,
        order: CustomerOrder | None = None,
        day: int | None = None,
    ) -> int:
        selected_day = self.current_day if day is None else max(1, int(day))
        selected_order = self.current_order if order is None else order
        if selected_order is None:
            return 0
        price = selected_order.price + self.customer_tip(selected_order)
        if weather_for_day(selected_day) == "heat":
            price += 3
        price = round(price * SMOOTHIE_PRICE_MULTIPLIER)
        if is_blueberry_festival(selected_day):
            price *= 2
        if self.prepared_order is not None and self.prepared_order == selected_order:
            price += max(0, int(self.prepared_bonus))
        return price

    @staticmethod
    def customer_tip(order: CustomerOrder) -> int:
        patience_tip = max(0, (order.satisfaction - 50) // 10)
        regular_tip = 2 if order.regular else 0
        return patience_tip + regular_tip

    def tick_customer_wait(self, seconds: float) -> None:
        elapsed = max(0.0, float(seconds))
        if elapsed <= 0:
            return
        self._sync_customer_orders()
        for index, order in enumerate(self.customer_orders):
            # The front customer becomes impatient fastest; people farther
            # back understand that they are still waiting in line.
            order.wait_seconds += elapsed * max(0.35, 1.0 - index * 0.12)

    def daily_goal(self, day: int | None = None) -> dict[str, int | str]:
        return daily_goal_for_day(self.current_day if day is None else day)

    def daily_goal_progress(self, day: int | None = None) -> int:
        goal = self.daily_goal(day)
        kind = goal["kind"]
        if kind == "harvest":
            return self.daily_berries_harvested
        if kind == "smoothies":
            return self.daily_smoothies_sold
        return self.daily_money_earned

    def advance_to_day(self, day: int) -> dict | None:
        new_day = max(1, int(day))
        if new_day <= self.tracked_day:
            return None
        finished_day = self.tracked_day
        goal = self.daily_goal(finished_day)
        progress = self.daily_goal_progress(finished_day)
        complete = progress >= int(goal["target"])
        reward = int(goal["reward"]) if complete else 0
        reputation_reward = int(goal["reputation"]) if complete else 0
        if complete:
            self.money += reward
            self.reputation += reputation_reward
            if is_blueberry_festival(finished_day):
                self.festival_wins += 1
        report = {
            "day": finished_day,
            "earned": self.daily_money_earned,
            "spent": self.daily_money_spent,
            "profit": self.daily_money_earned - self.daily_money_spent,
            "harvested": self.daily_berries_harvested,
            "blueberries_sold": self.daily_blueberries_sold,
            "smoothies_sold": self.daily_smoothies_sold,
            "goal_label": str(goal["label"]),
            "goal_progress": progress,
            "goal_target": int(goal["target"]),
            "goal_complete": complete,
            "reward": reward,
            "reputation_reward": reputation_reward,
            "next_day": new_day,
        }
        self.pending_daily_report = report
        self.tracked_day = new_day
        self.daily_berries_harvested = 0
        self.daily_blueberries_sold = 0
        self.daily_smoothies_sold = 0
        self.daily_money_earned = 0
        self.daily_money_spent = 0
        return report

    def clear_daily_report(self) -> None:
        self.pending_daily_report = None

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

    def tree_shaken_today(self, tree_index: int, day: int | None = None) -> bool:
        selected_day = self.current_day if day is None else max(1, int(day))
        return int(self.tree_shaken_days.get(str(tree_index), 0)) == selected_day

    def shake_tree(
        self,
        tree_index: int,
        rng: random.Random | None = None,
        *,
        day: int | None = None,
    ) -> tuple[bool, str, str | None, int]:
        selected_day = self.current_day if day is None else max(1, int(day))
        if self.tree_shaken_today(tree_index, selected_day):
            return False, "이 나무는 오늘 이미 흔들었어요. 내일 다시 와 주세요.", None, 0
        picker = rng if rng is not None else random
        key = tree_drop_key_for_roll(picker.random())
        if key == "coins":
            amount = picker.randint(100, 250)
        elif key in ("golden_blueberries", "premium_honey", "low_fat_milk", "seeds"):
            amount = 1
        else:
            amount = picker.randint(1, 3)
        if key != "coins" and not self.can_add_to_bag(key, amount):
            return False, "가방에 빈 칸이 부족해서 떨어진 아이템을 받을 수 없어요.", None, 0

        self.tree_shaken_days[str(tree_index)] = selected_day
        self.trees_shaken += 1
        if key == "coins":
            self.money += amount
            self.daily_money_earned += amount
            return True, f"나무에서 코인 {amount}개가 떨어졌어요!", key, amount
        setattr(self, key, self.inventory(key) + amount)
        return True, f"나무에서 {BAG_ITEM_LABELS[key]} {amount}개가 떨어졌어요!", key, amount

    def facility_level(self, key: str) -> int:
        return max(0, min(MAX_FACILITY_LEVEL, int(self.facility_levels.get(key, 0))))

    def facility_build_cost(self, key: str) -> int:
        return int(FACILITY_CONFIG[key]["cost"])

    def facility_upgrade_cost(self, key: str) -> int | None:
        level = self.facility_level(key)
        if level <= 0 or level >= MAX_FACILITY_LEVEL:
            return None
        return int(FACILITY_CONFIG[key]["upgrade_costs"][level])

    def facility_yield(self, key: str) -> int:
        level = self.facility_level(key)
        yields = FACILITY_CONFIG[key]["yields"]
        return int(yields[level])

    def facility_is_ready(self, key: str, day: int | None = None) -> bool:
        level = self.facility_level(key)
        selected_day = self.current_day if day is None else max(1, int(day))
        return level > 0 and selected_day >= int(self.facility_ready_days.get(key, 0))

    def build_facility(self, key: str, day: int | None = None) -> tuple[bool, str]:
        if key not in FACILITY_CONFIG:
            return False, "알 수 없는 생산 시설이에요."
        config = FACILITY_CONFIG[key]
        if self.facility_level(key) > 0:
            return False, f"{config['name']}은 이미 지어져 있어요."
        required_rank = int(config["unlock_rank"])
        if self.farm_rank < required_rank:
            return False, f"농장 등급 {required_rank}부터 {config['name']}을 지을 수 있어요."
        cost = self.facility_build_cost(key)
        if self.money < cost:
            return False, f"{config['name']} 건설에는 {cost:,}코인이 필요해요."
        selected_day = self.current_day if day is None else max(1, int(day))
        self.money -= cost
        self.daily_money_spent += cost
        self.facility_levels[key] = 1
        self.facility_ready_days[key] = selected_day + 1
        return True, f"{config['name']}을 지었어요! 내일부터 {config['product_name']}을 받을 수 있어요."

    def upgrade_facility(self, key: str) -> tuple[bool, str]:
        if key not in FACILITY_CONFIG:
            return False, "알 수 없는 생산 시설이에요."
        config = FACILITY_CONFIG[key]
        level = self.facility_level(key)
        if level <= 0:
            return False, f"먼저 {config['name']}을 지어 주세요."
        if level >= MAX_FACILITY_LEVEL:
            return False, f"{config['name']}은 이미 최고 단계예요."
        required_rank = int(config["unlock_rank"]) + level
        if self.farm_rank < required_rank:
            return False, f"{level + 1}단계 업그레이드는 농장 등급 {required_rank}부터 가능해요."
        cost = self.facility_upgrade_cost(key)
        assert cost is not None
        if self.money < cost:
            return False, f"업그레이드에는 {cost:,}코인이 필요해요."
        self.money -= cost
        self.daily_money_spent += cost
        self.facility_levels[key] = level + 1
        amount = self.facility_yield(key)
        return True, f"{config['name']}이 {level + 1}단계가 됐어요! 하루 생산량은 {amount}개예요."

    def collect_facility(self, key: str, day: int | None = None) -> tuple[bool, str]:
        if key not in FACILITY_CONFIG:
            return False, "알 수 없는 생산 시설이에요."
        config = FACILITY_CONFIG[key]
        level = self.facility_level(key)
        if level <= 0:
            return False, f"아직 {config['name']}을 짓지 않았어요."
        selected_day = self.current_day if day is None else max(1, int(day))
        ready_day = int(self.facility_ready_days.get(key, selected_day + 1))
        if selected_day < ready_day:
            return False, f"{config['product_name']}은 {ready_day}일차에 준비돼요."
        product = str(config["product"])
        amount = self.facility_yield(key)
        if not self.can_add_to_bag(product, amount):
            return False, "가방에 빈 칸이 부족해요. 재료를 사용한 뒤 다시 수확해 주세요."
        setattr(self, product, self.inventory(product) + amount)
        self.facility_ready_days[key] = selected_day + 1
        return True, f"{config['name']}에서 {config['product_name']} {amount}개를 받았어요!"

    def _normalize_customer_identities(self) -> None:
        """Upgrade legacy/duplicate queue names without changing their orders."""
        migrated_visits: dict[str, int] = {}
        for name, visits in self.customer_visits.items():
            migrated_name = LEGACY_CUSTOMER_NAME_MAP.get(name, name)
            migrated_visits[migrated_name] = (
                migrated_visits.get(migrated_name, 0) + max(0, int(visits))
            )
        self.customer_visits = migrated_visits

        used_names: set[str] = set()
        for index, order in enumerate(self.customer_orders):
            if order.vip and order.customer_name in VIP_TITLES:
                order.vip_title = order.customer_name
                order.customer_name = "마을 손님"
            order.customer_name = LEGACY_CUSTOMER_NAME_MAP.get(
                order.customer_name,
                order.customer_name,
            )
            needs_new_name = (
                order.customer_name == "마을 손님"
                or order.customer_name in used_names
                or order.customer_name not in CUSTOMER_NAMES
            )
            if needs_new_name:
                start = (self.current_day * 37 + index * 53) % len(CUSTOMER_NAMES)
                for offset in range(len(CUSTOMER_NAMES)):
                    candidate = CUSTOMER_NAMES[(start + offset) % len(CUSTOMER_NAMES)]
                    if candidate not in used_names:
                        order.customer_name = candidate
                        break
            if order.vip and not order.vip_title:
                order.vip_title = VIP_TITLES[index % len(VIP_TITLES)]
            if not order.vip:
                order.vip_title = ""
            order.regular = self.customer_visits.get(order.customer_name, 0) > 0
            used_names.add(order.customer_name)

    def _sync_customer_orders(self) -> None:
        self.customers_waiting = max(
            0, min(CUSTOMER_QUEUE_SIZE, int(self.customers_waiting))
        )
        self.customer_orders = self.customer_orders[:self.customers_waiting]
        used_names = {order.customer_name for order in self.customer_orders}
        while len(self.customer_orders) < self.customers_waiting:
            order = self.make_customer_order(exclude_names=used_names)
            self.customer_orders.append(order)
            used_names.add(order.customer_name)

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
        if order is None:
            used_names = {current.customer_name for current in self.customer_orders}
            order = self.make_customer_order(rng, exclude_names=used_names)
        self.customer_orders.append(order)
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
        # A crop cycle is a predictable real-time minute. Weather and season
        # can still affect yield, but never silently shorten this cooldown.
        grow_seconds = GROW_SECONDS
        self.plots[plot_index] = Plot(
            planted=True,
            ready_at=current + grow_seconds,
            cycle_seconds=grow_seconds,
            fertilized=False,
        )
        return True, "블루베리 씨앗을 심었어요! 60초 뒤에 수확할 수 있어요."

    def harvest(self, plot_index: int, now: float | None = None) -> tuple[bool, str]:
        current = time.time() if now is None else now
        if not 0 <= plot_index < self.active_plots:
            return False, "아직 사용할 수 없는 땅이에요."
        plot = self.plots[plot_index]
        if not plot.planted:
            return False, "빈 밭이에요. 눌러서 씨앗을 심어 주세요."
        if not plot.is_ready(current):
            return False, f"조금만 기다려 주세요. {int(plot.remaining(current)) + 1}초 남았어요."
        harvest_yield = self.harvest_yield_for_day()
        harvest_key = "organic_blueberries" if plot.fertilized else "blueberries"
        if not self.can_add_to_bag(harvest_key, harvest_yield):
            return False, "가방이 가득 차서 수확할 수 없어요. B를 눌러 가방을 확인하세요."
        setattr(self, harvest_key, self.inventory(harvest_key) + harvest_yield)
        self.berries_harvested += harvest_yield
        self.daily_berries_harvested += harvest_yield
        regrow_seconds = REGROW_SECONDS
        self.plots[plot_index] = Plot(
            planted=True,
            ready_at=current + regrow_seconds,
            cycle_seconds=regrow_seconds,
            fertilized=False,
        )
        if harvest_key == "organic_blueberries":
            return True, f"유기농 블루베리 {harvest_yield}개를 수확했어요!"
        return True, f"싱싱한 블루베리 {harvest_yield}개를 수확했어요!"

    def fertilize(self, plot_index: int) -> tuple[bool, str]:
        if not 0 <= plot_index < self.active_plots:
            return False, "아직 사용할 수 없는 땅이에요."
        plot = self.plots[plot_index]
        if not plot.planted:
            return False, "먼저 블루베리 씨앗을 심어 주세요."
        if plot.fertilized:
            return False, "이 밭에는 이미 비료를 사용했어요."
        if self.fertilizer < 1:
            return False, "비료가 없어요. 상점에서 구입해 주세요."
        self.fertilizer -= 1
        plot.fertilized = True
        return True, "비료를 사용했어요! 다음 수확은 유기농 블루베리예요."

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
        self.daily_money_spent += cost
        setattr(self, key, self.inventory(key) + 1)
        return True, f"{ITEM_LABELS[key]} 1개를 샀어요."

    def buy_fishing_rod(self) -> tuple[bool, str]:
        if self.fishing_rod:
            return False, "이미 낚싯대를 가지고 있어요."
        if self.money < FISHING_ROD_COST:
            return False, f"낚싯대를 사려면 {FISHING_ROD_COST:,}코인이 필요해요."
        if not self.can_add_to_bag("fishing_rod", 1):
            return False, "가방에 낚싯대를 넣을 한 칸이 필요해요."
        self.money -= FISHING_ROD_COST
        self.daily_money_spent += FISHING_ROD_COST
        self.fishing_rod = 1
        self.fishing_rod_durability = FISHING_ROD_MAX_DURABILITY
        return True, (
            f"낚싯대를 샀어요! 내구도는 {FISHING_ROD_MAX_DURABILITY}이고 "
            "연못가에서 E로 낚시할 수 있어요."
        )

    def use_fishing_rod(self) -> tuple[bool, str, bool]:
        """Consume one cast of durability and report whether the rod broke."""
        if not self.fishing_rod or self.fishing_rod_durability <= 0:
            self.fishing_rod = 0
            self.fishing_rod_durability = 0
            return False, "낚싯대가 없어요. 상점에서 먼저 구입해 주세요.", False
        self.fishing_rod_durability -= 1
        broke = self.fishing_rod_durability <= 0
        if broke:
            self.fishing_rod = 0
            self.fishing_rod_durability = 0
            return True, "40번째 찌를 던져 낚싯대가 부서졌어요!", True
        return True, f"낚싯대 내구도 {self.fishing_rod_durability}/{FISHING_ROD_MAX_DURABILITY}", False

    def catch_fish(
        self,
        rng: random.Random | None = None,
        *,
        active_cast: bool = False,
    ) -> tuple[bool, str, str | None]:
        if not self.fishing_rod and not active_cast:
            return False, "낚싯대가 없어요. 상점에서 먼저 구입해 주세요.", None
        picker = rng if rng is not None else random
        roll = picker.random()
        fish_key = FISH_CATCH_TABLE[-1][1]
        for threshold, candidate in FISH_CATCH_TABLE:
            if roll < threshold:
                fish_key = candidate
                break
        if not self.can_add_to_bag(fish_key, 1):
            return False, "가방이 가득 차서 물고기를 담을 수 없어요.", None
        setattr(self, fish_key, self.inventory(fish_key) + 1)
        self.fish_caught += 1
        return True, f"{BAG_ITEM_LABELS[fish_key]}을(를) 낚았어요!", fish_key

    def sell_fish(self, key: str) -> tuple[bool, str]:
        if key not in FISH_PRICES:
            return False, "판매할 수 없는 물고기예요."
        if self.inventory(key) < 1:
            return False, f"판매할 {BAG_ITEM_LABELS[key]}이(가) 없어요."
        price = FISH_PRICES[key]
        setattr(self, key, self.inventory(key) - 1)
        self.money += price
        self.daily_money_earned += price
        return True, f"{BAG_ITEM_LABELS[key]} 1마리를 팔아 {price}코인을 벌었어요."

    def buy_furniture(self, key: str) -> tuple[bool, str]:
        if key not in FURNITURE_COSTS:
            return False, "판매하지 않는 가구예요."
        if key in self.furniture_owned:
            return False, f"{FURNITURE_LABELS[key]}은(는) 이미 집에 있어요."
        cost = FURNITURE_COSTS[key]
        if self.money < cost:
            return False, f"{FURNITURE_LABELS[key]} 구입에는 {cost:,}코인이 필요해요."
        self.money -= cost
        self.daily_money_spent += cost
        self.furniture_owned.append(key)
        return True, (
            f"{FURNITURE_LABELS[key]}을(를) 구입해 보관함에 넣었어요. "
            "G를 눌러 배치해 보세요."
        )

    @staticmethod
    def furniture_footprint(key: str, rotation: int = 0) -> tuple[int, int]:
        width, height = FURNITURE_FOOTPRINTS[key]
        if int(rotation) % 2:
            return height, width
        return width, height

    def can_place_furniture(
        self,
        key: str,
        column: int,
        row: int,
        rotation: int = 0,
    ) -> bool:
        if key not in self.furniture_owned or key not in FURNITURE_FOOTPRINTS:
            return False
        width, height = self.furniture_footprint(key, rotation)
        if (
            column < 0
            or row < 0
            or column + width > FURNITURE_GRID_COLUMNS
            or row + height > FURNITURE_GRID_ROWS
        ):
            return False
        candidate = (column, row, width, height)
        for other_key, raw_layout in self.furniture_layout.items():
            if other_key == key or other_key not in FURNITURE_FOOTPRINTS:
                continue
            other_column, other_row, other_rotation = raw_layout
            other_width, other_height = self.furniture_footprint(
                other_key,
                other_rotation,
            )
            separated = (
                candidate[0] + candidate[2] <= other_column
                or other_column + other_width <= candidate[0]
                or candidate[1] + candidate[3] <= other_row
                or other_row + other_height <= candidate[1]
            )
            if not separated:
                return False
        return True

    def place_furniture(
        self,
        key: str,
        column: int,
        row: int,
        rotation: int = 0,
    ) -> tuple[bool, str]:
        column = int(column)
        row = int(row)
        rotation = int(rotation) % 2
        if key not in self.furniture_owned:
            return False, "먼저 가구를 구입해 주세요."
        if not self.can_place_furniture(key, column, row, rotation):
            return False, "다른 가구와 겹치거나 방 바깥이라 놓을 수 없어요."
        self.furniture_layout[key] = [column, row, rotation]
        return True, f"{FURNITURE_LABELS[key]}을(를) 원하는 위치에 놓았어요."

    def store_furniture(self, key: str) -> tuple[bool, str]:
        if key not in self.furniture_owned:
            return False, "보유하지 않은 가구예요."
        if key not in self.furniture_layout:
            return False, "이 가구는 이미 보관함에 있어요."
        self.furniture_layout.pop(key)
        return True, f"{FURNITURE_LABELS[key]}을(를) 보관함에 넣었어요."

    def sell_blueberry_batch(
        self,
        key: str,
        amount: int | None = 1,
        day: int | None = None,
    ) -> tuple[bool, str]:
        products = {
            "blueberries": ("블루베리", self.raw_blueberry_price(day)),
            "golden_blueberries": ("황금 블루베리", GOLDEN_BLUEBERRY_PRICE),
            "organic_blueberries": ("유기농 블루베리", ORGANIC_BLUEBERRY_PRICE),
        }
        if key not in products:
            return False, "판매할 수 없는 물건이에요."
        available = max(0, int(getattr(self, key)))
        if available < 1:
            return False, f"판매할 {products[key][0]}가 없어요."
        if amount is None:
            quantity = available
        else:
            requested = int(amount)
            if requested < 1:
                return False, "판매 수량은 1개 이상이어야 해요."
            quantity = min(requested, available)

        label, unit_price = products[key]
        total = unit_price * quantity
        setattr(self, key, available - quantity)
        self.money += total
        self.daily_money_earned += total
        if key == "golden_blueberries":
            self.golden_blueberries_sold += quantity
        else:
            self.berries_sold += quantity
            self.daily_blueberries_sold += quantity
        return True, f"{label} {quantity}개를 팔아 {total:,}코인을 벌었어요."

    def sell_blueberry(self, day: int | None = None) -> tuple[bool, str]:
        return self.sell_blueberry_batch("blueberries", 1, day)

    def sell_golden_blueberry(self) -> tuple[bool, str]:
        return self.sell_blueberry_batch("golden_blueberries")

    def sell_organic_blueberry(self) -> tuple[bool, str]:
        return self.sell_blueberry_batch("organic_blueberries")

    def make_smoothie(
        self,
        selected_recipe: dict[str, int] | None = None,
        selected_specials: dict[str, bool] | None = None,
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
            order.wait_seconds += 4.0
            return False, "주문과 달라요: " + ", ".join(differences)

        missing: list[str] = []
        for key, amount in recipe.items():
            if self.inventory(key) < amount:
                missing.append(f"{labels[key]} {amount - self.inventory(key)}")
        if missing:
            return False, "재료가 부족해요: " + ", ".join(missing)
        special_labels = {
            "premium_honey": "고급 꿀",
            "low_fat_milk": "저지방 우유",
        }
        chosen_specials = [
            key
            for key, selected in (selected_specials or {}).items()
            if selected and key in special_labels
        ]
        missing_specials = [
            special_labels[key]
            for key in chosen_specials
            if self.inventory(key) < 1
        ]
        if missing_specials:
            return False, "특수 재료가 부족해요: " + ", ".join(missing_specials)
        for key, amount in recipe.items():
            setattr(self, key, self.inventory(key) - amount)
        for key in chosen_specials:
            setattr(self, key, self.inventory(key) - 1)
        self.smoothies += 1
        self.prepared_order = CustomerOrder(
            **order.recipe,
            customer_name=order.customer_name,
            vip=order.vip,
            regular=order.regular,
            vip_title=order.vip_title,
            story=order.story,
            wait_seconds=order.wait_seconds,
        )
        self.prepared_specials = chosen_specials
        self.prepared_bonus = len(chosen_specials) * SPECIAL_SMOOTHIE_BONUS
        sale_price = self.smoothie_sale_price(order)
        bonus_note = f" 특수 재료 보너스 +{self.prepared_bonus}코인!" if chosen_specials else ""
        return True, f"주문대로 스무디 완성! 판매하면 {sale_price}코인을 받아요.{bonus_note}"

    def sell_smoothie(self, day: int | None = None) -> tuple[bool, str]:
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
        sale_price = self.smoothie_sale_price(order, day)
        self.money += sale_price
        self.smoothies_sold += 1
        self.daily_smoothies_sold += 1
        self.daily_money_earned += sale_price
        reputation_gain = 5 if order.vip else 2
        if order.satisfaction >= 85:
            reputation_gain += 1
        if order.regular:
            reputation_gain += 1
        self.reputation += reputation_gain
        if order.vip:
            self.vip_customers_served += 1
        self.customer_visits[order.customer_name] = (
            self.customer_visits.get(order.customer_name, 0) + 1
        )
        self.prepared_order = None
        self.prepared_bonus = 0
        self.prepared_specials = []
        customer_type = (
            f"VIP · {order.vip_title}" if order.vip and order.vip_title
            else "VIP" if order.vip
            else "단골" if order.regular
            else "손님"
        )
        return True, (
            f"{order.customer_name} {customer_type} 만족도 {order.satisfaction}%! "
            f"{sale_price}코인 · 평판 +{reputation_gain}"
        )

    def buy_land(self) -> tuple[bool, str]:
        if self.active_plots >= MAX_PLOTS:
            return False, "농장을 최대로 넓혔어요!"
        cost = self.land_cost
        if self.money < cost:
            return False, f"텃밭을 사려면 {cost:,}코인이 필요해요."
        self.money -= cost
        self.daily_money_spent += cost
        self.active_plots += 1
        self.land_purchased += 1
        return True, f"새 텃밭을 샀어요! 이제 밭이 {self.active_plots}칸이에요."

    def buy_streetlight(self, index: int) -> tuple[bool, str]:
        if not 0 <= index < STREETLIGHT_COUNT:
            return False, "설치할 수 없는 가로등 부지예요."
        if self.streetlights_installed[index]:
            return False, "이곳에는 이미 가로등이 설치되어 있어요."
        if self.money < STREETLIGHT_COST:
            return False, f"가로등 설치에는 {STREETLIGHT_COST:,}코인이 필요해요."
        self.money -= STREETLIGHT_COST
        self.daily_money_spent += STREETLIGHT_COST
        self.streetlights_installed[index] = True
        return True, "가로등을 설치했어요! 저녁부터 주변을 환하게 밝혀 줍니다."

    def to_dict(self) -> dict:
        data = asdict(self)
        data["save_version"] = SAVE_VERSION
        data["streetlight_layout_version"] = STREETLIGHT_LAYOUT_VERSION
        elapsed = max(0.0, float(self.game_elapsed_seconds))
        data["calendar_day"] = self.current_day
        data["day_progress"] = (elapsed % GAME_DAY_SECONDS) / GAME_DAY_SECONDS
        data["day_length_seconds"] = GAME_DAY_SECONDS
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
            if save_version not in (1, 2, 3, 4, SAVE_VERSION):
                raise ValueError("지원하지 않는 저장 파일 버전입니다.")
            had_tracked_day = "tracked_day" in raw
            saved_calendar_day = raw.pop("calendar_day", None)
            saved_day_progress = raw.pop("day_progress", None)
            saved_day_length = raw.pop("day_length_seconds", None)
            plot_data = raw.pop("plots")
            order_data = raw.pop("customer_orders", [])
            prepared_order_data = raw.pop("prepared_order", None)
            raw.pop("save_version", None)
            streetlight_layout_version = raw.pop("streetlight_layout_version", None)
            raw_elapsed = max(0.0, float(raw.get("game_elapsed_seconds", 0.0)))
            if saved_calendar_day is not None and saved_day_progress is not None:
                calendar_day = max(1, int(saved_calendar_day))
                day_progress = max(0.0, min(0.999999999, float(saved_day_progress)))
            else:
                previous_day_length = (
                    max(1.0, float(saved_day_length))
                    if saved_day_length is not None
                    else LEGACY_GAME_DAY_SECONDS
                )
                elapsed_day = int(raw_elapsed // previous_day_length) + 1
                tracked_day = max(1, int(raw.get("tracked_day", elapsed_day)))
                # Older saves did not store the date explicitly. If their
                # counters disagree, keep the later known day so loading can
                # never move a player's calendar backwards.
                calendar_day = max(elapsed_day, tracked_day)
                day_progress = (raw_elapsed % previous_day_length) / previous_day_length
            raw["game_elapsed_seconds"] = (
                (calendar_day - 1) + day_progress
            ) * GAME_DAY_SECONDS
            allowed = {field_name for field_name in cls.__dataclass_fields__}
            had_rod_durability = "fishing_rod_durability" in raw
            had_furniture_layout = "furniture_layout" in raw
            state = cls(**{key: value for key, value in raw.items() if key in allowed})
            state.active_plots = max(STARTING_PLOTS, min(MAX_PLOTS, int(state.active_plots)))
            state.game_elapsed_seconds = max(0.0, float(state.game_elapsed_seconds))
            state.reputation = max(0, int(state.reputation))
            state.vip_customers_served = max(0, int(state.vip_customers_served))
            state.festival_wins = max(0, int(state.festival_wins))
            state.golden_blueberries = max(0, int(state.golden_blueberries))
            state.organic_blueberries = max(0, int(state.organic_blueberries))
            state.fertilizer = max(0, int(state.fertilizer))
            state.premium_honey = max(0, int(state.premium_honey))
            state.low_fat_milk = max(0, int(state.low_fat_milk))
            state.fishing_rod = 1 if state.fishing_rod else 0
            if state.fishing_rod:
                if had_rod_durability:
                    state.fishing_rod_durability = max(
                        0,
                        min(
                            FISHING_ROD_MAX_DURABILITY,
                            int(state.fishing_rod_durability),
                        ),
                    )
                else:
                    # Rods from older saves begin with full durability.
                    state.fishing_rod_durability = FISHING_ROD_MAX_DURABILITY
                if state.fishing_rod_durability <= 0:
                    state.fishing_rod = 0
            else:
                state.fishing_rod_durability = 0
            for fish_key in FISH_PRICES:
                setattr(state, fish_key, max(0, int(getattr(state, fish_key))))
            state.fish_caught = max(0, int(state.fish_caught))
            raw_furniture = state.furniture_owned if isinstance(state.furniture_owned, list) else []
            state.furniture_owned = [
                key for key in FURNITURE_COSTS
                if key in raw_furniture
            ]
            raw_layout = (
                state.furniture_layout
                if isinstance(state.furniture_layout, dict)
                else {}
            )
            state.furniture_layout = {}
            for furniture_key in state.furniture_owned:
                candidate = (
                    raw_layout.get(furniture_key)
                    if had_furniture_layout
                    else DEFAULT_FURNITURE_LAYOUT.get(furniture_key)
                )
                if not isinstance(candidate, (list, tuple)) or len(candidate) != 3:
                    continue
                try:
                    column, row, rotation = (int(value) for value in candidate)
                except (TypeError, ValueError):
                    continue
                rotation %= 2
                if state.can_place_furniture(
                    furniture_key,
                    column,
                    row,
                    rotation,
                ):
                    state.furniture_layout[furniture_key] = [
                        column,
                        row,
                        rotation,
                    ]
            state.golden_blueberries_sold = max(0, int(state.golden_blueberries_sold))
            state.trees_shaken = max(0, int(state.trees_shaken))
            raw_tree_days = state.tree_shaken_days if isinstance(state.tree_shaken_days, dict) else {}
            state.tree_shaken_days = {
                str(index): max(0, int(shaken_day))
                for index, shaken_day in raw_tree_days.items()
            }
            raw_visits = state.customer_visits if isinstance(state.customer_visits, dict) else {}
            state.customer_visits = {
                str(name)[:24]: max(0, int(visits))
                for name, visits in raw_visits.items()
            }
            for counter_name in (
                "daily_berries_harvested",
                "daily_blueberries_sold",
                "daily_smoothies_sold",
                "daily_money_earned",
                "daily_money_spent",
            ):
                setattr(state, counter_name, max(0, int(getattr(state, counter_name))))
            if had_tracked_day:
                state.tracked_day = min(
                    state.current_day,
                    max(1, int(state.tracked_day)),
                )
            else:
                # Old saves did not have daily counters. Start tracking from
                # their current day instead of inventing reports for past days.
                state.tracked_day = state.current_day
            if not isinstance(state.pending_daily_report, dict):
                state.pending_daily_report = None
            raw_levels = state.facility_levels if isinstance(state.facility_levels, dict) else {}
            raw_ready_days = (
                state.facility_ready_days
                if isinstance(state.facility_ready_days, dict)
                else {}
            )
            state.facility_levels = {
                key: max(0, min(MAX_FACILITY_LEVEL, int(raw_levels.get(key, 0))))
                for key in FACILITY_KEYS
            }
            state.facility_ready_days = {
                key: max(0, int(raw_ready_days.get(key, 0)))
                for key in FACILITY_KEYS
            }
            raw_streetlights = (
                state.streetlights_installed
                if isinstance(state.streetlights_installed, list)
                else []
            )
            # Sites were deliberately relocated after the old layout was
            # removed. Never carry installed flags onto unrelated new places.
            if streetlight_layout_version != STREETLIGHT_LAYOUT_VERSION:
                raw_streetlights = []
            state.streetlights_installed = [
                bool(raw_streetlights[index])
                if index < len(raw_streetlights)
                else False
                for index in range(STREETLIGHT_COUNT)
            ]
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
            allowed_specials = {"premium_honey", "low_fat_milk"}
            if not isinstance(state.prepared_specials, list):
                state.prepared_specials = []
            state.prepared_specials = [
                key for key in state.prepared_specials if key in allowed_specials
            ]
            state.prepared_bonus = max(0, int(state.prepared_bonus))
            if state.prepared_order is None:
                state.prepared_specials = []
                state.prepared_bonus = 0
            state._normalize_customer_identities()
            state._sync_customer_orders()
            # A smoothie can only be prepared for the first customer. When an
            # old save upgrades a short/duplicate name, keep that prepared
            # smoothie paired with the migrated customer instead of rejecting
            # it as somebody else's order.
            if state.prepared_order is not None and state.customer_orders:
                front_order = state.customer_orders[0]
                state.prepared_order.customer_name = front_order.customer_name
                state.prepared_order.vip = front_order.vip
                state.prepared_order.regular = front_order.regular
                state.prepared_order.vip_title = front_order.vip_title
                state.prepared_order.story = front_order.story
            state.plots = []
            for item in plot_data[:MAX_PLOTS]:
                state.plots.append(
                    Plot(
                        planted=bool(item.get("planted", False)),
                        ready_at=float(item.get("ready_at", 0.0)),
                        cycle_seconds=max(0.1, float(item.get("cycle_seconds", GROW_SECONDS))),
                        fertilized=bool(item.get("fertilized", False)),
                    )
                )
            while len(state.plots) < MAX_PLOTS:
                state.plots.append(Plot())
            return state
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            if on_error is not None:
                on_error(exc)
            return cls.new(current)
