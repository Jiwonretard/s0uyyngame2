import json
import random
import tempfile
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game_state import (  # noqa: E402
    BAG_SLOT_COUNT,
    BAG_STACK_SIZE,
    CUSTOMER_QUEUE_SIZE,
    CustomerOrder,
    DAYS_PER_SEASON,
    FACILITY_CONFIG,
    GAME_DAY_SECONDS,
    GOLDEN_BLUEBERRY_PRICE,
    GROW_SECONDS,
    HARVEST_YIELD,
    LAND_BASE_COST,
    LAND_COST_STEP,
    RAW_BERRY_PRICE,
    REGROW_SECONDS,
    SPECIAL_SMOOTHIE_BONUS,
    TREE_DROP_TABLE,
    GameState,
    is_blueberry_festival,
    season_for_day,
    tree_drop_key_for_roll,
    weather_for_day,
)


class FixedRng:
    def __init__(self, roll: float, amount: int = 1):
        self.roll = roll
        self.amount = amount

    def random(self) -> float:
        return self.roll

    def randint(self, start: int, end: int) -> int:
        return max(start, min(end, self.amount))


class GameStateTests(unittest.TestCase):
    def test_new_game_has_ready_bush_and_can_harvest(self):
        state = GameState.new(now=100.0)
        self.assertEqual((state.player_x, state.player_y), (360.0, 380.0))
        self.assertTrue(state.plots[0].is_ready(100.0))
        ok, _ = state.harvest(0, now=100.0)
        self.assertTrue(ok)
        self.assertEqual(state.blueberries, HARVEST_YIELD)
        self.assertEqual(state.plots[0].ready_at, 100.0 + REGROW_SECONDS)

    def test_plant_consumes_seed_and_grows(self):
        state = GameState.new(now=100.0)
        before = state.seeds
        ok, _ = state.plant(1, now=100.0)
        self.assertTrue(ok)
        self.assertEqual(state.seeds, before - 1)
        self.assertFalse(state.plots[1].is_ready(100.0 + GROW_SECONDS - 0.01))
        self.assertTrue(state.plots[1].is_ready(100.0 + GROW_SECONDS))

    def test_complete_smoothie_economy_loop(self):
        state = GameState.new(now=100.0)
        order = CustomerOrder(blueberries=3, honey=2, milk=1, ice=3)
        state.customers_waiting = 1
        state.customer_orders = [order]
        state.blueberries = order.blueberries
        state.honey = order.honey
        state.milk = order.milk
        state.ice = order.ice
        starting_money = state.money
        ok, _ = state.make_smoothie()
        self.assertTrue(ok)
        self.assertEqual(state.smoothies, 1)
        self.assertEqual(state.prepared_order, order)
        self.assertEqual((state.blueberries, state.honey, state.milk, state.ice), (0, 0, 0, 0))
        expected_sale_price = state.smoothie_sale_price(order)
        ok, _ = state.sell_smoothie()
        self.assertTrue(ok)
        self.assertEqual(state.smoothies, 0)
        self.assertEqual(state.money, starting_money + expected_sale_price)
        self.assertEqual(state.smoothies_sold, 1)
        self.assertEqual(state.customers_waiting, 0)
        self.assertIsNone(state.current_order)

    def test_customer_orders_are_moderate_and_more_ingredients_pay_more(self):
        for _ in range(100):
            order = CustomerOrder.random()
            self.assertEqual(order.blueberries, 3)
            self.assertIn(order.honey, range(0, 3))
            self.assertIn(order.milk, range(1, 3))
            self.assertIn(order.ice, range(1, 4))

        light = CustomerOrder(blueberries=3, honey=0, milk=1, ice=1)
        loaded = CustomerOrder(blueberries=3, honey=2, milk=2, ice=3)
        self.assertGreater(loaded.price, light.price)

    def test_blender_requires_the_front_customers_exact_amounts(self):
        state = GameState.new(now=100.0)
        state.customers_waiting = 1
        state.customer_orders = [CustomerOrder(3, 2, 2, 3)]
        state.blueberries = 3
        state.honey = state.milk = state.ice = 1

        ok, message = state.make_smoothie()

        self.assertFalse(ok)
        self.assertIn("꿀 1", message)
        self.assertIn("우유 1", message)
        self.assertIn("얼음 2", message)
        self.assertEqual(state.smoothies, 0)

    def test_manual_blender_rejects_wrong_recipe_without_using_ingredients(self):
        state = GameState.new(now=100.0)
        order = CustomerOrder(3, 2, 1, 2)
        state.customers_waiting = 1
        state.customer_orders = [order]
        state.blueberries = 5
        state.honey = 3
        state.milk = 2
        state.ice = 4
        before = (state.blueberries, state.honey, state.milk, state.ice)

        ok, message = state.make_smoothie({
            "blueberries": 3,
            "honey": 1,
            "milk": 1,
            "ice": 3,
        })

        self.assertFalse(ok)
        self.assertIn("꿀 1개 더 넣기", message)
        self.assertIn("얼음 1개 빼기", message)
        self.assertEqual((state.blueberries, state.honey, state.milk, state.ice), before)

    def test_raw_berry_sale_and_land_price_progression(self):
        state = GameState.new(now=100.0)
        state.blueberries = 1
        starting_money = state.money
        ok, _ = state.sell_blueberry()
        self.assertTrue(ok)
        self.assertEqual(state.money, starting_money + RAW_BERRY_PRICE)
        first_cost = state.land_cost
        self.assertEqual(first_cost, LAND_BASE_COST)
        state.money = first_cost
        ok, _ = state.buy_land()
        self.assertTrue(ok)
        self.assertEqual(state.money, 0)
        self.assertEqual(state.land_cost, first_cost + LAND_COST_STEP)
        second_cost = state.land_cost
        state.money = second_cost
        ok, _ = state.buy_land()
        self.assertTrue(ok)
        self.assertEqual(state.money, 0)
        self.assertEqual(state.land_cost, second_cost + LAND_COST_STEP)

    def test_tree_drop_probabilities_and_daily_shake_limit(self):
        self.assertEqual(
            TREE_DROP_TABLE,
            (
                (0.20, "blueberries"),
                (0.40, "honey"),
                (0.60, "milk"),
                (0.80, "ice"),
                (0.85, "coins"),
                (0.90, "golden_blueberries"),
                (0.95, "premium_honey"),
                (1.00, "low_fat_milk"),
            ),
        )
        threshold_cases = (
            (0.00, "blueberries"),
            (0.20, "honey"),
            (0.40, "milk"),
            (0.60, "ice"),
            (0.80, "coins"),
            (0.85, "golden_blueberries"),
            (0.90, "premium_honey"),
            (0.95, "low_fat_milk"),
        )
        for roll, expected in threshold_cases:
            self.assertEqual(tree_drop_key_for_roll(roll), expected)

        state = GameState.new(now=100.0)
        starting_money = state.money
        ok, _, key, amount = state.shake_tree(2, FixedRng(0.81, 150), day=1)
        self.assertTrue(ok)
        self.assertEqual((key, amount), ("coins", 150))
        self.assertEqual(state.money, starting_money + 150)
        self.assertEqual(state.daily_money_earned, 150)
        self.assertTrue(state.tree_shaken_today(2, day=1))

        ok, message, _key, _amount = state.shake_tree(
            2, FixedRng(0.01, 3), day=1
        )
        self.assertFalse(ok)
        self.assertIn("이미", message)

        ok, _, key, amount = state.shake_tree(2, FixedRng(0.01, 3), day=2)
        self.assertTrue(ok)
        self.assertEqual((key, amount), ("blueberries", 3))
        self.assertEqual(state.blueberries, 3)
        self.assertEqual(state.trees_shaken, 2)

    def test_golden_blueberry_sells_for_two_hundred_coins(self):
        state = GameState.new(now=100.0)
        state.golden_blueberries = 1
        starting_money = state.money

        ok, message = state.sell_golden_blueberry()

        self.assertTrue(ok)
        self.assertIn("황금 블루베리", message)
        self.assertEqual(state.golden_blueberries, 0)
        self.assertEqual(state.money, starting_money + GOLDEN_BLUEBERRY_PRICE)
        self.assertEqual(state.golden_blueberries_sold, 1)

    def test_special_smoothie_ingredients_add_one_hundred_each(self):
        state = GameState.new(now=100.0)
        order = CustomerOrder(3, 1, 1, 1)
        state.customers_waiting = 1
        state.customer_orders = [order]
        for key, amount in order.recipe.items():
            setattr(state, key, amount)
        state.premium_honey = 1
        state.low_fat_milk = 1
        base_price = state.smoothie_sale_price(order)

        ok, _ = state.make_smoothie(
            order.recipe,
            {"premium_honey": True, "low_fat_milk": True},
        )

        self.assertTrue(ok)
        self.assertEqual(state.premium_honey, 0)
        self.assertEqual(state.low_fat_milk, 0)
        self.assertEqual(state.prepared_bonus, SPECIAL_SMOOTHIE_BONUS * 2)
        self.assertEqual(
            state.smoothie_sale_price(order),
            base_price + SPECIAL_SMOOTHIE_BONUS * 2,
        )
        starting_money = state.money
        ok, _ = state.sell_smoothie()
        self.assertTrue(ok)
        self.assertEqual(
            state.money,
            starting_money + base_price + SPECIAL_SMOOTHIE_BONUS * 2,
        )
        self.assertEqual(state.prepared_bonus, 0)
        self.assertEqual(state.prepared_specials, [])

    def test_missing_special_does_not_consume_regular_recipe(self):
        state = GameState.new(now=100.0)
        order = CustomerOrder(3, 1, 1, 1)
        state.customers_waiting = 1
        state.customer_orders = [order]
        for key, amount in order.recipe.items():
            setattr(state, key, amount)
        before = tuple(state.inventory(key) for key in order.recipe)

        ok, message = state.make_smoothie(
            order.recipe,
            {"premium_honey": True},
        )

        self.assertFalse(ok)
        self.assertIn("고급 꿀", message)
        self.assertEqual(tuple(state.inventory(key) for key in order.recipe), before)

    def test_bag_has_sixteen_slots_with_sixteen_items_per_stack(self):
        state = GameState.new(now=100.0)
        state.blueberries = BAG_SLOT_COUNT * BAG_STACK_SIZE
        state.seeds = state.honey = state.milk = state.ice = 0

        self.assertEqual(state.bag_slots_used, BAG_SLOT_COUNT)
        self.assertEqual(len(state.bag_stacks()), BAG_SLOT_COUNT)
        self.assertTrue(all(amount == BAG_STACK_SIZE for _key, amount in state.bag_stacks()))
        self.assertFalse(state.can_add_to_bag("blueberries", 1))

        state.blueberries -= 1
        self.assertTrue(state.can_add_to_bag("blueberries", 1))
        self.assertFalse(state.can_add_to_bag("blueberries", 2))

    def test_full_bag_blocks_harvest_and_purchase_without_losing_money(self):
        state = GameState.new(now=100.0)
        state.blueberries = BAG_SLOT_COUNT * BAG_STACK_SIZE
        state.seeds = state.honey = state.milk = state.ice = 0
        state.money = 100
        ready_at = state.plots[0].ready_at

        ok, harvest_message = state.harvest(0, now=100.0)
        self.assertFalse(ok)
        self.assertIn("가방", harvest_message)
        self.assertEqual(state.blueberries, BAG_SLOT_COUNT * BAG_STACK_SIZE)
        self.assertEqual(state.plots[0].ready_at, ready_at)

        ok, purchase_message = state.buy_item("honey")
        self.assertFalse(ok)
        self.assertIn("가방", purchase_message)
        self.assertEqual(state.money, 100)
        self.assertEqual(state.honey, 0)

    def test_daily_report_tracks_profit_goal_reward_and_resets_counters(self):
        state = GameState.new(now=100.0)
        state.daily_berries_harvested = 9
        state.daily_money_earned = 75
        state.daily_money_spent = 20
        starting_money = state.money

        report = state.advance_to_day(2)

        self.assertIsNotNone(report)
        self.assertTrue(report["goal_complete"])
        self.assertEqual(report["profit"], 55)
        self.assertEqual(state.money, starting_money + 45)
        self.assertEqual(state.reputation, 3)
        self.assertEqual(state.tracked_day, 2)
        self.assertEqual(state.daily_money_earned, 0)
        self.assertEqual(state.daily_berries_harvested, 0)
        self.assertEqual(state.pending_daily_report, report)

    def test_facilities_unlock_produce_and_upgrade_by_reputation_rank(self):
        state = GameState.new(now=100.0)
        state.money = 50_000
        self.assertEqual(state.facility_build_cost("beehive"), 2_000)
        self.assertEqual(state.facility_build_cost("ice_maker"), 4_000)
        self.assertEqual(state.facility_build_cost("cow_barn"), 7_000)
        ok, _ = state.build_facility("beehive", day=1)
        self.assertTrue(ok)
        self.assertEqual(state.facility_level("beehive"), 1)
        self.assertEqual(state.facility_ready_days["beehive"], 2)
        self.assertEqual(state.daily_money_spent, FACILITY_CONFIG["beehive"]["cost"])

        ok, _ = state.collect_facility("beehive", day=1)
        self.assertFalse(ok)
        ok, _ = state.collect_facility("beehive", day=2)
        self.assertTrue(ok)
        self.assertEqual(state.honey, 2)
        self.assertEqual(state.facility_upgrade_cost("beehive"), 3_500)

        ok, _ = state.upgrade_facility("beehive")
        self.assertFalse(ok)
        state.reputation = 8
        before_money = state.money
        ok, _ = state.upgrade_facility("beehive")
        self.assertTrue(ok)
        self.assertEqual(state.facility_level("beehive"), 2)
        self.assertEqual(state.facility_yield("beehive"), 3)
        self.assertEqual(state.facility_upgrade_cost("beehive"), 6_000)
        self.assertLess(state.money, before_money)

        ok, message = state.build_facility("cow_barn", day=2)
        self.assertFalse(ok)
        self.assertIn("등급 3", message)
        state.reputation = 25
        ok, _ = state.build_facility("cow_barn", day=2)
        self.assertTrue(ok)

    def test_seasons_weather_harvest_and_festival_prices_change(self):
        self.assertEqual(season_for_day(1), ("봄", 1, 1))
        self.assertEqual(season_for_day(1 + DAYS_PER_SEASON)[0], "여름")
        self.assertEqual(season_for_day(1 + DAYS_PER_SEASON * 2)[0], "가을")
        self.assertEqual(season_for_day(1 + DAYS_PER_SEASON * 3)[0], "겨울")
        self.assertEqual(season_for_day(1 + DAYS_PER_SEASON * 4), ("봄", 1, 2))
        self.assertEqual(weather_for_day(2), "rain")

        state = GameState.new(now=100.0)
        state.game_elapsed_seconds = GAME_DAY_SECONDS
        self.assertEqual(state.harvest_yield_for_day(), HARVEST_YIELD + 1)
        winter_day = 1 + DAYS_PER_SEASON * 3
        self.assertEqual(state.raw_blueberry_price(winter_day), RAW_BERRY_PRICE + 2)

        festival_day = DAYS_PER_SEASON * 2
        self.assertTrue(is_blueberry_festival(festival_day))
        state.game_elapsed_seconds = (festival_day - 1) * GAME_DAY_SECONDS
        order = state.make_customer_order(random.Random(7))
        self.assertTrue(order.vip)
        self.assertEqual(
            state.smoothie_sale_price(order),
            (order.price + state.customer_tip(order)) * 2,
        )

    def test_customer_patience_tips_regulars_and_vip_reputation(self):
        state = GameState.new(now=100.0)
        order = CustomerOrder(3, 1, 1, 1, customer_name="민아", vip=True)
        state.customers_waiting = 1
        state.customer_orders = [order]
        fresh_price = state.smoothie_sale_price(order)
        state.tick_customer_wait(30.0)
        self.assertLess(order.satisfaction, 100)
        self.assertLess(state.smoothie_sale_price(order), fresh_price)

        for key, amount in order.recipe.items():
            setattr(state, key, amount)
        ok, _ = state.make_smoothie(order.recipe)
        self.assertTrue(ok)
        reputation_before = state.reputation
        ok, _ = state.sell_smoothie()
        self.assertTrue(ok)
        self.assertGreater(state.reputation, reputation_before)
        self.assertEqual(state.customer_visits["민아"], 1)
        self.assertEqual(state.vip_customers_served, 1)

        state.customer_visits = {name: 1 for name in ("민아", "하늘", "도윤", "수빈", "유진", "지호", "나리", "태오")}
        state.game_elapsed_seconds = 0
        state.reputation = 0
        regular = state.make_customer_order(random.Random(11))
        self.assertTrue(regular.regular)
        self.assertIn("또 왔어요", regular.story)

    def test_customers_leave_the_queue_one_at_a_time(self):
        state = GameState.new(now=100.0)
        state.smoothies = CUSTOMER_QUEUE_SIZE + 1
        for expected_waiting in range(CUSTOMER_QUEUE_SIZE - 1, -1, -1):
            ok, _ = state.sell_smoothie()
            self.assertTrue(ok)
            self.assertEqual(state.customers_waiting, expected_waiting)

        ok, _ = state.sell_smoothie()
        self.assertFalse(ok)
        self.assertEqual(state.smoothies, 1)

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            state = GameState.new(now=100.0)
            state.money = 123
            state.blueberries = 9
            state.game_elapsed_seconds = 123.5
            state.customers_waiting = 2
            state.customer_orders = [
                CustomerOrder(3, 0, 1, 2),
                CustomerOrder(3, 2, 2, 3),
            ]
            state.golden_blueberries = 2
            state.premium_honey = 3
            state.low_fat_milk = 4
            state.tree_shaken_days = {"1": 5}
            state.trees_shaken = 7
            state.plant(1, now=100.0)
            state.save(path)
            loaded = GameState.load(path, now=101.0)
            self.assertEqual(loaded.money, 123)
            self.assertEqual(loaded.blueberries, 9)
            self.assertEqual(loaded.game_elapsed_seconds, 123.5)
            self.assertTrue(loaded.plots[1].planted)
            self.assertEqual(loaded.plots[1].ready_at, 100.0 + GROW_SECONDS)
            self.assertEqual(loaded.customers_waiting, 2)
            self.assertEqual(loaded.customer_orders, state.customer_orders)
            self.assertEqual(loaded.golden_blueberries, 2)
            self.assertEqual(loaded.premium_honey, 3)
            self.assertEqual(loaded.low_fat_milk, 4)
            self.assertEqual(loaded.tree_shaken_days, {"1": 5})
            self.assertEqual(loaded.trees_shaken, 7)

    def test_version_one_save_keeps_progress_and_gains_customer_orders(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            state = GameState.new(now=100.0)
            state.money = 777
            state.smoothies = 2
            data = state.to_dict()
            data["save_version"] = 1
            data.pop("customer_orders")
            data.pop("prepared_order")
            path.write_text(json.dumps(data), encoding="utf-8")

            errors = []
            loaded = GameState.load(path, now=101.0, on_error=errors.append)

            self.assertFalse(errors)
            self.assertEqual(loaded.money, 777)
            self.assertEqual(loaded.smoothies, 2)
            self.assertEqual(len(loaded.customer_orders), CUSTOMER_QUEUE_SIZE)

            order = loaded.current_order
            self.assertIsNotNone(order)
            for key, amount in order.recipe.items():
                setattr(loaded, key, amount)
            ok, _ = loaded.make_smoothie(order.recipe)
            self.assertTrue(ok)
            self.assertEqual(loaded.smoothies, 3)
            ok, _ = loaded.sell_smoothie()
            self.assertTrue(ok)
            self.assertEqual(loaded.smoothies, 2)
            self.assertIsNone(loaded.prepared_order)

    def test_version_two_save_migrates_without_fake_old_daily_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            state = GameState.new(now=100.0)
            state.money = 654
            state.game_elapsed_seconds = GAME_DAY_SECONDS * 8
            data = state.to_dict()
            data["save_version"] = 2
            for key in (
                "reputation", "vip_customers_served", "customer_visits",
                "tracked_day", "daily_berries_harvested",
                "daily_blueberries_sold", "daily_smoothies_sold",
                "daily_money_earned", "daily_money_spent",
                "pending_daily_report", "festival_wins",
                "facility_levels", "facility_ready_days",
                "golden_blueberries", "premium_honey", "low_fat_milk",
                "golden_blueberries_sold", "trees_shaken", "tree_shaken_days",
                "prepared_bonus", "prepared_specials",
            ):
                data.pop(key)
            path.write_text(json.dumps(data), encoding="utf-8")

            loaded = GameState.load(path, now=101.0)

            self.assertEqual(loaded.money, 654)
            self.assertEqual(loaded.current_day, 9)
            self.assertEqual(loaded.tracked_day, 9)
            self.assertIsNone(loaded.pending_daily_report)
            self.assertTrue(all(level == 0 for level in loaded.facility_levels.values()))

    def test_corrupt_save_falls_back_to_new_game(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            path.write_text("{not json", encoding="utf-8")
            errors = []
            state = GameState.load(path, now=200.0, on_error=errors.append)
            self.assertTrue(errors)
            self.assertTrue(state.plots[0].is_ready(200.0))


if __name__ == "__main__":
    unittest.main()
