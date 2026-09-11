import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
import main


class FishingTimingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.save_patch = patch.object(main, 'SAVE_PATH', Path(self.temp.name) / 'test.json')
        self.save_patch.start()
        self.app = main.GameApp()
        self.app.overlay = None
        self.app.player.update(main.POND.left - 25, main.POND.centery)
        self.app.state.fishing_rod = 1
        self.app.state.fishing_rod_durability = 39
        self.app.fishing_bobber = (main.POND.left + 55, main.POND.centery)

    def tearDown(self):
        pygame.quit()
        self.save_patch.stop()
        self.temp.cleanup()

    def prepare_bite(self, phase='waiting'):
        self.app.fishing_phase = phase
        self.app.fishing_bite_at = 100.0
        self.app.fishing_escape_at = 101.5

    def press_e_at(self, now, repeat=False):
        with patch('main.time.time', return_value=now):
            self.app.handle_key(pygame.event.Event(
                pygame.KEYDOWN, key=pygame.K_e, scancode=pygame.KSCAN_E, mod=0, repeat=repeat))

    def test_early_good_late_and_expired_inputs_use_scheduled_timing(self):
        for phase in ('waiting', 'bite'):
            for now, good in ((99.9, False), (100.1, False), (100.25, True),
                              (100.6, True), (101.1, True), (101.11, False), (101.6, False)):
                with self.subTest(phase=phase, now=now):
                    self.prepare_bite(phase)
                    with patch.object(self.app.state, 'catch_fish', return_value=(True, '잡았어요!', 'carp')) as catch:
                        self.press_e_at(now)
                    self.assertEqual(catch.call_count, int(good))
                    self.assertEqual(self.app.fishing_phase, 'idle')
                    self.assertEqual(self.app.toast_error, not good)
                    self.assertEqual(self.app.state.fishing_rod_durability, 39)

    def test_no_key_or_delayed_update_escapes_without_reward(self):
        for phase in ('waiting', 'bite'):
            self.prepare_bite(phase)
            before = self.app.state.to_dict()
            with patch.object(self.app.state, 'catch_fish') as catch:
                self.app.update_fishing_bite(101.5)
            catch.assert_not_called()
            self.assertEqual(self.app.fishing_phase, 'idle')
            self.assertEqual(self.app.state.to_dict(), before)

    def test_bite_starts_splash_once_and_does_not_extend_deadline(self):
        self.prepare_bite()
        self.app.update_fishing_bite(100.1)
        self.assertEqual(self.app.fishing_phase, 'bite')
        self.assertEqual(self.app.fishing_escape_at, 101.5)
        self.assertEqual(len(self.app.particles), 28)
        self.assertEqual(self.app.action_effects[-1].label, '물었다!')
        self.app.update_fishing_bite(100.4)
        self.assertEqual(len(self.app.particles), 28)
        self.assertEqual(self.app.fishing_escape_at, 101.5)

    def test_held_key_repeat_does_not_hook(self):
        self.prepare_bite('bite')
        with patch.object(self.app.state, 'catch_fish') as catch:
            self.press_e_at(100.6, repeat=True)
        catch.assert_not_called()
        self.assertEqual(self.app.fishing_phase, 'bite')

    def test_bite_motion_and_cues_change_over_time(self):
        self.prepare_bite('bite')
        self.app.camera.update(main.POND.centerx - 500, main.POND.centery - 300)
        frames = []
        for elapsed, cue in ((0.1, '기다려요'), (0.6, 'E 지금!'), (1.3, '늦었어요')):
            self.app.screen.fill((0, 0, 0))
            self.app.frame_time = 100 + elapsed
            with patch.object(self.app, 'text', wraps=self.app.text) as text:
                self.app.draw_fishing_line()
            self.assertIn(cue, [call.args[0] for call in text.call_args_list])
            frames.append(pygame.image.tostring(self.app.screen, 'RGB'))
        self.assertEqual(len(set(frames)), 3)
