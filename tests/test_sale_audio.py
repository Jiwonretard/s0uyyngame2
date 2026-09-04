import audioop
import os
from pathlib import Path
import sys
import tempfile
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
    def test_audio_keeps_the_original_leading_preroll(self):
        with wave.open(str(main.SALE_SOUND_PATH), "rb") as sound:
            self.assertEqual(sound.getframerate(), 44_100)
            self.assertEqual(sound.getnchannels(), 2)
            self.assertGreaterEqual(sound.getnframes() / sound.getframerate(), 4.82)

            leading_audio = sound.readframes(round(sound.getframerate() * 0.42))
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
                self.assertEqual(len(main.CUSTOMER_QUEUE_POINTS), main.CUSTOMER_QUEUE_SIZE)
            finally:
                pygame.quit()
                main.SAVE_PATH = original_save_path


if __name__ == "__main__":
    unittest.main()
