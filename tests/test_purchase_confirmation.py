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
import purchase_ui
import wardrobe_ui
from game_state import GameState


class PurchaseConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.save_path = Path(self.temp.name) / 'save.json'
        self.save_patch = patch.object(main, 'SAVE_PATH', self.save_path)
        self.save_patch.start()
        self.app = main.GameApp()
        self.app.overlay = 'home'
        self.app.state.money = 10000

    def tearDown(self):
        pygame.quit()
        self.save_patch.stop()
        self.temp.cleanup()

    def key(self, key):
        self.app.handle_key(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0))

    def wardrobe(self):
        self.app.state.buy_furniture('wardrobe')
        self.app.state.place_furniture('wardrobe', 0, 0)
        self.app.open_wardrobe()

    def test_furniture_cancel_and_confirmation_save_once(self):
        self.key(pygame.K_1)
        self.assertIsNotNone(self.app.pending_purchase)
        self.assertEqual(self.app.state.money, 10000)
        self.assertNotIn('bed', self.app.state.furniture_owned)
        # Enter defaults to cancel, without closing the home.
        self.key(pygame.K_RETURN)
        self.assertIsNone(self.app.pending_purchase)
        self.assertEqual(self.app.overlay, 'home')
        self.assertEqual(self.app.state.money, 10000)
        self.key(pygame.K_1)
        self.app.handle_click(purchase_ui.BUY_BUTTON.center)
        self.assertEqual(self.app.state.money, 7000)
        self.assertIn('bed', self.app.state.furniture_owned)
        self.assertEqual(GameState.load(self.save_path).money, 7000)
        self.app.finish_purchase_confirmation(True)
        self.assertEqual(self.app.state.money, 7000)

    def test_modal_blocks_home_controls_and_background_clicks(self):
        self.app.buy_furniture('bed')
        self.key(pygame.K_g)
        self.key(pygame.K_h)
        self.app.handle_click(main.HOME_EXIT_BUTTON.center)
        self.assertFalse(self.app.home_edit_mode)
        self.assertEqual(self.app.overlay, 'home')
        self.assertIsNotNone(self.app.pending_purchase)
        self.app.handle_click(purchase_ui.CANCEL_BUTTON.center)
        self.assertEqual(self.app.state.money, 10000)

    def test_insufficient_balance_cannot_buy(self):
        self.app.buy_furniture('bed')
        self.app.state.money = 2999
        self.key(pygame.K_y)
        self.assertEqual(self.app.state.money, 2999)
        self.assertNotIn('bed', self.app.state.furniture_owned)
        self.assertTrue(self.app.toast_error)

    def test_cosmetic_cancel_purchase_and_owned_equipment(self):
        self.wardrobe()
        self.app.wardrobe_category = 'outfit'
        before = self.app.state.money
        self.app.apply_wardrobe_option('blueberry')
        self.assertEqual(self.app.state.money, before)
        self.assertFalse(self.app.state.owns_cosmetic('outfit', 'blueberry'))
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.overlay, 'wardrobe')
        self.app.apply_wardrobe_option('blueberry')
        self.key(pygame.K_y)
        self.assertEqual(self.app.state.money, before - 1600)
        self.assertEqual(self.app.state.appearance['outfit'], 'blueberry')
        self.app.apply_wardrobe_option('classic')
        self.assertIsNone(self.app.pending_purchase)
        self.assertEqual(self.app.state.appearance['outfit'], 'classic')
        self.assertEqual(self.app.state.money, before - 1600)

    def test_partial_theme_price_and_confirmation(self):
        self.wardrobe()
        self.app.state.buy_cosmetic('outfit', 'whale')
        before = self.app.state.money
        self.app.handle_click(wardrobe_ui.WHALE_RECT.center)
        self.assertEqual(self.app.pending_purchase.price, 3600)
        self.assertEqual(self.app.state.money, before)
        # Default cancel can be switched to buy using a keyboard.
        self.key(pygame.K_LEFT)
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.state.money, before - 3600)
        self.assertTrue(self.app.state.owns_theme('whale'))
        self.assertEqual(self.app.state.appearance['outfit'], 'whale')

    def test_confirmation_draws_price_and_remaining_balance(self):
        self.app.buy_furniture('bed')
        with patch.object(self.app, 'text', wraps=self.app.text) as draw_text:
            self.app.draw()
        labels = [call.args[0] for call in draw_text.call_args_list]
        self.assertIn('정말 구매할까요?', labels)
        self.assertIn('가격 3,000벨리', labels)
        self.assertIn('보유 10,000벨리 · 구매 후 7,000벨리', labels)
