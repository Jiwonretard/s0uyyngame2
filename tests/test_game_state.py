import json
import tempfile
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game_state import (  # noqa: E402
    CUSTOMER_QUEUE_SIZE,
    CustomerOrder,
    GROW_SECONDS,
    HARVEST_YIELD,
    LAND_BASE_COST,
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
        self.assertGreater(state.land_cost, first_cost)

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
