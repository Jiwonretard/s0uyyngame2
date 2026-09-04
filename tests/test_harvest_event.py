import os
from pathlib import Path
import sys
import tempfile
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame  # noqa: E402
import main  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
