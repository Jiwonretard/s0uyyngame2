import tempfile
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game_state import (  # noqa: E402
    GROW_SECONDS,
    HARVEST_YIELD,
    RAW_BERRY_PRICE,
    REGROW_SECONDS,
    SMOOTHIE_PRICE,
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
        state.blueberries = 3
        state.honey = state.milk = state.ice = 1
        starting_money = state.money
        ok, _ = state.make_smoothie()
        self.assertTrue(ok)
        self.assertEqual(state.smoothies, 1)
        self.assertEqual((state.blueberries, state.honey, state.milk, state.ice), (0, 0, 0, 0))
        ok, _ = state.sell_smoothie()
        self.assertTrue(ok)
        self.assertEqual(state.smoothies, 0)
        self.assertEqual(state.money, starting_money + SMOOTHIE_PRICE)
        self.assertEqual(state.smoothies_sold, 1)

    def test_raw_berry_sale_and_land_price_progression(self):
        state = GameState.new(now=100.0)
        state.blueberries = 1
        starting_money = state.money
        ok, _ = state.sell_blueberry()
        self.assertTrue(ok)
        self.assertEqual(state.money, starting_money + RAW_BERRY_PRICE)
        first_cost = state.land_cost
        state.money = first_cost
        ok, _ = state.buy_land()
        self.assertTrue(ok)
        self.assertEqual(state.money, 0)
        self.assertGreater(state.land_cost, first_cost)

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            state = GameState.new(now=100.0)
            state.money = 123
            state.blueberries = 9
            state.plant(1, now=100.0)
            state.save(path)
            loaded = GameState.load(path, now=101.0)
            self.assertEqual(loaded.money, 123)
            self.assertEqual(loaded.blueberries, 9)
            self.assertTrue(loaded.plots[1].planted)
            self.assertEqual(loaded.plots[1].ready_at, 100.0 + GROW_SECONDS)

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
