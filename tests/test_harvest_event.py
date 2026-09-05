import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame  # noqa: E402
import main  # noqa: E402
from game_state import CustomerOrder  # noqa: E402


class HarvestEventTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.original_save_path = main.SAVE_PATH
        main.SAVE_PATH = Path(self.temp_directory.name) / "save.json"
        self.app = main.GameApp()
        self.app.overlay = None
        self.app.player.update(360, 380)

    def tearDown(self):
        pygame.quit()
        main.SAVE_PATH = self.original_save_path
        self.temp_directory.cleanup()

    def test_e_key_harvests_and_creates_visible_impact(self):
        before = self.app.state.blueberries
        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_e,
            scancode=pygame.KSCAN_E,
            mod=0,
        )
        self.app.handle_key(event)
        self.assertEqual(self.app.state.blueberries, before + 4)
        self.assertGreaterEqual(len(self.app.particles), 30)
        self.assertTrue(self.app.action_effects)
        self.assertGreater(self.app.impact_timer, 0)

    def test_physical_e_scancode_works_with_non_latin_input(self):
        before = self.app.state.blueberries
        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=0,
            scancode=pygame.KSCAN_E,
            mod=0,
        )
        self.app.handle_key(event)
        self.assertEqual(self.app.state.blueberries, before + 4)

    def test_photo_character_sheet_has_all_movement_frames(self):
        self.assertEqual(self.app.player_sprite_error, "")
        self.assertEqual(set(self.app.player_frames), {"down", "left", "right", "up"})
        self.assertTrue(all(len(frames) == 3 for frames in self.app.player_frames.values()))
        self.assertTrue(
            all(frame.get_flags() & pygame.SRCALPHA for frames in self.app.player_frames.values()
                for frame in frames)
        )

    def test_world_draw_does_not_resize_transparent_surfaces(self):
        with patch("pygame.transform.scale", side_effect=AssertionError("unexpected resize")):
            self.app.draw()

    def test_e_at_blender_opens_manual_mixing_before_creating_smoothie(self):
        order = CustomerOrder(3, 2, 1, 2)
        self.app.state.customers_waiting = 1
        self.app.state.customer_orders = [order]
        self.app.state.blueberries = order.blueberries
        self.app.state.honey = order.honey
        self.app.state.milk = order.milk
        self.app.state.ice = order.ice
        self.app.player.update(main.CAFE.centerx, main.CAFE.bottom + 42)

        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_e,
            scancode=pygame.KSCAN_E,
            mod=0,
        )
        self.app.handle_key(event)

        self.assertEqual(self.app.overlay, "blender")
        self.assertEqual(self.app.state.smoothies, 0)
        self.assertTrue(all(amount == 0 for amount in self.app.blender_mix.values()))

        for rect, key, _label, _color in self.app.blender_cards:
            plus = pygame.Rect(rect.x + 268, rect.y + 57, 40, 40)
            for _ in range(order.recipe[key]):
                self.app.handle_click(plus.center)
        self.app.handle_click(pygame.Rect(440, 550, 300, 56).center)

        self.assertEqual(self.app.overlay, "blending")
        self.assertEqual(self.app.blender_animation_remaining, main.BLENDER_DURATION)
        self.assertEqual(self.app.state.smoothies, 1)
        self.assertEqual(self.app.state.prepared_order, order)
        self.assertEqual(
            (self.app.state.blueberries, self.app.state.honey,
             self.app.state.milk, self.app.state.ice),
            (0, 0, 0, 0),
        )
        self.app.update(main.BLENDER_DURATION - 0.05)
        self.assertEqual(self.app.overlay, "blending")
        self.app.update(0.06)
        self.assertIsNone(self.app.overlay)
        self.assertTrue(self.app.particles)

    def test_calendar_uses_active_play_time_and_pauses_in_menus(self):
        self.app.state.started_at = -1_000_000.0
        self.app.state.game_elapsed_seconds = 0.0
        self.assertEqual(self.app.game_clock()[:3], (1, 6, 0))

        self.app.overlay = None
        self.app.update(12.0)
        self.assertEqual(self.app.state.game_elapsed_seconds, 12.0)
        self.app.overlay = "shop"
        self.app.update(100.0)
        self.assertEqual(self.app.state.game_elapsed_seconds, 12.0)

        self.app.state.game_elapsed_seconds = main.DAY_SECONDS / 2
        self.assertEqual(self.app.game_clock()[:3], (1, 14, 0))
        self.app.state.game_elapsed_seconds = main.DAY_SECONDS
        self.assertEqual(self.app.game_clock()[:3], (2, 6, 0))


if __name__ == "__main__":
    unittest.main()
