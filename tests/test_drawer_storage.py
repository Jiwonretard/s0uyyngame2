import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game_state import GameState, BAG_ITEM_KEYS, BAG_STACK_SIZE, DRAWER_SLOT_COUNT


class DrawerTests(unittest.TestCase):
    def ready(self):
        state = GameState.new(now=100)
        state.money = 5000
        for key, col in (("drawer", 0), ("drawer_white", 5)):
            self.assertTrue(state.buy_furniture(key)[0])
            self.assertTrue(state.place_furniture(key, col, 0)[0])
        for key in BAG_ITEM_KEYS:
            setattr(state, key, 0)
        return state

    def test_stack_transfers_separate_drawers_and_capacity_are_atomic(self):
        state = self.ready()
        state.blueberries = 32
        self.assertTrue(state.transfer_drawer("drawer", "blueberries", 16, deposit=True)[0])
        self.assertTrue(state.transfer_drawer("drawer_white", "blueberries", 1, deposit=True)[0])
        self.assertEqual(state.blueberries, 15)
        self.assertEqual(state.drawer_stacks("drawer"), [("blueberries", 16)])
        self.assertEqual(state.drawer_stacks("drawer_white"), [("blueberries", 1)])
        self.assertTrue(state.transfer_drawer("drawer", "blueberries", 1, deposit=False)[0])
        state.drawer_contents["drawer"] = {"honey": DRAWER_SLOT_COUNT * BAG_STACK_SIZE}
        state.honey = 1
        before = state.to_dict()
        self.assertFalse(state.transfer_drawer("drawer", "honey", 1, deposit=True)[0])
        self.assertEqual(state.to_dict(), before)
        state.seeds = 16 * 14
        # berries 16, honey 1, seeds 224: all 16 bag slots used.
        before = state.to_dict()
        self.assertFalse(state.transfer_drawer("drawer", "honey", 16, deposit=False)[0])
        self.assertEqual(state.to_dict(), before)
        self.assertTrue(state.transfer_drawer("drawer", "honey", 1, deposit=False)[0])
        self.assertEqual(state.honey, 2)

    def test_invalid_transfers_and_unplaced_drawers_keep_inventory(self):
        state = self.ready()
        state.blueberries = 5
        for key, amount in (("money", 1), ("blueberries", -1), ("blueberries", 6), ("blueberries", 1.5)):
            before = state.to_dict()
            self.assertFalse(state.transfer_drawer("drawer", key, amount, deposit=True)[0])
            self.assertEqual(state.to_dict(), before)
        state.store_furniture("drawer")
        self.assertFalse(state.transfer_drawer("drawer", "blueberries", 1, deposit=True)[0])

    def test_contents_and_rod_durability_survive_saving_and_furniture_storage(self):
        state = self.ready()
        state.fishing_rod, state.fishing_rod_durability = 1, 17
        state.premium_honey = 7
        self.assertTrue(state.transfer_drawer("drawer", "fishing_rod", 1, deposit=True)[0])
        self.assertTrue(state.transfer_drawer("drawer", "premium_honey", 7, deposit=True)[0])
        self.assertEqual((state.fishing_rod, state.fishing_rod_durability), (0, 0))
        self.assertFalse(state.buy_fishing_rod()[0])
        state.store_furniture("drawer")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "save.json"
            state.save(path)
            loaded = GameState.load(path, now=101)
            self.assertEqual(loaded.drawer_contents, state.drawer_contents)
            self.assertEqual(loaded.drawer_rod_durability, {"drawer": 17})
            self.assertTrue(loaded.place_furniture("drawer", 0, 0)[0])
            self.assertTrue(loaded.transfer_drawer("drawer", "fishing_rod", 1, deposit=False)[0])
            self.assertEqual((loaded.fishing_rod, loaded.fishing_rod_durability), (1, 17))
            self.assertTrue(loaded.transfer_drawer("drawer", "premium_honey", 7, deposit=False)[0])
            self.assertEqual(loaded.premium_honey, 7)
            data = json.loads(path.read_text())
            data.pop("drawer_contents")
            data.pop("drawer_rod_durability")
            path.write_text(json.dumps(data))
            self.assertEqual(GameState.load(path).drawer_contents, {})
