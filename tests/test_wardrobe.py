import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from game_state import GameState
from dressup import SKIN, build_frames, character_surface, product_surface
from wardrobe_catalog import (
    COSMETIC_PRICES,
    DEFAULT_LOOK,
    DEFAULT_OWNED_COSMETICS,
    OPTIONS,
    OUTFITS,
    THEME_SETS,
    cosmetic_id,
    theme_price,
)


class WardrobeTests(unittest.TestCase):
    def ready_state(self):
        state = GameState.new(now=100)
        state.money = 1500
        self.assertTrue(state.buy_furniture("wardrobe")[0])
        self.assertEqual(state.money, 0)
        self.assertTrue(state.place_furniture("wardrobe", 0, 0)[0])
        return state

    def test_equipment_requires_owned_and_placed_wardrobe(self):
        state = GameState.new(now=100)
        self.assertFalse(state.equip_theme("whale"))
        state.money = 1500
        state.buy_furniture("wardrobe")
        self.assertFalse(state.equip_cosmetic("hair", "blonde"))
        state.place_furniture("wardrobe", 0, 0)
        self.assertFalse(state.equip_cosmetic("hair", "blonde"))
        state.money = 700
        self.assertTrue(state.buy_cosmetic("hair", "blonde")[0])
        self.assertTrue(state.equip_cosmetic("hair", "blonde"))
        self.assertFalse(state.equip_cosmetic("hair", "invalid"))
        self.assertFalse(state.equip_cosmetic("invalid", "black"))
        self.assertFalse(state.equip_theme("invalid"))
        state.store_furniture("wardrobe")
        self.assertFalse(state.equip_theme("whale"))
        self.assertEqual(state.appearance["hair"], "blonde")

    def test_twelve_outfits_accessories_and_theme_sets(self):
        state = self.ready_state()
        self.assertEqual(len(OUTFITS), 12)
        self.assertEqual(set(state.owned_cosmetics), set(DEFAULT_OWNED_COSMETICS))
        state.money = 100000
        for category, options in OPTIONS.items():
            for key in options:
                if not state.owns_cosmetic(category, key):
                    before = state.money
                    self.assertTrue(state.buy_cosmetic(category, key)[0])
                    self.assertEqual(before - state.money, COSMETIC_PRICES[category][key])
                self.assertTrue(state.equip_cosmetic(category, key))
                self.assertEqual(state.appearance[category], key)
        state.equip_cosmetic("hair", "silver")
        for theme, pieces in THEME_SETS.items():
            self.assertTrue(state.equip_theme(theme))
            for category, key in pieces.items():
                self.assertEqual(state.appearance[category], key)
            self.assertEqual(state.appearance["hair"], "silver")

    def test_signature_items_cost_over_one_thousand_and_sets_buy_missing_parts(self):
        for theme, pieces in THEME_SETS.items():
            for category, key in pieces.items():
                self.assertGreaterEqual(COSMETIC_PRICES[category][key], 1000, (theme, category))
        state = self.ready_state()
        blueberry_cost = theme_price("blueberry", state.owned_cosmetics)
        self.assertEqual(blueberry_cost, 4950)
        state.money = blueberry_cost - 1
        self.assertFalse(state.buy_theme("blueberry")[0])
        state.money += 1
        self.assertTrue(state.buy_theme("blueberry")[0])
        self.assertEqual(state.money, 0)
        self.assertTrue(state.owns_theme("blueberry"))
        self.assertTrue(state.equip_theme("blueberry"))
        self.assertEqual(state.appearance["outfit"], "blueberry")

    def test_buying_one_theme_part_reduces_set_price(self):
        state = self.ready_state()
        state.money = 10000
        self.assertTrue(state.buy_cosmetic("outfit", "whale")[0])
        self.assertEqual(theme_price("whale", state.owned_cosmetics), 3600)
        self.assertTrue(state.buy_theme("whale")[0])
        self.assertEqual(state.money, 4600)
        self.assertEqual(state.daily_money_spent, 1500 + 5400)

    def test_appearance_save_legacy_and_invalid_values(self):
        state = self.ready_state()
        state.money = 10000
        state.buy_theme("blueberry")
        state.equip_theme("blueberry")
        state.buy_cosmetic("hair", "lavender")
        state.equip_cosmetic("hair", "lavender")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "save.json"
            state.save(path)
            loaded = GameState.load(path, now=101)
            self.assertEqual(loaded.appearance, state.appearance)
            self.assertEqual(loaded.owned_cosmetics, state.owned_cosmetics)
            self.assertTrue(loaded.wardrobe_available)
            data = json.loads(path.read_text())
            del data["appearance"]
            path.write_text(json.dumps(data))
            self.assertEqual(GameState.load(path, now=102).appearance, {})
            data["appearance"] = {"hair": [], "outfit": "removed"}
            data["owned_cosmetics"] = ["bad", [], cosmetic_id("shoes", "pink")]
            path.write_text(json.dumps(data))
            loaded = GameState.load(path, now=102)
            self.assertEqual(loaded.appearance, DEFAULT_LOOK)
            self.assertEqual(
                set(loaded.owned_cosmetics),
                {*DEFAULT_OWNED_COSMETICS, cosmetic_id("shoes", "pink")},
            )
            self.assertTrue(loaded.wardrobe_available)

    def test_old_save_grandfathers_equipped_cosmetics(self):
        state = self.ready_state()
        state.appearance = {**DEFAULT_LOOK, **THEME_SETS["whale"]}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "save.json"
            state.save(path)
            data = json.loads(path.read_text())
            del data["owned_cosmetics"]
            path.write_text(json.dumps(data))
            loaded = GameState.load(path, now=101)
            self.assertTrue(loaded.owns_theme("whale"))
            self.assertTrue(loaded.equip_theme("whale"))

    def test_all_outfits_animate_in_four_directions(self):
        for key in OUTFITS:
            frames = build_frames({"outfit": key})
            self.assertEqual(len(frames), 4)
            for direction, poses in frames.items():
                self.assertEqual(len(poses), 3)
                pixels = {pygame.image.tostring(frame, "RGBA") for frame in poses}
                self.assertEqual(len(pixels), 3, (key, direction))
                self.assertEqual(poses[0].get_size(), (96, 120))
        base = pygame.image.tostring(character_surface(DEFAULT_LOOK), "RGBA")
        for category, options in OPTIONS.items():
            for key in options:
                if key != DEFAULT_LOOK[category]:
                    alternate = character_surface({category: key})
                    self.assertTrue(base != pygame.image.tostring(alternate, "RGBA"), (category, key))

    def test_store_cards_show_products_without_character_bodies(self):
        for category, options in OPTIONS.items():
            products = []
            for key in options:
                icon = product_surface(category, key)
                self.assertEqual(icon.get_size(), (96, 80))
                self.assertGreater(icon.get_bounding_rect().width, 0)
                self.assertNotIn(SKIN, {icon.get_at((x, y))[:3] for x in range(icon.get_width()) for y in range(icon.get_height())})
                products.append(pygame.image.tostring(icon, "RGBA"))
            self.assertEqual(len(products), len(set(products)), category)
