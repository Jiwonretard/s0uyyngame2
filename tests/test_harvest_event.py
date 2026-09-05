import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame  # noqa: E402
import main  # noqa: E402
from game_state import CustomerOrder, GOLDEN_BLUEBERRY_PRICE, GameState  # noqa: E402


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

    def test_tree_shake_drops_item_once_per_game_day_with_visible_impact(self):
        self.app.rng = Mock()
        self.app.rng.random.return_value = 0.94
        self.app.rng.randint.return_value = 0
        self.app.rng.uniform.side_effect = lambda start, end: (start + end) / 2
        tree_index = 0
        self.app.player.update(*main.TREE_POSITIONS[tree_index])
        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_e,
            scancode=pygame.KSCAN_E,
            mod=0,
        )

        self.app.handle_key(event)

        self.assertEqual(self.app.state.premium_honey, 1)
        self.assertEqual(self.app.state.trees_shaken, 1)
        self.assertTrue(self.app.state.tree_shaken_today(tree_index))
        self.assertEqual(len(self.app.tree_drops), 1)
        self.assertGreater(self.app.tree_shake_timers[tree_index], 0)
        self.app.draw()

        self.app.handle_key(event)
        self.assertEqual(self.app.state.premium_honey, 1)
        self.assertEqual(self.app.state.trees_shaken, 1)

    def test_northern_trees_are_fully_visible_below_hud_when_approached(self):
        top_tree = main.TREE_POSITIONS[3]
        self.app.player.update(*top_tree)
        self.app._snap_camera()
        _screen_x, screen_y = self.app.world_to_screen(top_tree)

        # draw_tree reaches 104 pixels above its world anchor. The HUD ends
        # around y=98, so leave a little visible gap instead of hiding foliage.
        self.assertGreaterEqual(screen_y - 104, 105)
        self.assertLess(self.app.camera.y, 0)
        self.assertFalse(self.app._collides(0, 0))
        self.app.draw()

    def test_roof_detail_lines_stay_inside_sloped_edges(self):
        rect = pygame.Rect(120, 170, 440, 250)
        widths = []
        apex_y = rect.top - 82
        base_y = rect.top + 43
        full_half_width = rect.width / 2 + 28

        for row in range(4):
            start, end = main.roof_detail_segment(rect, row)
            self.assertEqual(start[1], end[1])
            progress = (start[1] - apex_y) / (base_y - apex_y)
            edge_half_width = full_half_width * progress
            self.assertGreater(start[0], rect.centerx - edge_half_width)
            self.assertLess(end[0], rect.centerx + edge_half_width)
            widths.append(end[0] - start[0])

        self.assertEqual(widths, sorted(widths, reverse=True))

    def test_shop_name_is_shortened_to_shop(self):
        self.app.player.update(main.SHOP.centerx, main.SHOP.bottom + 42)
        target = self.app.nearest_interaction()
        self.assertIsNotNone(target)
        self.assertEqual(target["kind"], "shop")
        self.assertEqual(target["prompt"], "상점 들어가기")

        with patch.object(self.app, "draw_house") as draw_house:
            self.app.draw_world()
        titles = [call.args[1] for call in draw_house.call_args_list]
        self.assertIn("상점", titles)
        self.assertNotIn("꿀 · 우유 · 얼음 상점", titles)

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

    def test_user_ingredient_icons_are_extracted_with_transparent_backgrounds(self):
        expected = {"milk", "blueberries", "ice", "honey"}
        self.assertEqual(self.app.ingredient_icon_error, "")
        self.assertEqual(set(self.app.ingredient_icons), expected)
        self.assertEqual(set(self.app.ingredient_icons_small), expected)
        for icon in self.app.ingredient_icons.values():
            self.assertTrue(icon.get_flags() & pygame.SRCALPHA)
            self.assertEqual(icon.get_at((0, 0)).a, 0)
            self.assertGreater(pygame.mask.from_surface(icon).count(), 100)
        self.assertGreater(self.app.ingredient_icons["milk"].get_at((29, 29)).a, 0)

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

    def test_blender_special_buttons_consume_items_and_add_bonus(self):
        order = CustomerOrder(3, 1, 1, 1)
        self.app.state.customers_waiting = 1
        self.app.state.customer_orders = [order]
        for key, amount in order.recipe.items():
            setattr(self.app.state, key, amount)
        self.app.state.premium_honey = 1
        self.app.state.low_fat_milk = 1
        self.app.player.update(main.CAFE.centerx, main.CAFE.bottom + 42)
        interact = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_e,
            scancode=pygame.KSCAN_E,
            mod=0,
        )
        self.app.handle_key(interact)
        self.assertEqual(self.app.overlay, "blender")

        for rect, key, _label, _color in self.app.blender_cards:
            plus = pygame.Rect(rect.x + 268, rect.y + 57, 40, 40)
            for _ in range(order.recipe[key]):
                self.app.handle_click(plus.center)
        for special_key in ("premium_honey", "low_fat_milk"):
            self.app.handle_click(self.app.blender_special_button(special_key).center)
        self.app.draw()
        self.app.handle_click(pygame.Rect(440, 550, 300, 56).center)

        self.assertEqual(self.app.overlay, "blending")
        self.assertEqual(self.app.state.prepared_bonus, 200)
        self.assertEqual(self.app.state.premium_honey, 0)
        self.assertEqual(self.app.state.low_fat_milk, 0)
        self.app.draw()

    def test_market_overlay_sells_golden_blueberry_for_two_hundred(self):
        self.app.state.golden_blueberries = 1
        self.app.player.update(main.MARKET.centerx, main.MARKET.bottom + 38)
        interact = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_e,
            scancode=pygame.KSCAN_E,
            mod=0,
        )
        self.app.handle_key(interact)
        self.assertEqual(self.app.overlay, "market")
        self.app.draw()
        starting_money = self.app.state.money

        sell = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_2,
            scancode=pygame.KSCAN_2,
            mod=0,
        )
        self.app.handle_key(sell)

        self.assertEqual(self.app.state.golden_blueberries, 0)
        self.assertEqual(self.app.state.money, starting_money + GOLDEN_BLUEBERRY_PRICE)

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

    def test_app_save_restores_exact_day_and_progress(self):
        self.assertEqual(main.DAY_SECONDS, 24 * 60)
        self.assertEqual(main.AUTOSAVE_SECONDS, 5.0)
        self.app.state.game_elapsed_seconds = main.DAY_SECONDS * 3.4
        self.app.state.tracked_day = 4

        self.app.save()
        loaded = GameState.load(main.SAVE_PATH)

        self.assertEqual(loaded.current_day, 4)
        self.assertEqual(loaded.tracked_day, 4)
        self.assertAlmostEqual(
            loaded.game_elapsed_seconds,
            main.DAY_SECONDS * 3.4,
        )

    def test_b_key_opens_four_by_four_bag_and_e_closes_it(self):
        self.app.state.blueberries = 17
        self.app.state.seeds = 1
        self.app.state.honey = self.app.state.milk = self.app.state.ice = 0
        open_event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_b,
            scancode=pygame.KSCAN_B,
            mod=0,
        )
        self.app.handle_key(open_event)

        self.assertEqual(self.app.overlay, "bag")
        self.assertEqual(main.BAG_COLUMNS * main.BAG_ROWS, 16)
        self.assertEqual(
            self.app.state.bag_stacks(),
            [("blueberries", 16), ("blueberries", 1), ("seeds", 1)],
        )
        self.app.draw()

        close_event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_e,
            scancode=pygame.KSCAN_E,
            mod=0,
        )
        self.app.handle_key(close_event)
        self.assertIsNone(self.app.overlay)

    def test_physical_b_scancode_opens_bag_with_non_latin_input(self):
        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=0,
            scancode=pygame.KSCAN_B,
            mod=0,
        )

        self.app.handle_key(event)

        self.assertEqual(self.app.overlay, "bag")

    def test_facility_can_be_built_and_collected_from_world_interaction(self):
        self.app.state.money = 10_000
        self.app.state.reputation = 0
        self.app.player.update(main.BEEHIVE.centerx, main.BEEHIVE.bottom + 38)
        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_e,
            scancode=pygame.KSCAN_E,
            mod=0,
        )

        self.app.handle_key(event)
        self.assertEqual(self.app.overlay, "facility")
        self.assertEqual(self.app.selected_facility, "beehive")
        self.app.handle_key(event)
        self.assertEqual(self.app.state.facility_level("beehive"), 1)

        self.app.state.game_elapsed_seconds = main.DAY_SECONDS
        before_honey = self.app.state.honey
        self.app.handle_key(event)
        self.assertEqual(
            self.app.state.honey,
            before_honey + self.app.state.facility_yield("beehive"),
        )
        self.app.draw()

    def test_day_rollover_opens_summary_and_keeps_time_paused_until_closed(self):
        self.app.state.game_elapsed_seconds = main.DAY_SECONDS - 0.01
        self.app.state.tracked_day = 1
        self.app.state.daily_berries_harvested = 8

        self.app.update(0.02)

        self.assertEqual(self.app.overlay, "daily_report")
        self.assertIsNotNone(self.app.state.pending_daily_report)
        paused_at = self.app.state.game_elapsed_seconds
        self.app.update(30.0)
        self.assertEqual(self.app.state.game_elapsed_seconds, paused_at)
        self.app.draw()

        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_e,
            scancode=pygame.KSCAN_E,
            mod=0,
        )
        self.app.handle_key(event)
        self.assertIsNone(self.app.overlay)
        self.assertIsNone(self.app.state.pending_daily_report)

    def test_festival_weather_and_vip_customer_scene_draws(self):
        festival_day = main.DAYS_PER_SEASON * 2
        self.app.state.game_elapsed_seconds = (festival_day - 1) * main.DAY_SECONDS
        self.app.state.tracked_day = festival_day
        self.app.state.reputation = 25
        self.app.state.customers_waiting = 1
        self.app.state.customer_orders = [self.app.state.make_customer_order()]
        self.assertTrue(self.app.state.current_order.vip)

        self.app.draw()


if __name__ == "__main__":
    unittest.main()
