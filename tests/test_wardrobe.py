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
from dressup import build_frames, character_surface
from wardrobe_catalog import DEFAULT_LOOK, OPTIONS, OUTFITS, THEME_SETS


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
        for category, options in OPTIONS.items():
            for key in options:
                self.assertTrue(state.equip_cosmetic(category, key))
                self.assertEqual(state.appearance[category], key)
        state.equip_cosmetic("hair", "silver")
        for theme, pieces in THEME_SETS.items():
            self.assertTrue(state.equip_theme(theme))
            for category, key in pieces.items():
                self.assertEqual(state.appearance[category], key)
            self.assertEqual(state.appearance["hair"], "silver")

    def test_appearance_save_legacy_and_invalid_values(self):
        state = self.ready_state()
        state.equip_theme("blueberry")
        state.equip_cosmetic("hair", "lavender")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "save.json"
            state.save(path)
            loaded = GameState.load(path, now=101)
            self.assertEqual(loaded.appearance, state.appearance)
            self.assertTrue(loaded.wardrobe_available)
            data = json.loads(path.read_text())
            del data["appearance"]
            path.write_text(json.dumps(data))
            self.assertEqual(GameState.load(path, now=102).appearance, {})
            data["appearance"] = {"hair": [], "outfit": "removed"}
            path.write_text(json.dumps(data))
            loaded = GameState.load(path, now=102)
            self.assertEqual(loaded.appearance, DEFAULT_LOOK)
            self.assertTrue(loaded.wardrobe_available)

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
