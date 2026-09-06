import audioop
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
import wave


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame  # noqa: E402
import main  # noqa: E402


class RecordingChannel:
    def __init__(self) -> None:
        self.play_count = 0

    def get_busy(self) -> bool:
        return False

    def play(self, _sound: object) -> None:
        self.play_count += 1


class SaleAudioTests(unittest.TestCase):
    def test_blender_grinding_sound_covers_the_full_three_second_animation(self):
        with wave.open(str(main.BLENDER_SOUND_PATH), "rb") as sound:
            duration = sound.getnframes() / sound.getframerate()
            self.assertEqual(sound.getframerate(), 44_100)
            self.assertEqual(sound.getnchannels(), 2)
            self.assertGreaterEqual(duration, main.BLENDER_DURATION)
            samples = sound.readframes(sound.getnframes())
            self.assertGreater(audioop.max(samples, sound.getsampwidth()), 2_000)

    def test_audio_keeps_original_and_extra_leading_preroll(self):
        with wave.open(str(main.SALE_SOUND_PATH), "rb") as sound:
            self.assertEqual(sound.getframerate(), 44_100)
            self.assertEqual(sound.getnchannels(), 2)
            self.assertGreaterEqual(sound.getnframes() / sound.getframerate(), 5.32)

            leading_audio = sound.readframes(round(sound.getframerate() * 0.92))
            self.assertLessEqual(audioop.max(leading_audio, sound.getsampwidth()), 8)

            audible_audio = sound.readframes(round(sound.getframerate() * 0.8))
            self.assertGreater(audioop.max(audible_audio, sound.getsampwidth()), 500)

    def test_one_successful_customer_sale_plays_the_sound_once(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            original_save_path = main.SAVE_PATH
            main.SAVE_PATH = Path(temp_directory) / "save.json"
            try:
                app = main.GameApp()
                app.overlay = None
                app.state.smoothies = 1
                app.player.update(
                    main.SMOOTHIE_CART.centerx,
                    main.SMOOTHIE_CART.bottom + 38,
                )
                channel = RecordingChannel()
                app.sale_sound = object()
                app.sale_channel = channel

                app.interact()

                self.assertEqual(app.state.smoothies, 0)
                self.assertEqual(app.state.customers_waiting, main.CUSTOMER_QUEUE_SIZE - 1)
                self.assertEqual(channel.play_count, 1)
                self.assertEqual(len(app.departing_customers), 1)
                self.assertLessEqual(app.current_bgm_volume, main.BGM_DUCK_VOLUME)
                self.assertGreater(app.bgm_duck_until, time.time())
                app.bgm_duck_until = 0
                app.update(1.0)
                self.assertAlmostEqual(app.current_bgm_volume, main.BGM_NORMAL_VOLUME)
            finally:
                pygame.quit()
                main.SAVE_PATH = original_save_path

    def test_original_background_music_loads_and_loops(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            original_save_path = main.SAVE_PATH
            main.SAVE_PATH = Path(temp_directory) / "save.json"
            try:
                app = main.GameApp()
                self.assertEqual(app.music_error, "")
                music = pygame.mixer.Sound(str(main.BGM_PATH))
                self.assertGreaterEqual(music.get_length(), 38.3)
                self.assertTrue(pygame.mixer.music.get_busy())
            finally:
                pygame.quit()
                main.SAVE_PATH = original_save_path

    def test_new_customer_joins_after_the_queue_timer(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            original_save_path = main.SAVE_PATH
            main.SAVE_PATH = Path(temp_directory) / "save.json"
            try:
                app = main.GameApp()
                app.overlay = None
                app.state.customers_waiting = 0
                app.next_customer_at = 0

                app.update(0.01)

                self.assertEqual(app.state.customers_waiting, 1)
                self.assertEqual(len(app.state.customer_orders), 1)
                self.assertIsNotNone(app.state.current_order)
                self.assertEqual(len(main.CUSTOMER_QUEUE_POINTS), main.CUSTOMER_QUEUE_SIZE)
            finally:
                pygame.quit()
                main.SAVE_PATH = original_save_path


if __name__ == "__main__":
    unittest.main()
