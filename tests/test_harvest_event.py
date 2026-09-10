import os
from pathlib import Path
import math
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
        self.assertEqual(self.app.action_effects[-1].label, "블루베리 +4")

    def test_fertilized_harvest_labels_the_actual_crop_and_next_crop_is_normal(self):
        self.app.player.update(*main.PLOT_RECTS[0].center)
        self.app.state.fertilizer = 1
        self.app.use_fertilizer_nearby()
        self.app.state.plots[0].ready_at = 0
        before = self.app.state.organic_blueberries
        amount = self.app.state.harvest_yield_for_day()
        self.app.interact()
        self.assertEqual(self.app.state.organic_blueberries, before + amount)
        self.assertEqual(self.app.action_effects[-1].label, f"유기농 블루베리 +{amount}")
        self.assertIn(f"유기농 블루베리 {amount}개", self.app.toast)
        self.assertFalse(self.app.state.plots[0].fertilized)
        # Having organic berries in the bag must not relabel the next plain crop.
        self.app.state.plots[0].ready_at = 0
        self.app.interact()
        self.assertEqual(self.app.action_effects[-1].label, f"블루베리 +{amount}")
        self.assertNotIn("유기농", self.app.toast)
        self.assertEqual(self.app.state.organic_blueberries, before + amount)

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

    def test_blender_walls_match_roof_width(self):
        self.assertEqual(main.CAFE.centerx, 1760)
        self.assertEqual(main.CAFE.width, 496)
        self.assertEqual(main.CAFE_ROOF_OVERHANG, 0)
        roof_width = main.CAFE.width + main.CAFE_ROOF_OVERHANG * 2
        self.assertEqual(roof_width, main.CAFE.width)

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
        self.assertEqual(
            main.PLAYER_SHEET_PATH.name,
            "player_doll_shark_sheet_v1.png",
        )
        sheet = pygame.image.load(str(main.PLAYER_SHEET_PATH)).convert_alpha()
        self.assertEqual(sheet.get_at((0, 0)).a, 0)
        sprite_rects = [
            rect
            for rect in pygame.mask.from_surface(sheet, 160).get_bounding_rects()
            if rect.width * rect.height > 20_000
        ]
        self.assertEqual(len(sprite_rects), 12)
        self.assertEqual(self.app.player_sprite_error, "")
        self.assertEqual(set(self.app.player_frames), {"down", "left", "right", "up"})
        self.assertTrue(all(len(frames) == 3 for frames in self.app.player_frames.values()))
        self.assertTrue(
            all(frame.get_flags() & pygame.SRCALPHA for frames in self.app.player_frames.values()
                for frame in frames)
        )

    def test_shark_character_keeps_white_clothing_opaque(self):
        for direction in ("down", "left", "right"):
            for frame in self.app.player_frames[direction]:
                white_pixels = sum(
                    1
                    for x in range(frame.get_width())
                    for y in range(frame.get_height())
                    if (
                        (color := frame.get_at((x, y))).a > 200
                        and min(color.r, color.g, color.b) > 220
                        and max(color.r, color.g, color.b)
                        - min(color.r, color.g, color.b) < 35
                    )
                )
                self.assertGreater(white_pixels, 100)

    def test_high_refresh_target_and_reused_render_resources(self):
        self.assertGreaterEqual(main.FPS, 165)
        self.assertIs(self.app._obstacles(), self.app._obstacles())
        self.assertIs(self.app._obstacles(), main.STATIC_OBSTACLES)
        self.assertEqual(set(self.app._ground_textures), set(main.GROUND_PALETTES))
        self.assertTrue(
            all(
                texture.get_size()
                == (main.GROUND_TEXTURE_SIZE, main.GROUND_TEXTURE_SIZE)
                for texture in self.app._ground_textures.values()
            )
        )
        self.assertEqual(self.app._sun_halo.get_size(), (112, 112))
        self.assertEqual(self.app._moon_halo.get_size(), (112, 112))
        self.assertEqual(self.app._stars_overlay.get_size(), (main.SCREEN_W, main.SCREEN_H))
        self.assertEqual(
            self.app._impact_overlay.get_size(),
            (main.SCREEN_W, main.SCREEN_H),
        )

        key = ("반복 글자", 13, main.INK)
        self.app.text(*key, 20, 20)
        cached = self.app._text_cache[key]
        self.app.text(*key, 20, 20)
        self.assertIs(self.app._text_cache[key], cached)

        shade_color = (31, 26, 39, 178)
        self.app.draw_screen_shade(shade_color)
        cached_shade = self.app._shade_overlays[shade_color]
        self.app.draw_screen_shade(shade_color)
        self.assertIs(self.app._shade_overlays[shade_color], cached_shade)

    def test_draw_calculates_nearest_interaction_only_once(self):
        with patch.object(
            self.app,
            "nearest_interaction",
            wraps=self.app.nearest_interaction,
        ) as nearest:
            self.app.draw()

        self.assertEqual(nearest.call_count, 1)

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
        self.app.state.premium_ice = 1
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
        for special_key in ("premium_honey", "low_fat_milk", "premium_ice"):
            self.app.handle_click(self.app.blender_special_button(special_key).center)
        self.app.draw()
        self.app.handle_click(pygame.Rect(440, 550, 300, 56).center)

        self.assertEqual(self.app.overlay, "blending")
        self.assertEqual(self.app.state.prepared_bonus, 300)
        self.assertEqual(self.app.state.premium_honey, 0)
        self.assertEqual(self.app.state.premium_ice, 0)
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

    def test_market_keyboard_sells_ten_then_all_remaining_blueberries(self):
        self.app.overlay = "market"
        self.app.state.blueberries = 14
        starting_money = self.app.state.money
        price = self.app.state.raw_blueberry_price()

        sell_ten = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_1,
            scancode=pygame.KSCAN_1,
            mod=pygame.KMOD_SHIFT,
        )
        self.app.handle_key(sell_ten)
        self.assertEqual(self.app.state.blueberries, 4)

        sell_all = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_1,
            scancode=pygame.KSCAN_1,
            mod=pygame.KMOD_META,
        )
        self.app.handle_key(sell_all)
        self.assertEqual(self.app.state.blueberries, 0)
        self.assertEqual(self.app.state.money, starting_money + price * 14)

    def test_market_buttons_sell_ten_and_all(self):
        self.app.overlay = "market"
        self.app.state.golden_blueberries = 15

        self.app.handle_click(main.market_sale_button_rect(1, 1).center)
        self.assertEqual(self.app.state.golden_blueberries, 5)
        self.app.handle_click(main.market_sale_button_rect(1, 2).center)
        self.assertEqual(self.app.state.golden_blueberries, 0)

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
        self.assertEqual(self.app.game_clock()[:3], (1, 18, 0))
        self.app.state.game_elapsed_seconds = main.DAY_SECONDS * 0.75
        self.assertEqual(self.app.game_clock()[:3], (1, 0, 0))
        self.app.state.game_elapsed_seconds = main.DAY_SECONDS
        self.assertEqual(self.app.game_clock()[:3], (2, 6, 0))

    def test_day_evening_and_night_are_visually_separate(self):
        self.assertEqual(main.day_period_for_phase(0.00), "아침")
        self.assertEqual(main.day_period_for_phase(2 / 24), "낮")
        self.assertEqual(main.day_period_for_phase(12 / 24), "저녁")
        self.assertEqual(main.day_period_for_phase(14 / 24), "밤")
        self.assertEqual(main.day_period_for_phase(22 / 24), "새벽")

        self.app.screen.fill((160, 160, 160))
        self.app.state.game_elapsed_seconds = main.DAY_SECONDS * 0.25
        self.app.draw_lighting()
        day_pixel = self.app.screen.get_at((20, 20))[:3]

        self.app.screen.fill((160, 160, 160))
        self.app.state.game_elapsed_seconds = main.DAY_SECONDS * 0.75
        self.app.draw_lighting()
        night_pixel = self.app.screen.get_at((20, 20))[:3]
        self.assertLess(sum(night_pixel), sum(day_pixel))

    def test_pixel_sun_and_moon_stay_fixed_at_the_upper_right(self):
        morning_sun = main.celestial_position_for_phase(0.05)
        afternoon_sun = main.celestial_position_for_phase(0.45)
        evening_moon = main.celestial_position_for_phase(0.55)
        late_moon = main.celestial_position_for_phase(0.95)
        sun = afternoon_sun
        moon = evening_moon
        self.assertEqual(sun[0], "sun")
        self.assertEqual(moon[0], "moon")
        self.assertEqual(morning_sun[1:3], main.CELESTIAL_FIXED_POSITION)
        self.assertEqual(afternoon_sun[1:3], main.CELESTIAL_FIXED_POSITION)
        self.assertEqual(evening_moon[1:3], main.CELESTIAL_FIXED_POSITION)
        self.assertEqual(late_moon[1:3], main.CELESTIAL_FIXED_POSITION)

        self.app.state.game_elapsed_seconds = main.DAY_SECONDS * 0.25
        self.app.screen.fill((0, 0, 0))
        self.app.draw_celestial_cycle()
        self.assertGreater(
            sum(self.app.screen.get_at(main.CELESTIAL_FIXED_POSITION)[:3]),
            0,
        )

    def test_photo_streetlight_sites_are_interactive_and_light_the_night(self):
        self.assertEqual(len(main.STREETLIGHT_POSITIONS), main.STREETLIGHT_COUNT)
        self.assertEqual(len(main.STREETLIGHT_SITE_LABELS), main.STREETLIGHT_COUNT)
        self.assertEqual(
            main.STREETLIGHT_POSITIONS,
            (
                (1550, 630), (1525, 50), (1280, 185),
                (-10, 570), (-10, 970), (704, 249), (540, 1360),
            ),
        )
        self.app.state.streetlights_installed = [False] * main.STREETLIGHT_COUNT
        for index, point in enumerate(main.STREETLIGHT_POSITIONS):
            with self.subTest(point=point):
                self.app.player.update(*point)
                self.app._snap_camera()
                target = self.app.nearest_interaction()
                self.assertIsNotNone(target)
                self.assertEqual(target["kind"], "streetlight")
                self.assertEqual(target["index"], index)

        self.app.state.streetlights_installed[0] = True
        self.app.state.game_elapsed_seconds = main.DAY_SECONDS * 0.75
        self.app.player.update(*main.STREETLIGHT_POSITIONS[0])
        self.app._snap_camera()
        self.app.screen.fill((150, 150, 150))
        self.app.draw_lighting()
        lamp_x, lamp_y = self.app.world_to_screen((1575, 548))
        self.assertGreater(
            sum(self.app.screen.get_at((lamp_x, lamp_y))[:3]),
            sum(self.app.screen.get_at((20, 620))[:3]),
        )
        self.app.state.money = 50_000
        self.app.state.berries_harvested = 10
        self.app.state.blueberries = 10
        self.assertIn("가로등", self.app.current_objective())
        with patch.object(self.app, "text", wraps=self.app.text) as draw_text:
            self.app.draw_help_overlay()
        self.assertTrue(any("가로등" in call.args[0] for call in draw_text.call_args_list))

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

    def test_rain_falls_straight_down_without_diagonal_bands(self):
        self.app.state.game_elapsed_seconds = main.DAY_SECONDS
        self.assertEqual(self.app.state.weather, "rain")
        with patch("pygame.draw.line") as draw_line:
            self.app.draw_weather_effects()
        self.assertEqual(draw_line.call_count, main.RAIN_DROP_COUNT)
        occupied_cells = set()
        for call in draw_line.call_args_list:
            start, end = call.args[2], call.args[3]
            self.assertEqual(start[0], end[0])
            self.assertGreater(end[1], start[1])
            occupied_cells.add((start[0] // 160, start[1] // 90))
        self.assertGreaterEqual(len(occupied_cells), 34)
        self.assertGreater(len({drop[2] for drop in main.RAIN_DROP_LAYOUT}), 1)
        self.assertGreater(len({drop[3] for drop in main.RAIN_DROP_LAYOUT}), 1)

    def test_hud_only_shows_balance_and_day_in_same_panel(self):
        drawn = {}
        original_text = self.app.text
        def capture_text(value, *args, **kwargs):
            drawn[value] = original_text(value, *args, **kwargs)
            return drawn[value]
        with patch.object(self.app, "text", side_effect=capture_text):
            self.app.draw_hud()
        self.assertEqual(len(drawn), 2)
        balance = next(label for label in drawn if label.endswith(" 벨리"))
        day = next(label for label in drawn if "일차" in label)
        current_day, hour, minute, _phase = self.app.game_clock()
        self.assertEqual(day, f"{current_day:,}일차  {hour:02d}:{minute:02d}")
        self.assertLessEqual(drawn[balance].bottom, drawn[day].top)
        self.assertTrue(main.HUD_LEFT_RECT.contains(drawn[balance]))
        self.assertTrue(main.HUD_LEFT_RECT.contains(drawn[day]))
        for removed in ("열매", "씨앗", "스무디", "도움말 H", "평판", "우유", "오늘 목표"):
            self.assertFalse(any(removed in label for label in drawn))

    def test_large_hud_balance_stays_inside_panel(self):
        self.app.state.money = 9_876_543_210
        drawn = {}
        original_text = self.app.text
        def capture_text(value, *args, **kwargs):
            drawn[value] = original_text(value, *args, **kwargs)
            return drawn[value]
        with patch.object(self.app, "text", side_effect=capture_text):
            self.app.draw_hud()
        self.assertTrue(main.HUD_LEFT_RECT.contains(drawn["98.8억 벨리"]))

    def test_top_menu_is_compact_and_day_changes_at_day_boundary(self):
        self.assertLessEqual(main.HUD_LEFT_RECT.height, 60)
        self.assertGreaterEqual(main.HUD_LEFT_RECT.left, 45)
        for elapsed, label in ((0, "1일차  06:00"),
                               (main.DAY_SECONDS * 0.75, "1일차  00:00"),
                               (main.DAY_SECONDS - 0.1, "1일차  05:59"),
                               (main.DAY_SECONDS, "2일차  06:00")):
            self.app.state.game_elapsed_seconds = elapsed
            with patch.object(self.app, "text", wraps=self.app.text) as draw_text:
                self.app.draw_hud()
            self.assertIn(label, [call.args[0] for call in draw_text.call_args_list])

    def test_customer_queue_has_clear_space_without_tree_overlap(self):
        customer_zones = []
        for index, (x, y) in enumerate(main.CUSTOMER_QUEUE_POINTS):
            customer_zones.append(
                pygame.Rect(x - 155, y - 214, 310, 228)
                if index == 0
                else pygame.Rect(x - 48, y - 142, 96, 156)
            )
        tree_zones = [
            pygame.Rect(x - 48, y - 110, 136, 146)
            for x, y in main.TREE_POSITIONS
        ]
        for customer_zone in customer_zones:
            for tree_zone in tree_zones:
                self.assertFalse(customer_zone.colliderect(tree_zone))

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

    def test_physical_h_scancode_opens_and_closes_help_with_non_latin_input(self):
        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=0,
            scancode=pygame.KSCAN_H,
            mod=0,
        )

        self.app.handle_key(event)
        self.assertEqual(self.app.overlay, "help")
        self.app.draw()
        self.app.handle_key(event)
        self.assertIsNone(self.app.overlay)

    def test_fertilizer_shortcut_creates_organic_crop_impact(self):
        self.app.state.fertilizer = 1
        self.app.player.update(*main.PLOT_RECTS[0].center)
        event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_f,
            scancode=pygame.KSCAN_F,
            mod=0,
        )

        self.app.handle_key(event)

        self.assertEqual(self.app.state.fertilizer, 0)
        self.assertTrue(self.app.state.plots[0].fertilized)
        self.assertTrue(self.app.action_effects)

    def test_blender_starts_three_second_grinding_sound(self):
        order = CustomerOrder(3, 1, 1, 1)
        self.app.state.customers_waiting = 1
        self.app.state.customer_orders = [order]
        self.app.state.blueberries = 3
        self.app.state.honey = self.app.state.milk = self.app.state.ice = 1
        self.app.blender_mix = dict(order.recipe)
        self.app.blender_sound = object()
        self.app.blender_channel = Mock()

        self.app.finish_blender_mix()

        self.assertEqual(self.app.overlay, "blending")
        self.assertEqual(self.app.blender_animation_remaining, main.BLENDER_DURATION)
        self.app.blender_channel.play.assert_called_once_with(self.app.blender_sound)
        self.assertLessEqual(self.app.current_bgm_volume, main.BGM_DUCK_VOLUME)

    def test_fishing_cast_bite_catch_and_shop_sale_flow(self):
        self.app.state.money = main.FISHING_ROD_COST
        self.app.buy_item("fishing_rod")
        self.assertEqual(self.app.state.fishing_rod, 1)
        self.app.player.update(main.POND.left - 25, main.POND.centery)
        controlled_rng = Mock()
        controlled_rng.uniform.side_effect = lambda start, end: (start + end) / 2
        controlled_rng.random.return_value = 0.01
        controlled_rng.randint.side_effect = lambda start, end: (start + end) // 2
        self.app.rng = controlled_rng

        self.app.interact()
        self.assertEqual(self.app.fishing_phase, "waiting")
        self.assertEqual(
            self.app.state.fishing_rod_durability,
            main.FISHING_ROD_MAX_DURABILITY - 1,
        )
        self.app.fishing_phase = "bite"
        self.app.interact()

        self.assertEqual(self.app.fishing_phase, "idle")
        self.assertEqual(self.app.state.carp, 1)
        self.assertIn(("carp", 1), self.app.state.bag_stacks())
        self.app.overlay = "fish_market"
        sale_event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_1,
            scancode=0,
            mod=0,
        )
        self.app.handle_key(sale_event)
        self.assertEqual(self.app.state.carp, 0)
        self.app.draw()

    def test_final_fishing_rod_cast_can_land_a_fish_after_the_rod_breaks(self):
        self.app.state.fishing_rod = 1
        self.app.state.fishing_rod_durability = 1
        self.app.player.update(main.POND.left - 25, main.POND.centery)
        controlled_rng = Mock()
        controlled_rng.uniform.side_effect = lambda start, end: (start + end) / 2
        controlled_rng.random.return_value = 0.01
        controlled_rng.randint.side_effect = lambda start, end: (start + end) // 2
        self.app.rng = controlled_rng

        self.app.interact()
        self.assertEqual(self.app.fishing_phase, "waiting")
        self.assertEqual(self.app.state.fishing_rod, 0)
        self.assertEqual(self.app.state.fishing_rod_durability, 0)

        self.app.fishing_phase = "bite"
        self.app.interact()

        self.assertEqual(self.app.fishing_phase, "idle")
        self.assertEqual(self.app.state.carp, 1)

    def test_farmhouse_furniture_shop_enters_edit_mode_and_places_items(self):
        self.app.state.money = sum(main.FURNITURE_COSTS.values())
        self.app.player.update(main.HOUSE.centerx, main.HOUSE.bottom + 37)
        self.app.interact()
        self.assertEqual(self.app.overlay, "home")
        for category_index in range(len(main.HOME_CATEGORIES)):
            self.app.handle_click(main.furniture_category_rect(category_index).center)
            for key_number in range(pygame.K_1, pygame.K_6):
                self.app.handle_key(pygame.event.Event(
                    pygame.KEYDOWN, key=key_number, scancode=0, mod=0,
                ))
                if self.app.pending_purchase is not None:
                    self.app.handle_key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_y, mod=0))
        self.assertEqual(set(self.app.state.furniture_owned), set(main.FURNITURE_COSTS))
        self.assertEqual(self.app.state.money, 0)
        self.assertEqual(self.app.state.furniture_layout, {})

        self.app.handle_key(pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_g,
            scancode=pygame.KSCAN_G,
            mod=0,
        ))
        self.assertTrue(self.app.home_edit_mode)
        self.app.handle_click(main.furniture_category_rect(0).center)
        self.app.handle_key(pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_1,
            scancode=0,
            mod=0,
        ))
        position = (
            main.HOME_BUILD_AREA.x + main.HOME_GRID_CELL + 4,
            main.HOME_BUILD_AREA.y + main.HOME_GRID_CELL + 4,
        )
        self.app.handle_click(position)
        self.assertEqual(self.app.state.furniture_layout["bed"], [1, 1, 0])

        self.app.handle_key(pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_r,
            scancode=0,
            mod=0,
        ))
        self.assertEqual(self.app.state.furniture_layout["bed"], [1, 1, 1])
        self.app.handle_key(pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_RIGHT,
            scancode=0,
            mod=0,
        ))
        self.assertEqual(self.app.state.furniture_layout["bed"], [2, 1, 1])
        self.app.draw()

    def test_new_furniture_tabs_support_click_purchase_and_edit_selection(self):
        self.app.overlay = "home"
        self.app.state.money = 10000
        self.app.handle_key(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_PAGEUP, scancode=0, mod=0,
        ))
        self.assertEqual(self.app.home_category, "wardrobe")
        self.app.handle_key(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_PAGEUP, scancode=0, mod=0,
        ))
        self.assertEqual(self.app.home_category, "flowerpot")
        self.app.handle_click(main.furniture_card_rect(4).center)
        self.assertIsNotNone(self.app.pending_purchase)
        self.app.handle_key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_y, mod=0))
        self.assertIn("plant_lavender", self.app.state.furniture_owned)
        self.app.handle_click(main.furniture_card_rect(4).center)
        self.assertTrue(self.app.home_edit_mode)
        self.assertEqual(self.app.selected_furniture, "plant_lavender")
        self.app.handle_click((main.HOME_BUILD_AREA.x + 4, main.HOME_BUILD_AREA.y + 4))
        self.assertEqual(self.app.state.furniture_layout["plant_lavender"], [0, 0, 0])
        self.app.draw()
        self.app.handle_key(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_PAGEDOWN, scancode=0, mod=0,
        ))
        self.assertEqual(self.app.home_category, "wardrobe")
        self.app.handle_key(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_PAGEDOWN, scancode=0, mod=0,
        ))
        self.assertEqual(self.app.home_category, "bed")
        # Browsing other categories must not lose the placed plant.
        self.assertEqual(self.app.state.furniture_layout["plant_lavender"], [0, 0, 0])

    def test_wardrobe_purchase_placement_equipment_and_reset(self):
        import wardrobe_ui
        self.app.overlay = "home"
        self.app.open_wardrobe()
        self.assertEqual(self.app.home_category, "wardrobe")
        self.assertEqual(self.app.overlay, "home")
        self.app.state.money = 1500
        self.assertTrue(self.app.state.buy_furniture("wardrobe")[0])
        self.app.open_wardrobe()
        self.assertTrue(self.app.home_edit_mode)
        self.assertTrue(self.app.state.place_furniture("wardrobe", 0, 0)[0])
        self.app.state.money = 10000
        self.app.handle_key(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_UNKNOWN, scancode=pygame.KSCAN_C, mod=0,
        ))
        self.assertEqual(self.app.overlay, "wardrobe")
        self.app.handle_click(wardrobe_ui.WHALE_RECT.center)
        self.assertIsNotNone(self.app.pending_purchase)
        self.assertEqual(self.app.state.money, 10000)
        self.app.handle_key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_y, mod=0))
        self.assertEqual(self.app.state.appearance["outfit"], "whale")
        self.assertTrue(self.app.state.owns_theme("whale"))
        self.assertEqual(self.app.state.money, 4600)
        self.assertEqual(GameState.load(main.SAVE_PATH).appearance, self.app.state.appearance)
        for index in range(5):
            self.app.handle_click(wardrobe_ui.tab_rect(index).center)
            self.app.handle_click(wardrobe_ui.item_rect(1).center)
            if self.app.pending_purchase is not None:
                self.app.handle_key(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_y, mod=0))
            self.app.draw()
        self.app.handle_key(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_RIGHT, scancode=0, mod=0,
        ))
        self.assertEqual(self.app.wardrobe_direction, "left")
        self.app.draw()
        self.app.handle_click(wardrobe_ui.RESET_RECT.center)
        self.assertEqual(self.app.state.appearance, {})
        self.assertIs(self.app.player_frames, self.app.original_player_frames)
        self.app.handle_click(wardrobe_ui.RETURN_RECT.center)
        self.assertEqual(self.app.overlay, "home")

    def test_fish_and_furniture_png_catalogues_are_loaded(self):
        self.assertEqual(set(self.app.fish_icons), set(main.FISH_KEYS))
        self.assertEqual(set(self.app.furniture_sprites), set(main.FURNITURE_KEYS))
        self.assertFalse(self.app.decor_asset_error)
        for path in (*main.FISH_ASSET_PATHS.values(), *main.FURNITURE_ASSET_PATHS.values()):
            self.assertTrue(path.exists(), path)
        self.app.draw_item_icon("carp", (100, 100))
        self.app.draw_furniture("bed", (200, 200), 0.5)

    def test_redesigned_facility_png_catalogue_is_loaded_and_drawn(self):
        self.assertEqual(set(self.app.facility_sprites), set(main.FACILITY_RECTS))
        for key, path in main.FACILITY_ASSET_PATHS.items():
            self.assertTrue(path.exists(), path)
            self.assertEqual(
                self.app.facility_sprites[key].get_size(),
                main.FACILITY_RECTS[key].size,
            )
            self.assertGreater(
                self.app.facility_sprites[key].get_bounding_rect(min_alpha=1).width,
                main.FACILITY_RECTS[key].width // 2,
            )
            self.app.state.facility_levels[key] = 3
            self.app.draw_facility(key, main.FACILITY_RECTS[key])

    def test_facilities_have_clear_space_between_each_building(self):
        facilities = sorted(main.FACILITY_RECTS.values(), key=lambda rect: rect.left)
        horizontal_gaps = [
            right.left - left.right
            for left, right in zip(facilities, facilities[1:])
        ]

        self.assertTrue(all(gap >= 100 for gap in horizontal_gaps))

    def test_tree_spacing_and_side_back_foot_motion_are_clear(self):
        closest_pair = min(
            math.dist(first, second)
            for index, first in enumerate(main.TREE_POSITIONS)
            for second in main.TREE_POSITIONS[index + 1:]
        )
        self.assertGreaterEqual(closest_pair, 300)
        self.app.is_moving = True
        for direction in ("left", "right", "up"):
            self.app.direction = direction
            self.app.walk_phase = 1.2
            frames = self.app.player_walk_frames[direction]
            self.assertEqual(len(frames), 12)
            leg_regions = [pygame.image.tostring(frame.subsurface(
                (0, frame.get_height() - 20, frame.get_width(), 20)), "RGBA") for frame in frames]
            self.assertGreater(len(set(leg_regions)), 3)
            self.assertLessEqual(frames[0].get_height(), 101)
            self.app.draw_character()

    def test_drawer_ui_moves_stacks_saves_and_returns_home(self):
        from storage_ui import slot_rect, RETURN_RECT
        self.app.state.money = 500
        self.app.state.buy_furniture("drawer")
        self.app.state.place_furniture("drawer", 0, 0)
        self.app.state.blueberries = 20
        self.app.overlay = "home"
        self.app.handle_click(main.HOME_DRAWER_BUTTON.center)
        self.assertEqual(self.app.overlay, "storage")
        self.app.handle_click(slot_rect(0, True).center)
        self.assertEqual(self.app.state.blueberries, 4)
        self.assertEqual(self.app.state.drawer_stacks("drawer"), [("blueberries", 16)])
        self.app.draw()
        self.assertEqual(GameState.load(main.SAVE_PATH).drawer_contents, self.app.state.drawer_contents)
        with patch("pygame.key.get_mods", return_value=pygame.KMOD_SHIFT):
            self.app.handle_click(slot_rect(0, False).center)
        self.assertEqual(self.app.state.blueberries, 5)
        self.app.handle_click(RETURN_RECT.center)
        self.assertEqual(self.app.overlay, "home")

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
        before_honey = self.app.state.premium_honey
        self.app.handle_key(event)
        self.assertEqual(
            self.app.state.premium_honey,
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

    def test_queue_name_tags_and_vip_title_are_visible(self):
        regular = CustomerOrder(
            3, 1, 1, 1, customer_name="김서연", regular=True
        )
        vip = CustomerOrder(
            3,
            2,
            2,
            2,
            customer_name="박도윤",
            vip=True,
            vip_title="유명 요리사",
        )

        with patch.object(self.app, "text", wraps=self.app.text) as draw_text:
            self.app.draw_customer((600, 700), 0, order=regular, front=False)
            self.app.draw_customer((700, 700), 1, order=vip, front=True)

        labels = [call.args[0] for call in draw_text.call_args_list]
        self.assertIn("김서연", labels)
        self.assertTrue(
            any("VIP" in label and "유명 요리사" in label and "박도윤" in label
                for label in labels)
        )


if __name__ == "__main__":
    unittest.main()
