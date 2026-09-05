import json
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
    GROW_SECONDS,
    HARVEST_YIELD,
    LAND_BASE_COST,
    LAND_COST_STEP,
    RAW_BERRY_PRICE,
    REGROW_SECONDS,
    GameState,
)


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
        ok, _ = state.sell_smoothie()
        self.assertTrue(ok)
        self.assertEqual(state.smoothies, 0)
        self.assertEqual(state.money, starting_money + order.price)
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
