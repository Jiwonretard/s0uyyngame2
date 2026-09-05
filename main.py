"""Top-down Blueberry Smoothie Tycoon built with pygame.

The world uses original code-drawn pixel art, and the player uses a custom
four-direction sprite sheet based on the user's character reference photo.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import random
import sys
import time

import pygame

from game_state import (
    BAG_COLUMNS,
    BAG_ITEM_LABELS,
    BAG_ROWS,
    BAG_SLOT_COUNT,
    BAG_STACK_SIZE,
    CUSTOMER_QUEUE_SIZE,
    CustomerOrder,
    GROW_SECONDS,
    HARVEST_YIELD,
    ITEM_COSTS,
    MAX_PLOTS,
    RAW_BERRY_PRICE,
    REGROW_SECONDS,
    GameState,
)


SCREEN_W, SCREEN_H = 1280, 720
WORLD_W, WORLD_H = 2200, 1500
FPS = 60
PLAYER_SPEED = 235.0
DAY_SECONDS = 720.0
CUSTOMER_RETURN_SECONDS = 14.0
BLENDER_DURATION = 3.0
BASE_DIR = Path(__file__).resolve().parent
SAVE_PATH = BASE_DIR / "save_game.json"
SALE_SOUND_PATH = BASE_DIR / "assets" / "smoothie_sale.wav"
BGM_PATH = BASE_DIR / "assets" / "blueberry_morning.ogg"
PLAYER_SHEET_PATH = BASE_DIR / "assets" / "player_reference_sheet.png"
INGREDIENT_SOURCE_PATHS = {
    "milk": BASE_DIR / "assets" / "ingredient_milk_source.png",
    "blueberries": BASE_DIR / "assets" / "ingredient_blueberry_source.png",
    "ice": BASE_DIR / "assets" / "ingredient_ice_source.png",
    "honey": BASE_DIR / "assets" / "ingredient_honey_source.png",
}
BGM_NORMAL_VOLUME = 0.28
BGM_DUCK_VOLUME = 0.055
BGM_VOLUME_CHANGE_SPEED = 2.8

INK = (48, 40, 42)
WHITE = (255, 255, 255)
CREAM = (255, 239, 190)
MUTED = (112, 89, 78)
GRASS = (119, 177, 83)
GRASS_DARK = (74, 132, 65)
GRASS_LIGHT = (154, 202, 98)
PATH = (210, 171, 108)
PATH_EDGE = (160, 119, 76)
SOIL = (126, 76, 47)
SOIL_LIGHT = (173, 111, 61)
GREEN = (54, 119, 61)
GREEN_DARK = (35, 82, 45)
LEAF = (64, 138, 64)
BLUEBERRY = (76, 67, 164)
BLUEBERRY_DARK = (40, 35, 91)
PURPLE_LIGHT = (221, 202, 233)
GOLD = (236, 167, 48)
RED = (169, 65, 62)
WOOD = (139, 85, 48)
WOOD_DARK = (77, 47, 38)
WATER = (70, 146, 166)
WATER_LIGHT = (126, 199, 197)

HOUSE = pygame.Rect(120, 70, 440, 250)
SHOP = pygame.Rect(1510, 100, 450, 320)
CAFE = pygame.Rect(1540, 700, 440, 300)
MARKET = pygame.Rect(1010, 990, 360, 190)
SMOOTHIE_CART = pygame.Rect(1530, 1120, 430, 170)
POND = pygame.Rect(1040, 245, 390, 270)

CUSTOMER_QUEUE_POINTS = [
    (1840, 1322),
    (1905, 1338),
    (1970, 1354),
    (2035, 1370),
    (2100, 1386),
    (2165, 1402),
]

CUSTOMER_STYLES = [
    ((244, 193, 152), (101, 58, 43), (211, 92, 93)),
    ((222, 167, 121), (52, 42, 39), (72, 132, 178)),
    ((246, 205, 170), (218, 159, 66), (86, 151, 91)),
    ((196, 137, 102), (45, 35, 42), (180, 103, 174)),
    ((235, 187, 146), (132, 73, 48), (224, 147, 61)),
    ((213, 156, 119), (73, 53, 42), (88, 166, 158)),
]

BLENDER_INGREDIENTS = [
    ("blueberries", "블루베리", BLUEBERRY),
    ("honey", "꿀", GOLD),
    ("milk", "우유", (84, 149, 183)),
    ("ice", "얼음", (79, 169, 194)),
]

PLOT_RECTS = [
    pygame.Rect(280 + col * 158, 405 + row * 158, 120, 94)
    for row in range(3)
    for col in range(4)
]

TREE_POSITIONS = [
    (80, 485), (115, 790), (90, 1110), (650, 105), (850, 125),
    (1020, 120), (1450, 560), (2045, 265), (2080, 620),
    (2040, 970), (2050, 1340), (1415, 1320), (890, 1250),
    (575, 1300), (245, 1320), (720, 1040),
]


def find_korean_font() -> str | None:
    candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/Library/Fonts/NanumGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    for name in ("applesdgothicneo", "malgungothic", "nanumgothic", "notosanscjkr"):
        matched = pygame.font.match_font(name)
        if matched:
            return matched
    return None


def rounded_rect(surface: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int],
                 radius: int = 16, border: tuple[int, int, int] | None = None,
                 border_width: int = 0) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border is not None and border_width:
        pygame.draw.rect(surface, border, rect, width=border_width, border_radius=radius)


def draw_shadow(surface: pygame.Surface, rect: pygame.Rect, radius: int = 16, alpha: int = 48) -> None:
    shadow = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (37, 33, 44, alpha), (8, 9, rect.width, rect.height), border_radius=radius)
    surface.blit(shadow, (rect.x - 8, rect.y - 8))


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def distance_to_rect(point: tuple[float, float], rect: pygame.Rect) -> float:
    closest_x = max(rect.left, min(point[0], rect.right))
    closest_y = max(rect.top, min(point[1], rect.bottom))
    return distance(point, (closest_x, closest_y))


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: tuple[int, int, int]
    life: float = 0.8
    size: float = 5.0

    def update(self, dt: float) -> None:
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 35 * dt


@dataclass
class ActionEffect:
    x: float
    y: float
    label: str
    color: tuple[int, int, int]
    life: float = 1.45
    duration: float = 1.45

    def update(self, dt: float) -> None:
        self.life -= dt
        self.y -= 23 * dt


@dataclass
class DepartingCustomer:
    x: float
    y: float
    style: int
    life: float = 1.4

    def update(self, dt: float) -> None:
        self.life -= dt
        self.x += 105 * dt
        self.y -= 30 * dt


class GameApp:
    def __init__(self) -> None:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("블루베리 밸리")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        font_path = find_korean_font()
        self.fonts = {
            size: pygame.font.Font(font_path, size)
            for size in (13, 14, 15, 16, 17, 18, 20, 22, 25, 28, 32, 38)
        }
        load_errors: list[Exception] = []
        self.state = GameState.load(SAVE_PATH, on_error=load_errors.append)
        self.player = pygame.Vector2(self.state.player_x, self.state.player_y)
        if self._collides(self.player.x, self.player.y):
            self.player.update(360, 380)
        self.camera = pygame.Vector2()
        self._snap_camera()
        self.direction = "down"
        self.walk_phase = 0.0
        self.is_moving = False
        self.running = True
        self.overlay: str | None = None if self.state.tutorial_seen else "help"
        self.toast = "이제 캐릭터를 직접 움직여 농장을 운영하세요!"
        if load_errors:
            self.toast = "저장 파일을 읽지 못해 새 농장으로 시작했어요."
        self.toast_error = bool(load_errors)
        self.toast_until = time.time() + 4.5
        self.last_autosave = time.time()
        self.sale_sound: pygame.mixer.Sound | None = None
        self.sale_channel: pygame.mixer.Channel | None = None
        self.pending_sale_sounds = 0
        self.audio_error = ""
        self.music_error = ""
        self.current_bgm_volume = BGM_NORMAL_VOLUME
        self.bgm_duck_until = 0.0
        self.bgm_muted = False
        self.particles: list[Particle] = []
        self.action_effects: list[ActionEffect] = []
        self.departing_customers: list[DepartingCustomer] = []
        self.next_customer_at = time.time() + CUSTOMER_RETURN_SECONDS
        self.action_timer = 0.0
        self.impact_timer = 0.0
        self.shake_offset = pygame.Vector2()
        self.rng = random.Random(17)
        self.flowers = self._make_flowers()
        self.shop_buttons = self._make_shop_buttons()
        self.blender_mix = {key: 0 for key, _label, _color in BLENDER_INGREDIENTS}
        self.blender_message = "재료의 + 버튼을 눌러 맨 앞 손님의 주문과 똑같이 맞추세요."
        self.blender_message_error = False
        self.blender_animation_remaining = 0.0
        self.blender_complete_message = ""
        self.blender_cards = self._make_blender_cards()
        self.ingredient_icons: dict[str, pygame.Surface] = {}
        self.ingredient_icons_small: dict[str, pygame.Surface] = {}
        self.ingredient_icon_error = ""
        self._load_ingredient_icons()
        self._load_audio()
        self.player_frames: dict[str, list[pygame.Surface]] = {}
        self.player_sprite_error = ""
        self._load_player_frames()

    def _make_flowers(self) -> list[tuple[int, int, tuple[int, int, int]]]:
        flowers = []
        colors = [(255, 238, 130), (247, 177, 197), (217, 229, 255), (255, 255, 240)]
        rng = random.Random(43)
        for _ in range(150):
            x, y = rng.randint(35, WORLD_W - 35), rng.randint(35, WORLD_H - 35)
            point = (x, y)
            blocked = any(rect.inflate(60, 60).collidepoint(point) for rect in (HOUSE, SHOP, CAFE, MARKET, SMOOTHIE_CART, POND))
            if not blocked and not pygame.Rect(215, 340, 730, 560).collidepoint(point):
                flowers.append((x, y, rng.choice(colors)))
        return flowers

    @staticmethod
    def _make_shop_buttons() -> list[tuple[pygame.Rect, str, str, tuple[int, int, int]]]:
        return [
            (pygame.Rect(402, 294, 222, 76), "seeds", "씨앗", GREEN),
            (pygame.Rect(656, 294, 222, 76), "honey", "꿀", GOLD),
            (pygame.Rect(402, 390, 222, 76), "milk", "우유", (84, 149, 183)),
            (pygame.Rect(656, 390, 222, 76), "ice", "얼음", (79, 169, 194)),
        ]

    @staticmethod
    def _make_blender_cards() -> list[tuple[pygame.Rect, str, str, tuple[int, int, int]]]:
        cards = []
        for index, (key, label, color) in enumerate(BLENDER_INGREDIENTS):
            col, row = index % 2, index // 2
            cards.append(
                (pygame.Rect(280 + col * 370, 258 + row * 137, 330, 112), key, label, color)
            )
        return cards

    def _load_audio(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            self.sale_sound = pygame.mixer.Sound(str(SALE_SOUND_PATH))
            self.sale_sound.set_volume(0.82)
            self.sale_channel = pygame.mixer.Channel(0)
        except (pygame.error, FileNotFoundError) as exc:
            self.audio_error = str(exc)
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            pygame.mixer.music.load(str(BGM_PATH))
            pygame.mixer.music.set_volume(self.current_bgm_volume)
            pygame.mixer.music.play(-1, fade_ms=1400)
        except (pygame.error, FileNotFoundError) as exc:
            self.music_error = str(exc)

    @staticmethod
    def _scale_icon_to_cell(icon: pygame.Surface, cell_size: int) -> pygame.Surface:
        scale = min((cell_size - 4) / icon.get_width(), (cell_size - 4) / icon.get_height())
        width = max(1, round(icon.get_width() * scale))
        height = max(1, round(icon.get_height() * scale))
        scaled = pygame.transform.scale(icon, (width, height))
        cell = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        cell.blit(scaled, scaled.get_rect(center=(cell_size // 2, cell_size // 2)))
        return cell

    @staticmethod
    def _extract_pixel_icon(source: pygame.Surface, *, keep_enclosed_fill: bool) -> pygame.Surface:
        source = source.convert_alpha()
        width, height = source.get_size()
        background = source.get_at((width // 2, 20))[:3]

        def is_background(pixel: pygame.Color) -> bool:
            return max(abs(pixel[index] - background[index]) for index in range(3)) <= 7

        points = []
        for y in range(24, height - 24):
            for x in range(24, width - 24):
                if not is_background(source.get_at((x, y))):
                    points.append((x, y))
        if not points:
            raise ValueError("ingredient icon pixels not found")
        left = min(point[0] for point in points)
        right = max(point[0] for point in points)
        top = min(point[1] for point in points)
        bottom = max(point[1] for point in points)
        crop_rect = pygame.Rect(left, top, right - left + 1, bottom - top + 1)
        crop_rect = crop_rect.inflate(12, 12).clip(source.get_rect())
        icon = source.subsurface(crop_rect).copy().convert_alpha()

        if keep_enclosed_fill:
            icon_width, icon_height = icon.get_size()
            visited: set[tuple[int, int]] = set()
            stack = [
                *((x, 0) for x in range(icon_width)),
                *((x, icon_height - 1) for x in range(icon_width)),
                *((0, y) for y in range(icon_height)),
                *((icon_width - 1, y) for y in range(icon_height)),
            ]
            while stack:
                x, y = stack.pop()
                if (x, y) in visited or not (0 <= x < icon_width and 0 <= y < icon_height):
                    continue
                if not is_background(icon.get_at((x, y))):
                    continue
                visited.add((x, y))
                stack.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
            for x, y in visited:
                color = icon.get_at((x, y))
                icon.set_at((x, y), (*color[:3], 0))
        else:
            for y in range(icon.get_height()):
                for x in range(icon.get_width()):
                    color = icon.get_at((x, y))
                    if is_background(color):
                        icon.set_at((x, y), (*color[:3], 0))
        return icon

    def _load_ingredient_icons(self) -> None:
        try:
            for key, path in INGREDIENT_SOURCE_PATHS.items():
                source = pygame.image.load(str(path))
                icon = self._extract_pixel_icon(
                    source, keep_enclosed_fill=(key == "milk")
                )
                self.ingredient_icons[key] = self._scale_icon_to_cell(icon, 58)
                self.ingredient_icons_small[key] = self._scale_icon_to_cell(icon, 34)
        except (pygame.error, FileNotFoundError, ValueError) as exc:
            self.ingredient_icons.clear()
            self.ingredient_icons_small.clear()
            self.ingredient_icon_error = str(exc)

    def _load_player_frames(self) -> None:
        """Extract the 12 generated sprites by their connected alpha regions."""
        try:
            sheet = pygame.image.load(str(PLAYER_SHEET_PATH)).convert_alpha()
            mask = pygame.mask.from_surface(sheet, 160)
            sprite_rects = [
                rect for rect in mask.get_bounding_rects()
                if rect.width * rect.height > 20_000
            ]
            sprite_rects.sort(key=lambda rect: (rect.y, rect.x))
            if len(sprite_rects) != 12:
                raise ValueError(f"expected 12 player frames, found {len(sprite_rects)}")
            max_source_height = max(rect.height for rect in sprite_rects)
            directions = ("down", "left", "right", "up")
            frames: dict[str, list[pygame.Surface]] = {direction: [] for direction in directions}
            for row, direction in enumerate(directions):
                for column in range(3):
                    rect = sprite_rects[row * 3 + column].inflate(12, 12).clip(sheet.get_rect())
                    source = sheet.subsurface(rect).copy()
                    scale = 104 / max_source_height
                    width = max(1, round(source.get_width() * scale))
                    height = max(1, round(source.get_height() * scale))
                    scaled = pygame.transform.scale(source, (width, height))
                    canvas = pygame.Surface((92, 112), pygame.SRCALPHA)
                    canvas.blit(scaled, ((canvas.get_width() - width) // 2, canvas.get_height() - height))
                    frames[direction].append(canvas)
            self.player_frames = frames
        except (pygame.error, OSError, ValueError) as exc:
            self.player_frames = {}
            self.player_sprite_error = str(exc)

    def _snap_camera(self) -> None:
        self.camera.x = max(0, min(WORLD_W - SCREEN_W, self.player.x - SCREEN_W / 2))
        self.camera.y = max(0, min(WORLD_H - SCREEN_H, self.player.y - SCREEN_H / 2))

    def world_to_screen(self, point: tuple[float, float]) -> tuple[int, int]:
        return (
            int(point[0] - self.camera.x + self.shake_offset.x),
            int(point[1] - self.camera.y + self.shake_offset.y),
        )

    def rect_to_screen(self, rect: pygame.Rect) -> pygame.Rect:
        return rect.move(
            -round(self.camera.x) + round(self.shake_offset.x),
            -round(self.camera.y) + round(self.shake_offset.y),
        )

    def text(self, value: str, size: int, color: tuple[int, int, int], x: int, y: int,
             *, center: bool = False) -> pygame.Rect:
        image = self.fonts[size].render(value, True, color)
        rect = image.get_rect(center=(x, y)) if center else image.get_rect(topleft=(x, y))
        self.screen.blit(image, rect)
        return rect

    def wrapped_text(self, value: str, size: int, color: tuple[int, int, int], rect: pygame.Rect,
                     line_gap: int = 4, center: bool = False) -> int:
        font = self.fonts[size]
        lines: list[str] = []
        current = ""
        for word in value.split():
            candidate = word if not current else current + " " + word
            if font.size(candidate)[0] <= rect.width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        y = rect.y
        for line in lines:
            image = font.render(line, True, color)
            x = rect.centerx - image.get_width() // 2 if center else rect.x
            self.screen.blit(image, (x, y))
            y += image.get_height() + line_gap
        return y

    def notify(self, message: str, error: bool = False) -> None:
        self.toast = message
        self.toast_error = error
        self.toast_until = time.time() + 3.2

    def save(self, announce: bool = False) -> None:
        self.state.player_x, self.state.player_y = self.player.x, self.player.y
        try:
            self.state.save(SAVE_PATH)
            self.last_autosave = time.time()
            if announce:
                self.notify("농장과 현재 위치를 저장했어요.")
        except OSError as exc:
            self.notify(f"저장하지 못했어요: {exc}", True)

    def _feet_rect(self, x: float, y: float) -> pygame.Rect:
        return pygame.Rect(round(x - 13), round(y - 13), 26, 20)

    def _obstacles(self) -> list[pygame.Rect]:
        obstacles = [HOUSE, SHOP, CAFE, MARKET, SMOOTHIE_CART, POND.inflate(-34, -30)]
        obstacles.extend(pygame.Rect(x - 14, y - 8, 28, 32) for x, y in TREE_POSITIONS)
        return obstacles

    def _collides(self, x: float, y: float) -> bool:
        feet = self._feet_rect(x, y)
        if feet.left < 8 or feet.right > WORLD_W - 8 or feet.top < 8 or feet.bottom > WORLD_H - 8:
            return True
        return any(feet.colliderect(obstacle) for obstacle in self._obstacles())

    def move_player(self, dt: float) -> None:
        if self.overlay is not None:
            self.is_moving = False
            return
        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(
            int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a]),
            int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w]),
        )
        self.is_moving = movement.length_squared() > 0
        if not self.is_moving:
            return
        movement = movement.normalize() * PLAYER_SPEED * dt
        if abs(movement.x) > abs(movement.y):
            self.direction = "right" if movement.x > 0 else "left"
        else:
            self.direction = "down" if movement.y > 0 else "up"
        new_x = self.player.x + movement.x
        if not self._collides(new_x, self.player.y):
            self.player.x = new_x
        new_y = self.player.y + movement.y
        if not self._collides(self.player.x, new_y):
            self.player.y = new_y
        self.walk_phase += dt * 11.0

    def update(self, dt: float) -> None:
        self.move_player(dt)
        if self.overlay is None:
            # The farm calendar advances only while the player is actually in
            # the world. Closing the game or opening a menu pauses the clock.
            self.state.game_elapsed_seconds += max(0.0, dt)
        target = pygame.Vector2(
            max(0, min(WORLD_W - SCREEN_W, self.player.x - SCREEN_W / 2)),
            max(0, min(WORLD_H - SCREEN_H, self.player.y - SCREEN_H / 2)),
        )
        self.camera += (target - self.camera) * min(1.0, dt * 6.5)
        for particle in self.particles:
            particle.update(dt)
        self.particles = [particle for particle in self.particles if particle.life > 0]
        for effect in self.action_effects:
            effect.update(dt)
        self.action_effects = [effect for effect in self.action_effects if effect.life > 0]
        for customer in self.departing_customers:
            customer.update(dt)
        self.departing_customers = [
            customer for customer in self.departing_customers if customer.life > 0
        ]
        now = time.time()
        if self.state.customers_waiting < CUSTOMER_QUEUE_SIZE and now >= self.next_customer_at:
            was_empty = self.state.customers_waiting == 0
            self.state.add_customer()
            self.next_customer_at = now + CUSTOMER_RETURN_SECONDS
            if was_empty:
                self.notify("새 손님이 스무디 판매대에 도착했어요!")
        self.action_timer = max(0.0, self.action_timer - dt)
        self.impact_timer = max(0.0, self.impact_timer - dt)
        if self.impact_timer > 0:
            strength = max(1, int(7 * self.impact_timer / 0.28))
            self.shake_offset.update(
                self.rng.randint(-strength, strength),
                self.rng.randint(-strength, strength),
            )
        else:
            self.shake_offset.update(0, 0)
        if self.pending_sale_sounds and self.sale_channel and self.sale_sound and not self.sale_channel.get_busy():
            self.pending_sale_sounds -= 1
            self.sale_channel.play(self.sale_sound)
            self.duck_background_music(self.sale_sound.get_length() + 0.25)
        if not self.music_error:
            effect_is_playing = bool(
                self.sale_channel
                and (self.sale_channel.get_busy() or self.pending_sale_sounds)
            )
            should_duck = effect_is_playing or time.time() < self.bgm_duck_until
            target_volume = 0.0 if self.bgm_muted else (
                BGM_DUCK_VOLUME if should_duck else BGM_NORMAL_VOLUME
            )
            amount = min(1.0, dt * BGM_VOLUME_CHANGE_SPEED)
            self.current_bgm_volume += (target_volume - self.current_bgm_volume) * amount
            pygame.mixer.music.set_volume(self.current_bgm_volume)
        if self.overlay == "blending":
            self.blender_animation_remaining = max(
                0.0, self.blender_animation_remaining - max(0.0, dt)
            )
            if self.blender_animation_remaining <= 0.0:
                self.overlay = None
                self.notify(self.blender_complete_message)
                self.spawn_particles(
                    (CAFE.centerx, CAFE.bottom + 42), (192, 102, 186), 30
                )
        if time.time() - self.last_autosave > 10.0:
            self.save()

    def spawn_particles(self, point: tuple[float, float], color: tuple[int, int, int], count: int = 12) -> None:
        for _ in range(count):
            angle = self.rng.uniform(0, math.tau)
            speed = self.rng.uniform(35, 95)
            self.particles.append(
                Particle(point[0], point[1], math.cos(angle) * speed, math.sin(angle) * speed - 50,
                         color, self.rng.uniform(0.55, 1.0), self.rng.uniform(3, 7))
            )

    def spawn_harvest_impact(self, point: tuple[float, float], amount: int) -> None:
        colors = (BLUEBERRY, BLUEBERRY_DARK, (190, 176, 235), LEAF, GOLD)
        for index in range(34):
            angle = math.tau * index / 34 + self.rng.uniform(-0.1, 0.1)
            speed = self.rng.uniform(70, 175)
            self.particles.append(
                Particle(
                    point[0], point[1] - 20,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed - 80,
                    colors[index % len(colors)],
                    self.rng.uniform(0.9, 1.35),
                    self.rng.uniform(8, 14),
                )
            )
        self.action_effects.append(
            ActionEffect(point[0], point[1] - 88, f"블루베리 +{amount}", BLUEBERRY_DARK)
        )
        self.action_timer = 0.36
        self.impact_timer = 0.28

    def duck_background_music(self, seconds: float) -> None:
        self.bgm_duck_until = max(self.bgm_duck_until, time.time() + max(0.0, seconds))
        if not self.music_error and not self.bgm_muted:
            self.current_bgm_volume = BGM_DUCK_VOLUME
            pygame.mixer.music.set_volume(self.current_bgm_volume)

    def play_sale_sound(self) -> None:
        if not self.sale_sound or not self.sale_channel:
            if self.audio_error:
                self.notify("판매는 됐지만 첨부 효과음을 재생하지 못했어요.", True)
            return
        sound_length = (
            self.sale_sound.get_length()
            if hasattr(self.sale_sound, "get_length")
            else 1.0
        )
        if self.sale_channel.get_busy():
            self.pending_sale_sounds += 1
            self.duck_background_music(
                sound_length * (self.pending_sale_sounds + 1) + 0.25
            )
        else:
            self.sale_channel.play(self.sale_sound)
            self.duck_background_music(sound_length + 0.25)

    def nearest_interaction(self) -> dict | None:
        position = (self.player.x, self.player.y)
        candidates: list[tuple[float, dict]] = []
        now = time.time()
        for index, rect in enumerate(PLOT_RECTS[:self.state.active_plots]):
            gap = distance_to_rect(position, rect)
            if gap <= 84:
                plot = self.state.plots[index]
                if not plot.planted:
                    prompt = f"씨앗 심기 (보유 {self.state.seeds})"
                elif plot.is_ready(now):
                    prompt = f"블루베리 수확하기 (+{HARVEST_YIELD})"
                else:
                    prompt = f"자라는 중 · {int(plot.remaining(now)) + 1}초 남음"
                candidates.append((gap, {"kind": "plot", "index": index, "prompt": prompt,
                                         "point": rect.center}))

        order = self.state.current_order
        craft_prompt = (
            f"주문 스무디 만들기 · {order.short_text()}"
            if order is not None
            else "새 주문을 기다리는 중"
        )
        sell_prompt = (
            f"주문 스무디 판매 (+{order.price}코인 · 대기 {self.state.customers_waiting}명)"
            if order is not None
            else "새 손님을 기다리는 중"
        )
        fixed = [
            ("save", (HOUSE.centerx, HOUSE.bottom + 37), 82, "집 앞에서 농장 저장하기"),
            ("shop", (SHOP.centerx, SHOP.bottom + 42), 90, "재료 상점 들어가기"),
            ("craft", (CAFE.centerx, CAFE.bottom + 42), 90, craft_prompt),
            ("sell_raw", (MARKET.centerx, MARKET.bottom + 38), 88,
             f"블루베리 생과 1개 판매 (+{RAW_BERRY_PRICE}코인)"),
            ("sell_smoothie", (SMOOTHIE_CART.centerx, SMOOTHIE_CART.bottom + 38), 92,
             sell_prompt),
            ("land", (980, 650), 86,
             "농장 최대 확장 완료" if self.state.active_plots >= MAX_PLOTS
             else f"텃밭 1칸 구입하기 ({self.state.land_cost:,}코인)"),
        ]
        for kind, point, radius, prompt in fixed:
            gap = distance(position, point)
            if gap <= radius:
                candidates.append((gap, {"kind": kind, "prompt": prompt, "point": point}))
        return min(candidates, key=lambda item: item[0])[1] if candidates else None

    def interact(self) -> None:
        target = self.nearest_interaction()
        if target is None:
            self.notify("상호작용할 곳에 조금 더 가까이 가세요.", True)
            return
        kind = target["kind"]
        if kind == "plot":
            before = self.state.blueberries
            ok, message = self.state.use_plot(target["index"])
            if ok and self.state.blueberries > before:
                self.spawn_harvest_impact(
                    target["point"], self.state.blueberries - before
                )
            elif ok:
                self.action_effects.append(
                    ActionEffect(target["point"][0], target["point"][1] - 70,
                                 "씨앗을 심었어요!", GREEN_DARK)
                )
                self.action_timer = 0.28
            else:
                plot = self.state.plots[target["index"]]
                label = (
                    f"아직 {int(plot.remaining(time.time())) + 1}초"
                    if plot.planted and not plot.is_ready(time.time())
                    else "지금은 수확할 수 없어요"
                )
                self.action_effects.append(
                    ActionEffect(target["point"][0], target["point"][1] - 70,
                                 label, RED, life=0.95, duration=0.95)
                )
        elif kind == "shop":
            self.overlay = "shop"
            return
        elif kind == "save":
            self.save(announce=True)
            return
        elif kind == "craft":
            if self.state.current_order is None:
                self.notify("지금은 주문한 손님이 없어요.", True)
                return
            if self.state.prepared_order is not None:
                self.notify("이미 만든 주문 스무디를 먼저 판매해 주세요.", True)
                return
            self.blender_mix = {
                key: 0 for key, _label, _color in BLENDER_INGREDIENTS
            }
            self.blender_message = "재료의 + 버튼을 눌러 주문 수량을 직접 맞추세요."
            self.blender_message_error = False
            self.overlay = "blender"
            return
        elif kind == "sell_raw":
            ok, message = self.state.sell_blueberry()
            if ok:
                self.spawn_particles(target["point"], GOLD, 10)
        elif kind == "sell_smoothie":
            departing_style = self.state.smoothies_sold
            ok, message = self.state.sell_smoothie()
            if ok:
                front_x, front_y = CUSTOMER_QUEUE_POINTS[0]
                self.departing_customers.append(
                    DepartingCustomer(front_x, front_y, departing_style)
                )
                self.next_customer_at = time.time() + CUSTOMER_RETURN_SECONDS
                self.play_sale_sound()
                self.spawn_particles(target["point"], GOLD, 20)
        elif kind == "land":
            ok, message = self.state.buy_land()
            if ok:
                unlocked = PLOT_RECTS[self.state.active_plots - 1].center
                self.spawn_particles(unlocked, GOLD, 22)
        else:
            return
        self.notify(message, not ok)
        if ok:
            self.save()

    def buy_item(self, key: str) -> None:
        ok, message = self.state.buy_item(key)
        self.notify(message, not ok)
        if ok:
            self.save()

    def change_blender_ingredient(self, key: str, amount: int) -> None:
        if key not in self.blender_mix:
            return
        self.blender_mix[key] = max(0, min(9, self.blender_mix[key] + amount))
        self.blender_message = "주문표와 넣은 수량을 비교한 뒤 완성 버튼을 누르세요."
        self.blender_message_error = False

    def finish_blender_mix(self) -> None:
        ok, message = self.state.make_smoothie(self.blender_mix)
        if not ok:
            self.blender_message = message
            self.blender_message_error = True
            return
        self.blender_animation_remaining = BLENDER_DURATION
        self.blender_complete_message = message
        self.overlay = "blending"
        self.save()

    def close_help(self) -> None:
        self.overlay = None
        if not self.state.tutorial_seen:
            self.state.tutorial_seen = True
            self.save()

    @staticmethod
    def is_interaction_key(event: pygame.event.Event) -> bool:
        # SDL scancodes follow the physical key, so E keeps working even while a
        # Korean input source is selected. Space/Return are convenient fallbacks.
        return (
            event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN)
            or getattr(event, "scancode", None) == pygame.KSCAN_E
        )

    def handle_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_ESCAPE:
            if self.overlay == "blending":
                return
            if self.overlay:
                if self.overlay == "help":
                    self.close_help()
                else:
                    self.overlay = None
            else:
                self.running = False
            return
        if event.key == pygame.K_h:
            if self.overlay == "help":
                self.close_help()
            elif self.overlay is None:
                self.overlay = "help"
            return
        if (
            event.key == pygame.K_b
            or getattr(event, "scancode", None) == pygame.KSCAN_B
        ):
            if self.overlay == "blending":
                return
            if self.overlay == "bag":
                self.overlay = None
            elif self.overlay is None:
                self.overlay = "bag"
            return
        if event.key == pygame.K_m:
            self.bgm_muted = not self.bgm_muted
            self.current_bgm_volume = 0.0 if self.bgm_muted else BGM_NORMAL_VOLUME
            if not self.music_error:
                pygame.mixer.music.set_volume(self.current_bgm_volume)
            self.notify("배경음악을 껐어요." if self.bgm_muted else "배경음악을 켰어요.")
            return
        if event.key == pygame.K_s and (event.mod & (pygame.KMOD_CTRL | pygame.KMOD_META)):
            self.save(announce=True)
            return
        if self.overlay == "bag":
            if self.is_interaction_key(event):
                self.overlay = None
            return
        if self.overlay == "blender":
            shortcuts = {
                pygame.K_1: "blueberries",
                pygame.K_2: "honey",
                pygame.K_3: "milk",
                pygame.K_4: "ice",
            }
            if event.key in shortcuts:
                amount = -1 if event.mod & pygame.KMOD_SHIFT else 1
                self.change_blender_ingredient(shortcuts[event.key], amount)
            elif event.key == pygame.K_r:
                self.blender_mix = {
                    key: 0 for key, _label, _color in BLENDER_INGREDIENTS
                }
                self.blender_message = "재료를 모두 비웠어요. 다시 직접 넣어 보세요."
                self.blender_message_error = False
            elif event.key == pygame.K_RETURN:
                self.finish_blender_mix()
            return
        if self.overlay == "shop":
            shortcuts = {pygame.K_1: "seeds", pygame.K_2: "honey", pygame.K_3: "milk", pygame.K_4: "ice"}
            if event.key in shortcuts:
                self.buy_item(shortcuts[event.key])
            elif self.is_interaction_key(event):
                self.overlay = None
            return
        if self.overlay is None and self.is_interaction_key(event):
            self.interact()

    def handle_click(self, position: tuple[int, int]) -> None:
        if self.overlay == "help":
            if pygame.Rect(510, 616, 260, 55).collidepoint(position):
                self.close_help()
            return
        if self.overlay == "blender":
            if pygame.Rect(440, 550, 300, 56).collidepoint(position):
                self.finish_blender_mix()
                return
            if pygame.Rect(760, 550, 120, 56).collidepoint(position):
                self.blender_mix = {
                    key: 0 for key, _label, _color in BLENDER_INGREDIENTS
                }
                self.blender_message = "재료를 모두 비웠어요. 다시 직접 넣어 보세요."
                self.blender_message_error = False
                return
            if pygame.Rect(900, 550, 110, 56).collidepoint(position):
                self.overlay = None
                return
            for rect, key, _label, _color in self.blender_cards:
                minus = pygame.Rect(rect.x + 178, rect.y + 57, 40, 40)
                plus = pygame.Rect(rect.x + 268, rect.y + 57, 40, 40)
                if minus.collidepoint(position):
                    self.change_blender_ingredient(key, -1)
                    return
                if plus.collidepoint(position):
                    self.change_blender_ingredient(key, 1)
                    return
            return
        if self.overlay == "shop":
            if pygame.Rect(510, 520, 260, 52).collidepoint(position):
                self.overlay = None
                return
            for rect, key, _label, _color in self.shop_buttons:
                if rect.collidepoint(position):
                    self.buy_item(key)
                    return
        if self.overlay == "bag":
            if pygame.Rect(510, 614, 260, 48).collidepoint(position):
                self.overlay = None
            return
        if self.overlay is None and pygame.Rect(1168, 18, 92, 38).collidepoint(position):
            self.overlay = "help"

    def draw_ground(self) -> None:
        self.screen.fill(GRASS)
        # A 32 px ground grid is textured in small, hard-edged clusters for a
        # coherent pixel-art look without a transparency-breaking resize pass.
        tile = 32
        start_world_x = int(self.camera.x // tile) * tile
        start_world_y = int(self.camera.y // tile) * tile
        for world_y in range(start_world_y, int(self.camera.y) + SCREEN_H + tile, tile):
            for world_x in range(start_world_x, int(self.camera.x) + SCREEN_W + tile, tile):
                sx, sy = self.world_to_screen((world_x, world_y))
                value = ((world_x // tile) * 17 + (world_y // tile) * 31) % 11
                if value in (0, 7):
                    pygame.draw.rect(self.screen, (124, 182, 85), (sx, sy, tile, tile))
                if value in (2, 9):
                    pygame.draw.rect(self.screen, GRASS_LIGHT, (sx + 8, sy + 12, 3, 8))
                    pygame.draw.rect(self.screen, GRASS_DARK, (sx + 14, sy + 8, 3, 12))
                    pygame.draw.rect(self.screen, GRASS_LIGHT, (sx + 19, sy + 14, 3, 6))
        for x, y, color in self.flowers:
            sx, sy = self.world_to_screen((x, y))
            if -8 <= sx <= SCREEN_W + 8 and -8 <= sy <= SCREEN_H + 8:
                pygame.draw.rect(self.screen, GRASS_DARK, (sx, sy, 2, 7))
                pygame.draw.rect(self.screen, color, (sx - 3, sy - 2, 8, 4))
                pygame.draw.rect(self.screen, color, (sx - 1, sy - 4, 4, 8))
                pygame.draw.rect(self.screen, GOLD, (sx, sy - 1, 2, 2))

    def draw_path(self, rect: pygame.Rect) -> None:
        screen_rect = self.rect_to_screen(rect)
        pygame.draw.rect(self.screen, PATH_EDGE, screen_rect.inflate(8, 8))
        pygame.draw.rect(self.screen, PATH, screen_rect)
        pebble = (181, 137, 89)
        for x in range(screen_rect.left + 20, screen_rect.right, 40):
            y = screen_rect.centery + ((x // 40) % 3 - 1) * 14
            pygame.draw.rect(self.screen, pebble, (x, y, 6, 4))
            pygame.draw.rect(self.screen, (229, 193, 128), (x + 13, y + 19, 4, 3))

    def draw_paths(self) -> None:
        paths = [
            pygame.Rect(330, 285, 105, 690),
            pygame.Rect(375, 875, 1410, 108),
            pygame.Rect(1710, 390, 105, 750),
            pygame.Rect(1115, 920, 105, 320),
            pygame.Rect(1180, 920, 585, 90),
        ]
        for rect in paths:
            self.draw_path(rect)

    def draw_pond(self) -> None:
        rect = self.rect_to_screen(POND)
        pygame.draw.ellipse(self.screen, (70, 137, 110), rect.inflate(20, 18))
        pygame.draw.ellipse(self.screen, WATER, rect)
        pygame.draw.arc(self.screen, WATER_LIGHT, rect.inflate(-60, -70), 0.2, 2.5, 4)
        pygame.draw.arc(self.screen, WATER_LIGHT, rect.inflate(-150, -120), 3.2, 5.7, 3)
        for dx, dy in ((85, 100), (275, 175), (190, 60)):
            x, y = rect.x + dx, rect.y + dy
            pygame.draw.ellipse(self.screen, (74, 144, 72), (x - 15, y - 5, 30, 12))
            pygame.draw.line(self.screen, (209, 131, 177), (x, y - 3), (x, y - 15), 2)
            pygame.draw.circle(self.screen, (242, 183, 212), (x + 3, y - 17), 5)

    def draw_house(self, world_rect: pygame.Rect, title: str, wall: tuple[int, int, int],
                   roof: tuple[int, int, int], door_x: int | None = None) -> None:
        rect = self.rect_to_screen(world_rect)
        if rect.right < -100 or rect.left > SCREEN_W + 100 or rect.bottom < -120 or rect.top > SCREEN_H + 100:
            return
        pygame.draw.rect(self.screen, (58, 74, 43), rect.move(12, 14))
        pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(8, 8))
        pygame.draw.rect(self.screen, wall, rect)
        pygame.draw.rect(self.screen, tuple(max(0, c - 32) for c in wall),
                         (rect.x, rect.bottom - 25, rect.width, 25))
        for plank_y in range(rect.top + 24, rect.bottom - 25, 28):
            pygame.draw.line(self.screen, tuple(max(0, c - 18) for c in wall),
                             (rect.left, plank_y), (rect.right, plank_y), 3)
        roof_poly = [(rect.left - 28, rect.top + 43), (rect.centerx, rect.top - 82),
                     (rect.right + 28, rect.top + 43)]
        pygame.draw.polygon(self.screen, roof, roof_poly)
        pygame.draw.polygon(self.screen, tuple(max(0, c - 35) for c in roof), roof_poly, 5)
        for row, inset in enumerate((12, 28, 46, 64)):
            y = rect.top + 32 - row * 25
            pygame.draw.line(self.screen, tuple(max(0, c - 24) for c in roof),
                             (rect.left + inset, y), (rect.right - inset, y), 4)
        chimney = pygame.Rect(rect.right - 100, rect.top - 62, 36, 66)
        pygame.draw.rect(self.screen, WOOD_DARK, chimney.inflate(6, 4))
        pygame.draw.rect(self.screen, (151, 83, 66), chimney)
        pygame.draw.line(self.screen, (190, 112, 82), chimney.topleft,
                         (chimney.left + 22, chimney.top), 4)
        for window_x in (rect.left + 76, rect.right - 126):
            window = pygame.Rect(window_x, rect.top + 100, 56, 56)
            pygame.draw.rect(self.screen, WOOD_DARK, window.inflate(10, 10))
            pygame.draw.rect(self.screen, (111, 190, 203), window)
            pygame.draw.rect(self.screen, (187, 231, 220), (window.x + 6, window.y + 6, 17, 17))
            pygame.draw.line(self.screen, CREAM, (window.centerx, window.top), (window.centerx, window.bottom), 4)
            pygame.draw.line(self.screen, CREAM, (window.left, window.centery), (window.right, window.centery), 4)
            pygame.draw.rect(self.screen, (91, 128, 62), (window.x - 6, window.bottom + 5, 68, 9))
        dx = rect.centerx - 30 if door_x is None else int(door_x - self.camera.x - 30)
        pygame.draw.rect(self.screen, (53, 35, 33), (dx - 5, rect.bottom - 90, 70, 90))
        pygame.draw.rect(self.screen, WOOD, (dx, rect.bottom - 84, 60, 84))
        for line_y in range(rect.bottom - 72, rect.bottom - 5, 16):
            pygame.draw.line(self.screen, (111, 65, 44), (dx + 5, line_y), (dx + 55, line_y), 2)
        pygame.draw.rect(self.screen, GOLD, (dx + 45, rect.bottom - 44, 6, 6))
        sign = pygame.Rect(rect.centerx - 108, rect.top + 42, 216, 42)
        pygame.draw.rect(self.screen, WOOD_DARK, sign.inflate(8, 8))
        pygame.draw.rect(self.screen, CREAM, sign)
        self.text(title, 17, INK, sign.centerx, sign.centery, center=True)

    def draw_market(self) -> None:
        rect = self.rect_to_screen(MARKET)
        pygame.draw.rect(self.screen, (56, 72, 42), rect.move(12, 12))
        pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(8, 8))
        pygame.draw.rect(self.screen, WOOD, rect)
        pygame.draw.rect(self.screen, CREAM, (rect.x + 20, rect.y + 55, rect.width - 40, rect.height - 65))
        stripe_w = rect.width // 8
        for index in range(8):
            color = RED if index % 2 == 0 else CREAM
            pygame.draw.polygon(self.screen, color, [
                (rect.x + index * stripe_w, rect.y + 5),
                (rect.x + (index + 1) * stripe_w, rect.y + 5),
                (rect.x + (index + 1) * stripe_w - 7, rect.y + 55),
                (rect.x + index * stripe_w + 7, rect.y + 55),
            ])
        pygame.draw.line(self.screen, WOOD_DARK, (rect.x + 20, rect.y + 55), (rect.right - 20, rect.y + 55), 5)
        self.text("블루베리 생과 시장", 20, INK, rect.centerx, rect.y + 92, center=True)
        icon = self.ingredient_icons.get("blueberries")
        if icon is not None:
            self.screen.blit(icon, icon.get_rect(center=(rect.centerx, rect.y + 130)))
        else:
            for i in range(5):
                bx = rect.centerx - 38 + i * 19
                pygame.draw.rect(self.screen, BLUEBERRY_DARK, (bx - 7, rect.y + 126, 15, 15))
                pygame.draw.rect(self.screen, BLUEBERRY, (bx - 5, rect.y + 128, 11, 11))
        self.text(f"한 알 {RAW_BERRY_PRICE}코인", 15, MUTED, rect.centerx, rect.y + 161, center=True)

    def draw_smoothie_cart(self) -> None:
        rect = self.rect_to_screen(SMOOTHIE_CART)
        pygame.draw.rect(self.screen, (56, 72, 42), rect.move(12, 12))
        pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(8, 8))
        pygame.draw.rect(self.screen, (198, 164, 209), rect)
        pygame.draw.rect(self.screen, BLUEBERRY_DARK, (rect.x, rect.y, rect.width, 48))
        self.text("BLUEBERRY SMOOTHIE", 20, WHITE, rect.centerx, rect.y + 24, center=True)
        for x in (rect.left + 64, rect.right - 64):
            pygame.draw.rect(self.screen, INK, (x - 24, rect.bottom - 18, 48, 38))
            pygame.draw.rect(self.screen, (139, 130, 146), (x - 10, rect.bottom - 8, 20, 20))
        cup_x, cup_y = rect.centerx, rect.y + 104
        pygame.draw.polygon(self.screen, (183, 100, 184), [
            (cup_x - 22, cup_y - 25), (cup_x + 22, cup_y - 25),
            (cup_x + 16, cup_y + 27), (cup_x - 16, cup_y + 27),
        ])
        pygame.draw.line(self.screen, (87, 70, 92), (cup_x + 7, cup_y - 25), (cup_x + 18, cup_y - 48), 4)
        for plank_y in (rect.y + 70, rect.y + 120):
            pygame.draw.line(self.screen, (161, 123, 178), (rect.x + 18, plank_y), (rect.right - 18, plank_y), 3)

        queue_badge = pygame.Rect(rect.right - 145, rect.y + 57, 122, 31)
        pygame.draw.rect(self.screen, WOOD_DARK, queue_badge.inflate(4, 4))
        pygame.draw.rect(self.screen, CREAM, queue_badge)
        self.text(
            f"대기 {self.state.customers_waiting}명",
            14,
            BLUEBERRY_DARK,
            queue_badge.centerx,
            queue_badge.centery,
            center=True,
        )

    def draw_customer(
        self,
        point: tuple[float, float],
        style: int,
        *,
        departing: bool = False,
        order: CustomerOrder | None = None,
        front: bool = False,
    ) -> None:
        x, y = self.world_to_screen(point)
        if not (-60 < x < SCREEN_W + 60 and -110 < y < SCREEN_H + 60):
            return
        skin, hair, shirt = CUSTOMER_STYLES[style % len(CUSTOMER_STYLES)]
        step = 4 if departing and int(time.time() * 10) % 2 else 0

        pygame.draw.ellipse(self.screen, (55, 98, 47), (x - 22, y - 8, 44, 12))
        pygame.draw.rect(self.screen, INK, (x - 14 + step, y - 20, 10, 20))
        pygame.draw.rect(self.screen, INK, (x + 4 - step, y - 20, 10, 20))
        pygame.draw.rect(self.screen, tuple(max(0, value - 40) for value in shirt),
                         (x - 18, y - 51, 36, 34))
        pygame.draw.rect(self.screen, shirt, (x - 15, y - 49, 30, 29))

        if departing:
            pygame.draw.rect(self.screen, skin, (x - 25, y - 59, 9, 27))
            pygame.draw.rect(self.screen, skin, (x + 16, y - 68, 9, 32))
            pygame.draw.rect(self.screen, skin, (x + 19, y - 76, 8, 10))
        else:
            pygame.draw.rect(self.screen, skin, (x - 23, y - 48, 8, 25))
            pygame.draw.rect(self.screen, skin, (x + 15, y - 48, 8, 25))
            pygame.draw.circle(self.screen, GOLD, (x - 19, y - 27), 5)
            pygame.draw.circle(self.screen, CREAM, (x - 19, y - 27), 2)

        pygame.draw.rect(self.screen, hair, (x - 19, y - 87, 38, 27))
        pygame.draw.rect(self.screen, skin, (x - 16, y - 79, 32, 27))
        pygame.draw.rect(self.screen, hair, (x - 19, y - 84, 9, 31))
        pygame.draw.rect(self.screen, hair, (x - 10, y - 87, 30, 8))
        pygame.draw.rect(self.screen, INK, (x - 11, y - 69, 5, 5))
        pygame.draw.rect(self.screen, (190, 81, 88), (x - 6, y - 59, 8, 3))

        if front and order is not None and not departing:
            bubble = pygame.Rect(x - 139, y - 185, 278, 77)
            rounded_rect(self.screen, bubble, (255, 250, 225), 12, WOOD_DARK, 3)
            pygame.draw.polygon(
                self.screen,
                (255, 250, 225),
                [(x - 10, bubble.bottom - 2), (x + 8, bubble.bottom - 2), (x, bubble.bottom + 14)],
            )
            pygame.draw.lines(
                self.screen,
                WOOD_DARK,
                False,
                [(x - 10, bubble.bottom), (x, bubble.bottom + 14), (x + 8, bubble.bottom)],
                3,
            )
            self.text("앞 손님의 주문", 13, BLUEBERRY_DARK, bubble.centerx, bubble.y + 17,
                      center=True)
            self.text(
                f"블루베리 3  꿀 {order.honey}  우유 {order.milk}  얼음 {order.ice}",
                14,
                INK,
                bubble.centerx,
                bubble.y + 40,
                center=True,
            )
            self.text(f"받을 돈  {order.price}코인", 13, RED, bubble.centerx, bubble.y + 61,
                      center=True)

    def draw_farm_fence(self) -> None:
        farm = self.rect_to_screen(pygame.Rect(225, 350, 720, 550))
        color = (177, 119, 63)
        for y in (farm.top, farm.bottom):
            pygame.draw.line(self.screen, WOOD_DARK, (farm.left, y + 3), (farm.right, y + 3), 10)
            pygame.draw.line(self.screen, color, (farm.left, y), (farm.right, y), 6)
        pygame.draw.line(self.screen, WOOD_DARK, farm.topleft, farm.bottomleft, 10)
        pygame.draw.line(self.screen, color, farm.topleft, farm.bottomleft, 6)
        pygame.draw.line(self.screen, WOOD_DARK, farm.topright, farm.bottomright, 10)
        pygame.draw.line(self.screen, color, farm.topright, farm.bottomright, 6)
        for x in range(farm.left, farm.right + 1, 60):
            for y in (farm.top, farm.bottom):
                pygame.draw.rect(self.screen, WOOD_DARK, (x - 7, y - 14, 14, 30))
                pygame.draw.rect(self.screen, color, (x - 4, y - 10, 8, 21))
                pygame.draw.polygon(self.screen, color, [(x - 4, y - 10), (x, y - 17), (x + 4, y - 10)])
        sign = pygame.Rect(farm.left + 10, farm.top - 43, 220, 42)
        pygame.draw.rect(self.screen, WOOD_DARK, sign.inflate(8, 8))
        pygame.draw.rect(self.screen, (239, 199, 126), sign)
        self.text("나의 블루베리 밭", 18, INK, sign.centerx, sign.centery, center=True)

    def draw_bush(self, rect: pygame.Rect, progress: float, ready: bool) -> None:
        cx, base_y = rect.centerx, rect.bottom - 21
        if progress < 0.18:
            pygame.draw.rect(self.screen, GREEN_DARK, (cx - 2, base_y - 25, 5, 27))
            pygame.draw.rect(self.screen, LEAF, (cx - 18, base_y - 25, 17, 9))
            pygame.draw.rect(self.screen, GREEN, (cx + 2, base_y - 34, 17, 9))
            return
        scale = 0.62 + progress * 0.38
        pygame.draw.rect(self.screen, WOOD_DARK, (cx - 3, base_y - 50, 7, 54))
        for dx, dy, width, height in ((-31, -40, 38, 30), (-13, -59, 42, 35),
                                      (13, -47, 40, 32), (-15, -35, 54, 32)):
            w, h = int(width * scale), int(height * scale)
            x, y = cx + int(dx * scale), base_y + int(dy * scale)
            color = LEAF if dx % 2 else GREEN
            pygame.draw.rect(self.screen, GREEN_DARK, (x - 3, y + 3, w, h))
            pygame.draw.rect(self.screen, color, (x, y, w - 4, h - 5))
            pygame.draw.rect(self.screen, GRASS_LIGHT, (x + 5, y + 5, 8, 5))
        positions = [(-25, -39), (-5, -58), (18, -45), (28, -25), (0, -28), (-21, -18), (15, -16), (1, -45)]
        count = 0 if progress < 0.62 else (4 if not ready else len(positions))
        for dx, dy in positions[:count]:
            x, y = cx + int(dx * scale), base_y + int(dy * scale)
            pygame.draw.rect(self.screen, BLUEBERRY_DARK, (x - 6, y - 5, 13, 13))
            pygame.draw.rect(self.screen, BLUEBERRY, (x - 4, y - 4, 9, 9))
            pygame.draw.rect(self.screen, (205, 194, 240), (x - 3, y - 3, 3, 3))
        if ready:
            pygame.draw.rect(self.screen, WOOD_DARK, (rect.right - 22, rect.top - 5, 26, 26))
            pygame.draw.rect(self.screen, GOLD, (rect.right - 19, rect.top - 2, 20, 20))
            self.text("!", 16, INK, rect.right - 9, rect.top + 8, center=True)

    def draw_plots(self) -> None:
        now = time.time()
        for index, world_rect in enumerate(PLOT_RECTS):
            rect = self.rect_to_screen(world_rect)
            if index >= self.state.active_plots:
                pygame.draw.rect(self.screen, (104, 156, 78), rect)
                pygame.draw.rect(self.screen, GRASS_DARK, rect, 4)
                for dx in (25, 58, 91):
                    pygame.draw.line(self.screen, (90, 137, 67), (rect.x + dx, rect.bottom - 12),
                                     (rect.x + dx - 8, rect.y + 16), 3)
                pygame.draw.rect(self.screen, (183, 145, 68),
                                 (rect.centerx - 16, rect.centery - 16, 32, 32))
                self.text("×", 20, INK, rect.centerx, rect.centery, center=True)
                continue
            pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(8, 8))
            pygame.draw.rect(self.screen, SOIL_LIGHT, rect)
            pygame.draw.rect(self.screen, SOIL, rect.inflate(-8, -8))
            for line in range(3):
                y = rect.y + 19 + line * 25
                pygame.draw.line(self.screen, SOIL_LIGHT, (rect.x + 10, y), (rect.right - 10, y), 5)
                for x in range(rect.x + 18, rect.right - 8, 24):
                    pygame.draw.rect(self.screen, (104, 62, 43), (x, y + 5, 8, 3))
            plot = self.state.plots[index]
            if plot.planted:
                self.draw_bush(rect, plot.progress(now), plot.is_ready(now))
            else:
                pygame.draw.rect(self.screen, (83, 50, 37), (rect.centerx - 4, rect.centery - 4, 8, 8))
                self.text("빈 밭", 13, CREAM, rect.centerx, rect.centery - 20, center=True)

    def draw_expansion_sign(self) -> None:
        x, y = self.world_to_screen((980, 650))
        pygame.draw.rect(self.screen, WOOD_DARK, (x - 6, y - 5, 12, 58))
        pygame.draw.rect(self.screen, WOOD, (x - 3, y - 3, 6, 53))
        sign = pygame.Rect(x - 94, y - 45, 188, 48)
        pygame.draw.rect(self.screen, WOOD_DARK, sign.inflate(8, 8))
        pygame.draw.rect(self.screen, (239, 199, 126), sign)
        label = (
            "최대 확장"
            if self.state.active_plots >= MAX_PLOTS
            else f"새 텃밭 {self.state.land_cost:,}코인"
        )
        self.text(label, 15, INK, sign.centerx, sign.centery, center=True)

    def draw_tree(self, point: tuple[int, int]) -> None:
        x, y = self.world_to_screen(point)
        if not (-100 < x < SCREEN_W + 100 and -140 < y < SCREEN_H + 100):
            return
        pygame.draw.rect(self.screen, (61, 107, 51), (x - 38, y + 14, 76, 12))
        pygame.draw.rect(self.screen, WOOD_DARK, (x - 12, y - 31, 24, 63))
        pygame.draw.rect(self.screen, WOOD, (x - 7, y - 28, 14, 57))
        clusters = [(-39, -80, 54, 48), (-10, -104, 58, 57), (27, -77, 53, 48), (-23, -56, 72, 52)]
        for index, (dx, dy, width, height) in enumerate(clusters):
            pygame.draw.rect(self.screen, GREEN_DARK, (x + dx - 4, y + dy + 4, width + 4, height + 4))
            pygame.draw.rect(self.screen, LEAF if index % 2 else GREEN, (x + dx, y + dy, width, height))
            pygame.draw.rect(self.screen, GRASS_LIGHT, (x + dx + 9, y + dy + 8, 14, 8))
        pygame.draw.rect(self.screen, (189, 203, 102), (x - 27, y - 96, 10, 10))

    def draw_interaction_marker(self) -> None:
        target = self.nearest_interaction()
        if target is None or self.overlay is not None:
            return
        x, y = self.world_to_screen(target["point"])
        pulse = 3 * math.sin(time.time() * 5)
        pygame.draw.circle(self.screen, (255, 247, 177), (x, y - 42), int(18 + pulse))
        pygame.draw.circle(self.screen, BLUEBERRY_DARK, (x, y - 42), 15)
        self.text("E", 16, WHITE, x, y - 42, center=True)

    def draw_harvest_basket(self, x: int, y: int) -> None:
        offsets = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}
        dx, dy = offsets[self.direction]
        basket_x = x - 18 + dx * 29
        basket_y = y - 40 + dy * 32
        pygame.draw.rect(self.screen, WOOD_DARK, (basket_x - 3, basket_y - 3, 42, 28))
        pygame.draw.rect(self.screen, (190, 128, 62), (basket_x, basket_y, 36, 22))
        pygame.draw.rect(self.screen, (235, 181, 88), (basket_x + 4, basket_y + 5, 28, 5))
        for berry_x, berry_y in ((7, 2), (17, 6), (26, 2), (12, 12), (23, 13)):
            pygame.draw.rect(self.screen, BLUEBERRY_DARK,
                             (basket_x + berry_x, basket_y + berry_y, 8, 8))
            pygame.draw.rect(self.screen, BLUEBERRY,
                             (basket_x + berry_x + 2, basket_y + berry_y + 1, 5, 5))

    def draw_character(self) -> None:
        x, y = self.world_to_screen((self.player.x, self.player.y))
        if self.player_frames:
            pygame.draw.rect(self.screen, (55, 98, 47), (x - 24, y - 7, 48, 10))
            frame_index = 0
            if self.is_moving:
                frame_index = 1 + (int(self.walk_phase / 2) % 2)
            frame = self.player_frames[self.direction][frame_index]
            self.screen.blit(frame, frame.get_rect(midbottom=(x, y + 2)))
            if self.action_timer > 0:
                self.draw_harvest_basket(x, y)
            return

        # Safe code-drawn fallback in case the sprite asset cannot be loaded.
        stride = 4 if self.is_moving and math.sin(self.walk_phase) > 0 else -4
        skin = (238, 184, 145)
        pants = (53, 54, 73)
        hair = (71, 45, 39)
        pygame.draw.rect(self.screen, (55, 98, 47), (x - 20, y - 7, 40, 10))
        pygame.draw.rect(self.screen, INK, (x - 14 + stride, y - 17, 10, 18))
        pygame.draw.rect(self.screen, INK, (x + 4 - stride, y - 17, 10, 18))
        pygame.draw.rect(self.screen, pants, (x - 14, y - 28, 28, 18))
        pygame.draw.rect(self.screen, BLUEBERRY_DARK, (x - 20, y - 58, 40, 33))
        pygame.draw.rect(self.screen, BLUEBERRY, (x - 15, y - 55, 30, 27))
        arm_shift = 4 if self.direction == "right" else (-4 if self.direction == "left" else 0)
        pygame.draw.rect(self.screen, INK, (x - 24 + arm_shift, y - 52, 10, 24))
        pygame.draw.rect(self.screen, skin, (x - 21 + arm_shift, y - 48, 7, 17))
        pygame.draw.rect(self.screen, INK, (x + 14 + arm_shift, y - 52, 10, 24))
        pygame.draw.rect(self.screen, skin, (x + 14 + arm_shift, y - 48, 7, 17))
        pygame.draw.rect(self.screen, hair, (x - 19, y - 84, 38, 32))
        pygame.draw.rect(self.screen, skin, (x - 15, y - 80, 30, 28))
        pygame.draw.rect(self.screen, hair, (x - 15, y - 82, 30, 8))
        pygame.draw.rect(self.screen, hair, (x - 19, y - 77, 7, 23))
        pygame.draw.rect(self.screen, hair, (x + 12, y - 77, 7, 23))
        # Straw hat: strong silhouette, like classic 16-bit farming games.
        pygame.draw.rect(self.screen, WOOD_DARK, (x - 29, y - 93, 58, 8))
        pygame.draw.rect(self.screen, (226, 184, 72), (x - 26, y - 96, 52, 8))
        pygame.draw.rect(self.screen, (232, 195, 88), (x - 17, y - 108, 34, 14))
        pygame.draw.rect(self.screen, (172, 104, 51), (x - 17, y - 98, 34, 5))
        if self.direction != "up":
            eye_dx = 4 if self.direction == "right" else (-4 if self.direction == "left" else 0)
            pygame.draw.rect(self.screen, INK, (x - 8 + eye_dx, y - 69, 4, 5))
            pygame.draw.rect(self.screen, INK, (x + 5 + eye_dx, y - 69, 4, 5))
            pygame.draw.rect(self.screen, RED, (x - 3 + eye_dx, y - 59, 7, 3))
        pygame.draw.rect(self.screen, BLUEBERRY_DARK, (x + 13, y - 57, 13, 13))
        pygame.draw.rect(self.screen, BLUEBERRY, (x + 15, y - 55, 9, 9))
        if self.action_timer > 0:
            self.draw_harvest_basket(x, y)

    def draw_particles(self) -> None:
        for particle in self.particles:
            x, y = self.world_to_screen((particle.x, particle.y))
            pygame.draw.circle(self.screen, particle.color, (x, y), max(1, int(particle.size * particle.life)))

    def draw_action_effects(self) -> None:
        for effect in self.action_effects:
            x, y = self.world_to_screen((effect.x, effect.y))
            progress = 1.0 - effect.life / effect.duration
            lift = int(math.sin(min(1.0, progress) * math.pi) * 8)
            image = self.fonts[20].render(effect.label, True, WHITE)
            box = image.get_rect(center=(x, y - lift)).inflate(30, 18)
            alpha = min(255, int(effect.life / 0.3 * 255))
            badge = pygame.Surface(box.size, pygame.SRCALPHA)
            pygame.draw.rect(badge, (*effect.color, alpha), badge.get_rect())
            pygame.draw.rect(badge, (*GOLD, alpha), badge.get_rect(), 4)
            self.screen.blit(badge, box)
            image.set_alpha(alpha)
            self.screen.blit(image, image.get_rect(center=box.center))

    def draw_impact_flash(self) -> None:
        if self.impact_timer <= 0:
            return
        alpha = int(42 * self.impact_timer / 0.28)
        flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        flash.fill((190, 174, 255, alpha))
        self.screen.blit(flash, (0, 0))

    def draw_world_labels(self) -> None:
        labels = [
            ((HOUSE.centerx, HOUSE.bottom + 32), "집 · 저장"),
            ((SHOP.centerx, SHOP.bottom + 34), "재료 상점"),
            ((CAFE.centerx, CAFE.bottom + 34), "스무디 만들기"),
            ((MARKET.centerx, MARKET.bottom + 32), "생과 판매"),
            ((SMOOTHIE_CART.centerx, SMOOTHIE_CART.bottom + 34), "스무디 판매"),
        ]
        for point, label in labels:
            x, y = self.world_to_screen(point)
            if -150 < x < SCREEN_W + 150 and -40 < y < SCREEN_H + 40:
                width = self.fonts[14].size(label)[0] + 24
                rect = pygame.Rect(x - width // 2, y - 17, width, 29)
                rounded_rect(self.screen, rect, (255, 250, 225), 10, WOOD_DARK, 2)
                self.text(label, 14, INK, rect.centerx, rect.centery, center=True)

    def draw_world(self) -> None:
        self.draw_ground()
        self.draw_paths()
        self.draw_pond()
        self.draw_farm_fence()
        self.draw_plots()
        self.draw_expansion_sign()
        self.draw_house(HOUSE, "블루베리 농장집", (244, 210, 151), (112, 73, 72))
        self.draw_house(SHOP, "꿀 · 우유 · 얼음 상점", (240, 223, 174), (64, 124, 101))
        self.draw_house(CAFE, "블루베리 블렌더", (229, 205, 238), (112, 79, 157))
        self.draw_market()
        self.draw_smoothie_cart()
        customers: list[
            tuple[tuple[float, float], int, bool, CustomerOrder | None, bool]
        ] = [
            (
                point,
                self.state.smoothies_sold + index,
                False,
                self.state.customer_orders[index]
                if index < len(self.state.customer_orders)
                else None,
                index == 0,
            )
            for index, point in enumerate(
                CUSTOMER_QUEUE_POINTS[:self.state.customers_waiting]
            )
        ]
        customers.extend(
            ((customer.x, customer.y), customer.style, True, None, False)
            for customer in self.departing_customers
        )
        for tree in sorted((tree for tree in TREE_POSITIONS if tree[1] <= self.player.y), key=lambda item: item[1]):
            self.draw_tree(tree)
        for point, style, departing, order, front in sorted(
            (customer for customer in customers if customer[0][1] <= self.player.y),
            key=lambda customer: customer[0][1],
        ):
            self.draw_customer(point, style, departing=departing, order=order, front=front)
        self.draw_particles()
        self.draw_character()
        for tree in sorted((tree for tree in TREE_POSITIONS if tree[1] > self.player.y), key=lambda item: item[1]):
            self.draw_tree(tree)
        for point, style, departing, order, front in sorted(
            (customer for customer in customers if customer[0][1] > self.player.y),
            key=lambda customer: customer[0][1],
        ):
            self.draw_customer(point, style, departing=departing, order=order, front=front)
        self.draw_interaction_marker()

    def current_objective(self) -> str:
        state = self.state
        if state.berries_harvested == 0:
            return "익은 블루베리 나무 가까이 가서 E로 수확하세요."
        if state.blueberries < 3 and state.smoothies_sold == 0:
            return "밭을 돌보거나 남쪽 시장에서 생과를 팔아 보세요."
        if state.active_plots < MAX_PLOTS and state.money >= state.land_cost:
            return f"확장 간판에서 다음 텃밭을 {state.land_cost:,}코인에 살 수 있어요."
        order = state.current_order
        if order is None:
            return "새 손님과 주문을 기다리고 있어요."
        if state.smoothies < 1:
            return (
                f"앞 주문: 블루베리 3 · 꿀 {order.honey} · 우유 {order.milk} · "
                f"얼음 {order.ice} → {order.price}코인"
            )
        return f"완성된 주문 스무디를 카트에서 팔면 {order.price}코인을 받아요."

    def game_clock(self) -> tuple[int, int, int, float]:
        elapsed = max(0.0, self.state.game_elapsed_seconds)
        day = int(elapsed // DAY_SECONDS) + 1
        phase = (elapsed % DAY_SECONDS) / DAY_SECONDS
        total_minutes = 6 * 60 + int(phase * 16 * 60)
        return day, total_minutes // 60, total_minutes % 60, phase

    def draw_lighting(self) -> None:
        _day, _hour, _minute, phase = self.game_clock()
        if phase < 0.12:
            alpha = int((0.12 - phase) / 0.12 * 22)
            color = (111, 73, 105, alpha)
        elif phase > 0.72:
            alpha = min(68, int((phase - 0.72) / 0.28 * 68))
            color = (35, 43, 89, alpha)
        else:
            return
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill(color)
        self.screen.blit(overlay, (0, 0))

    def draw_hud(self) -> None:
        left = pygame.Rect(14, 14, 440, 78)
        pygame.draw.rect(self.screen, (45, 43, 39), left.move(5, 6))
        pygame.draw.rect(self.screen, WOOD_DARK, left.inflate(6, 6))
        pygame.draw.rect(self.screen, (224, 184, 111), left)
        pygame.draw.rect(self.screen, (247, 218, 148), left.inflate(-8, -8))
        self.text("블루베리 밸리", 22, BLUEBERRY_DARK, 32, 27)
        stats = [
            ("코인", self.state.money, GOLD),
            ("열매", self.state.blueberries, BLUEBERRY),
            ("씨앗", self.state.seeds, GREEN),
            ("스무디", self.state.smoothies, (182, 82, 160)),
        ]
        x = 202
        for label, value, color in stats:
            pygame.draw.rect(self.screen, WOOD_DARK, (x, 34, 13, 13))
            pygame.draw.rect(self.screen, color, (x + 2, 36, 9, 9))
            self.text(label, 13, MUTED, x + 17, 25)
            self.text(str(value), 18, INK, x + 17, 46)
            x += 61

        objective = pygame.Rect(470, 14, 510, 78)
        pygame.draw.rect(self.screen, (45, 43, 39), objective.move(5, 6))
        pygame.draw.rect(self.screen, WOOD_DARK, objective.inflate(6, 6))
        pygame.draw.rect(self.screen, (246, 224, 165), objective)
        self.text("오늘의 농장 일", 14, BLUEBERRY_DARK, 490, 26)
        self.wrapped_text(self.current_objective(), 15, INK, pygame.Rect(490, 49, 470, 34))

        right = pygame.Rect(996, 14, 270, 78)
        pygame.draw.rect(self.screen, (45, 43, 39), right.move(5, 6))
        pygame.draw.rect(self.screen, WOOD_DARK, right.inflate(6, 6))
        pygame.draw.rect(self.screen, (224, 184, 111), right)
        pygame.draw.rect(self.screen, (247, 218, 148), right.inflate(-8, -8))
        day, hour, minute, _phase = self.game_clock()
        self.text(f"{day}일차", 14, MUTED, 1013, 25)
        self.text(f"{hour:02d}:{minute:02d}", 22, INK, 1013, 45)
        self.text(f"꿀 {self.state.honey}  우유 {self.state.milk}  얼음 {self.state.ice}", 13, INK, 1090, 61)
        self.text(f"밭 {self.state.active_plots}/{MAX_PLOTS}", 13, INK, 1090, 39)
        help_rect = pygame.Rect(1170, 20, 88, 34)
        pygame.draw.rect(self.screen, WOOD_DARK, help_rect.inflate(4, 4))
        pygame.draw.rect(self.screen, PURPLE_LIGHT, help_rect)
        self.text("도움말 H", 14, BLUEBERRY_DARK, help_rect.centerx, help_rect.centery, center=True)

    def draw_prompt(self) -> None:
        target = self.nearest_interaction()
        if target is None or self.overlay is not None:
            return
        label = "E  " + target["prompt"]
        width = min(700, max(330, self.fonts[17].size(label)[0] + 58))
        rect = pygame.Rect((SCREEN_W - width) // 2, 640, width, 58)
        pygame.draw.rect(self.screen, (42, 43, 39), rect.move(6, 6))
        pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(6, 6))
        pygame.draw.rect(self.screen, (244, 216, 151), rect)
        pygame.draw.rect(self.screen, (255, 234, 178), rect.inflate(-7, -7))
        key_rect = pygame.Rect(rect.x + 13, rect.y + 10, 38, 38)
        pygame.draw.rect(self.screen, BLUEBERRY_DARK, key_rect.inflate(4, 4))
        pygame.draw.rect(self.screen, BLUEBERRY, key_rect)
        self.text("E", 18, WHITE, key_rect.centerx, key_rect.centery, center=True)
        self.text(target["prompt"], 17, INK, rect.x + 65, rect.y + 18)

    def draw_toast(self) -> None:
        if time.time() >= self.toast_until:
            return
        width = min(720, max(340, self.fonts[16].size(self.toast)[0] + 50))
        rect = pygame.Rect((SCREEN_W - width) // 2, 110, width, 44)
        pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(6, 6))
        pygame.draw.rect(self.screen, (179, 94, 91) if self.toast_error else (80, 112, 78), rect)
        pygame.draw.rect(self.screen, (212, 129, 119) if self.toast_error else (118, 150, 92), rect.inflate(-6, -6))
        self.text(self.toast, 16, WHITE, rect.centerx, rect.centery, center=True)

    def draw_shop_overlay(self) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((31, 26, 39, 165))
        self.screen.blit(shade, (0, 0))
        card = pygame.Rect(330, 130, 620, 470)
        pygame.draw.rect(self.screen, (32, 30, 31), card.move(10, 10))
        pygame.draw.rect(self.screen, WOOD_DARK, card.inflate(14, 14))
        pygame.draw.rect(self.screen, WOOD, card)
        pygame.draw.rect(self.screen, CREAM, card.inflate(-18, -18))
        self.text("동네 재료 상점", 32, BLUEBERRY_DARK, card.centerx, 175, center=True)
        self.text(f"보유 코인  {self.state.money}", 18, INK, card.centerx, 215, center=True)
        amounts = {"seeds": self.state.seeds, "honey": self.state.honey,
                   "milk": self.state.milk, "ice": self.state.ice}
        for index, (rect, key, label, color) in enumerate(self.shop_buttons, start=1):
            affordable = self.state.money >= ITEM_COSTS[key]
            fill = color if affordable else (174, 168, 177)
            pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(6, 6))
            pygame.draw.rect(self.screen, fill, rect)
            pygame.draw.rect(self.screen, tuple(min(255, channel + 18) for channel in fill), rect.inflate(-8, -8), 3)
            icon = self.ingredient_icons.get(key)
            text_center_x = rect.centerx
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=(rect.x + 39, rect.centery)))
                text_center_x += 25
            self.text(f"[{index}] {label} 1개", 18, WHITE,
                      text_center_x, rect.y + 24, center=True)
            self.text(f"{ITEM_COSTS[key]}코인 · 보유 {amounts[key]}", 14, WHITE,
                      text_center_x, rect.y + 53, center=True)
        close = pygame.Rect(510, 520, 260, 52)
        pygame.draw.rect(self.screen, WOOD_DARK, close.inflate(6, 6))
        pygame.draw.rect(self.screen, BLUEBERRY, close)
        self.text("가게 나가기  E", 18, WHITE, close.centerx, close.centery, center=True)

    def draw_blender_overlay(self) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((31, 26, 39, 178))
        self.screen.blit(shade, (0, 0))
        card = pygame.Rect(200, 45, 880, 620)
        pygame.draw.rect(self.screen, (30, 28, 34), card.move(11, 11))
        pygame.draw.rect(self.screen, WOOD_DARK, card.inflate(14, 14))
        pygame.draw.rect(self.screen, (130, 91, 151), card)
        pygame.draw.rect(self.screen, CREAM, card.inflate(-18, -18))
        self.text("내 손으로 만드는 주문 스무디", 32, BLUEBERRY_DARK,
                  card.centerx, 84, center=True)
        self.text("+ / - 버튼으로 직접 담기 · 숫자키 1~4로 추가 · Shift+숫자키로 빼기",
                  14, MUTED, card.centerx, 119, center=True)

        order = self.state.current_order
        ticket = pygame.Rect(280, 143, 730, 82)
        rounded_rect(self.screen, ticket, (255, 247, 211), 12, WOOD_DARK, 3)
        if order is not None:
            self.text("맨 앞 손님의 주문표", 15, BLUEBERRY_DARK,
                      ticket.centerx, ticket.y + 18, center=True)
            self.text(
                f"블루베리 3   꿀 {order.honey}   우유 {order.milk}   얼음 {order.ice}",
                20,
                INK,
                ticket.centerx,
                ticket.y + 46,
                center=True,
            )
            self.text(f"완성 판매가  {order.price}코인", 14, RED,
                      ticket.centerx, ticket.y + 69, center=True)
        else:
            self.text("현재 기다리는 주문이 없어요.", 18, MUTED,
                      ticket.centerx, ticket.centery, center=True)

        for index, (rect, key, label, color) in enumerate(self.blender_cards, start=1):
            rounded_rect(self.screen, rect, (249, 232, 186), 12, WOOD_DARK, 3)
            icon = self.ingredient_icons.get(key)
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=(rect.x + 40, rect.y + 31)))
            else:
                pygame.draw.rect(self.screen, color, (rect.x + 16, rect.y + 17, 18, 18))
            self.text(f"[{index}] {label}", 20, INK, rect.x + 72, rect.y + 12)
            ordered = getattr(order, key) if order is not None else 0
            self.text(f"주문 {ordered} · 보유 {self.state.inventory(key)}", 14, MUTED,
                      rect.x + 18, rect.y + 55)

            minus = pygame.Rect(rect.x + 178, rect.y + 57, 40, 40)
            plus = pygame.Rect(rect.x + 268, rect.y + 57, 40, 40)
            rounded_rect(self.screen, minus, (202, 174, 157), 8, WOOD_DARK, 2)
            rounded_rect(self.screen, plus, color, 8, WOOD_DARK, 2)
            self.text("-", 25, INK, minus.centerx, minus.centery - 1, center=True)
            self.text(str(self.blender_mix[key]), 25, BLUEBERRY_DARK,
                      rect.x + 243, rect.y + 77, center=True)
            self.text("+", 25, WHITE, plus.centerx, plus.centery - 1, center=True)

        message_box = pygame.Rect(280, 515, 730, 27)
        message_color = (154, 67, 67) if self.blender_message_error else GREEN_DARK
        self.text(self.blender_message, 14, message_color,
                  message_box.centerx, message_box.centery, center=True)

        finish = pygame.Rect(440, 550, 300, 56)
        reset = pygame.Rect(760, 550, 120, 56)
        close = pygame.Rect(900, 550, 110, 56)
        rounded_rect(self.screen, finish, BLUEBERRY, 10, WOOD_DARK, 4)
        rounded_rect(self.screen, reset, (210, 168, 92), 10, WOOD_DARK, 3)
        rounded_rect(self.screen, close, (177, 151, 136), 10, WOOD_DARK, 3)
        self.text("스무디 완성  Enter", 18, WHITE,
                  finish.centerx, finish.centery, center=True)
        self.text("전부 비우기", 15, INK, reset.centerx, reset.centery, center=True)
        self.text("나가기", 15, INK, close.centerx, close.centery, center=True)

    def draw_blending_overlay(self) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((31, 26, 39, 190))
        self.screen.blit(shade, (0, 0))
        card = pygame.Rect(300, 48, 680, 624)
        pygame.draw.rect(self.screen, (27, 25, 31), card.move(12, 12))
        pygame.draw.rect(self.screen, WOOD_DARK, card.inflate(14, 14))
        pygame.draw.rect(self.screen, (127, 87, 151), card)
        pygame.draw.rect(self.screen, CREAM, card.inflate(-18, -18))

        elapsed = BLENDER_DURATION - self.blender_animation_remaining
        progress = min(1.0, max(0.0, elapsed / BLENDER_DURATION))
        shake = round(math.sin(elapsed * 38.0) * 4)
        center_x = card.centerx + shake
        self.text("위이이잉! 스무디를 갈고 있어요", 32, BLUEBERRY_DARK,
                  card.centerx, 91, center=True)
        self.text("재료가 부드러워질 때까지 3초만 기다려 주세요.", 16, MUTED,
                  card.centerx, 128, center=True)

        jar = [
            (center_x - 118, 188),
            (center_x + 118, 188),
            (center_x + 92, 470),
            (center_x - 92, 470),
        ]
        pygame.draw.polygon(self.screen, (103, 81, 111), jar)
        inner = [
            (center_x - 108, 201),
            (center_x + 108, 201),
            (center_x + 82, 458),
            (center_x - 82, 458),
        ]
        pygame.draw.polygon(self.screen, (224, 213, 229), inner)
        liquid_top = 267 - round(progress * 26)
        liquid = [
            (center_x - 101, liquid_top),
            (center_x - 45, liquid_top - round(math.sin(elapsed * 16) * 8)),
            (center_x + 18, liquid_top + round(math.sin(elapsed * 16) * 7)),
            (center_x + 101, liquid_top - round(math.sin(elapsed * 16) * 5)),
            (center_x + 82, 458),
            (center_x - 82, 458),
        ]
        pygame.draw.polygon(self.screen, (171, 82, 177), liquid)
        pygame.draw.polygon(self.screen, (201, 123, 195), liquid, 5)

        ingredient_colors = {
            "blueberries": BLUEBERRY,
            "honey": GOLD,
            "milk": WHITE,
            "ice": WATER_LIGHT,
        }
        bubbles: list[tuple[str, int]] = []
        for key, count in self.blender_mix.items():
            bubbles.extend((key, index) for index in range(count))
        for index, (key, _count) in enumerate(bubbles):
            angle = elapsed * (4.2 + index % 3) + index * 1.7
            radius_x = 28 + (index * 17) % 63
            radius_y = 42 + (index * 11) % 78
            bubble_x = center_x + round(math.cos(angle) * radius_x)
            bubble_y = 350 + round(math.sin(angle * 1.15) * radius_y)
            icon = self.ingredient_icons_small.get(key)
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=(bubble_x, bubble_y)))
            else:
                radius = 7 if key == "blueberries" else 9
                pygame.draw.circle(self.screen, WOOD_DARK, (bubble_x, bubble_y), radius + 2)
                pygame.draw.circle(
                    self.screen, ingredient_colors[key], (bubble_x, bubble_y), radius
                )

        blade_center = (center_x, 426)
        blade_angle = elapsed * 18.0
        for offset in (0.0, math.pi / 2):
            dx = round(math.cos(blade_angle + offset) * 47)
            dy = round(math.sin(blade_angle + offset) * 19)
            pygame.draw.line(
                self.screen,
                (84, 74, 91),
                (blade_center[0] - dx, blade_center[1] - dy),
                (blade_center[0] + dx, blade_center[1] + dy),
                7,
            )
        pygame.draw.circle(self.screen, GOLD, blade_center, 10)

        pygame.draw.rect(self.screen, WOOD_DARK, (center_x - 132, 168, 264, 31))
        pygame.draw.rect(self.screen, (105, 75, 123), (center_x - 124, 172, 248, 20))
        pygame.draw.rect(self.screen, WOOD_DARK, (center_x - 106, 465, 212, 78))
        pygame.draw.rect(self.screen, (112, 79, 157), (center_x - 96, 471, 192, 60))
        pygame.draw.circle(self.screen, (242, 185, 87), (center_x, 501), 13)

        bar = pygame.Rect(390, 582, 500, 31)
        rounded_rect(self.screen, bar, (196, 176, 157), 10, WOOD_DARK, 3)
        fill_width = round((bar.width - 8) * progress)
        if fill_width > 0:
            pygame.draw.rect(
                self.screen,
                (127, 82, 168),
                (bar.x + 4, bar.y + 4, fill_width, bar.height - 8),
                border_radius=7,
            )
        seconds_left = max(0.0, self.blender_animation_remaining)
        self.text(f"완성까지 {seconds_left:.1f}초", 16, INK,
                  bar.centerx, 638, center=True)

    def draw_bag_overlay(self) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((31, 26, 39, 178))
        self.screen.blit(shade, (0, 0))

        card = pygame.Rect(312, 30, 656, 660)
        pygame.draw.rect(self.screen, (28, 25, 30), card.move(11, 11))
        pygame.draw.rect(self.screen, WOOD_DARK, card.inflate(14, 14))
        pygame.draw.rect(self.screen, WOOD, card)
        pygame.draw.rect(self.screen, CREAM, card.inflate(-18, -18))
        self.text("재료 가방", 32, BLUEBERRY_DARK, card.centerx, 70, center=True)
        self.text(
            f"4×4 총 {BAG_SLOT_COUNT}칸 · 한 칸에 같은 재료 최대 {BAG_STACK_SIZE}개",
            16,
            MUTED,
            card.centerx,
            108,
            center=True,
        )

        stacks = self.state.bag_stacks()
        used = len(stacks)
        meter = pygame.Rect(438, 129, 404, 18)
        rounded_rect(self.screen, meter, (215, 191, 146), 7, WOOD_DARK, 2)
        fill_width = round((meter.width - 6) * min(used, BAG_SLOT_COUNT) / BAG_SLOT_COUNT)
        if fill_width:
            pygame.draw.rect(
                self.screen,
                (114, 137, 76) if used < BAG_SLOT_COUNT else RED,
                (meter.x + 3, meter.y + 3, fill_width, meter.height - 6),
                border_radius=5,
            )
        self.text(f"{used}/{BAG_SLOT_COUNT}칸 사용", 13, INK,
                  meter.centerx, meter.centery, center=True)

        slot_w, slot_h, gap = 126, 94, 12
        start_x, start_y = 370, 165
        visible_stacks = stacks[:BAG_SLOT_COUNT]
        for index in range(BAG_SLOT_COUNT):
            column = index % BAG_COLUMNS
            row = index // BAG_COLUMNS
            rect = pygame.Rect(
                start_x + column * (slot_w + gap),
                start_y + row * (slot_h + gap),
                slot_w,
                slot_h,
            )
            pygame.draw.rect(self.screen, (92, 65, 52), rect.move(4, 5), border_radius=8)
            pygame.draw.rect(self.screen, (250, 236, 198), rect, border_radius=8)
            pygame.draw.rect(self.screen, (172, 137, 88), rect, 3, border_radius=8)
            self.text(f"{index + 1:02d}", 13, (176, 151, 115), rect.x + 8, rect.y + 6)

            if index >= len(visible_stacks):
                pygame.draw.rect(
                    self.screen,
                    (223, 205, 167),
                    pygame.Rect(rect.centerx - 11, rect.centery - 11, 22, 22),
                    3,
                    border_radius=6,
                )
                continue

            key, amount = visible_stacks[index]
            icon = self.ingredient_icons.get(key)
            icon_center = (rect.x + 38, rect.y + 50)
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=icon_center))
            elif key == "seeds":
                pygame.draw.ellipse(
                    self.screen, (97, 68, 34),
                    (icon_center[0] - 12, icon_center[1] - 7, 16, 23),
                )
                pygame.draw.ellipse(
                    self.screen, (222, 177, 62),
                    (icon_center[0] - 9, icon_center[1] - 5, 10, 17),
                )
                pygame.draw.line(
                    self.screen, GREEN_DARK,
                    (icon_center[0] + 1, icon_center[1] - 5),
                    (icon_center[0] + 10, icon_center[1] - 17), 4,
                )
                pygame.draw.ellipse(
                    self.screen, LEAF,
                    (icon_center[0] + 6, icon_center[1] - 20, 15, 10),
                )
            self.text(BAG_ITEM_LABELS[key], 15, INK, rect.x + 69, rect.y + 24)
            badge = pygame.Rect(rect.x + 68, rect.y + 49, 48, 29)
            rounded_rect(self.screen, badge, BLUEBERRY_DARK, 8)
            self.text(f"×{amount}", 16, WHITE, badge.centerx, badge.centery, center=True)

        if used > BAG_SLOT_COUNT:
            self.text(
                "이전 저장에 16칸을 넘는 재료가 있어요. 재료를 사용하면 정상 용량으로 돌아옵니다.",
                13,
                RED,
                card.centerx,
                594,
                center=True,
            )
        else:
            self.text("블루베리·씨앗·꿀·우유·얼음이 종류별로 자동 정리됩니다.",
                      13, MUTED, card.centerx, 594, center=True)

        close = pygame.Rect(510, 614, 260, 48)
        rounded_rect(self.screen, close, BLUEBERRY, 10, WOOD_DARK, 4)
        self.text("가방 닫기  B / E", 18, WHITE, close.centerx, close.centery, center=True)

    def draw_help_overlay(self) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((31, 26, 39, 175))
        self.screen.blit(shade, (0, 0))
        card = pygame.Rect(270, 58, 740, 632)
        pygame.draw.rect(self.screen, (32, 30, 31), card.move(10, 10))
        pygame.draw.rect(self.screen, WOOD_DARK, card.inflate(14, 14))
        pygame.draw.rect(self.screen, WOOD, card)
        pygame.draw.rect(self.screen, CREAM, card.inflate(-18, -18))
        self.text("직접 걸어 다니는 블루베리 농장", 32, BLUEBERRY_DARK, card.centerx, 103, center=True)
        self.text("화면 속 장소로 캐릭터를 이동한 뒤 E를 눌러 운영하세요.", 17, MUTED,
                  card.centerx, 145, center=True)
        rows = [
            ("이동·가방", "WASD · B 가방", "마을을 걸어 다니고 4×4 재료 가방을 확인해요."),
            ("밭", "나무 가까이에서 E", "빈 밭에는 씨앗을 심고 익은 나무는 직접 수확해요."),
            ("재료 상점", "동쪽 초록 지붕", "꿀·우유·얼음과 씨앗을 구매해요."),
            ("주문", "맨 앞 손님의 말풍선", "꿀·우유·얼음 수량과 받을 돈을 먼저 확인해요."),
            ("제조·판매", "블렌더 앞 E → +/-", "재료를 직접 주문 수량대로 담고 완성한 뒤 판매해요."),
        ]
        y = 183
        for title, control, body in rows:
            pygame.draw.circle(self.screen, BLUEBERRY, (326, y + 25), 20)
            self.text(title[0], 17, WHITE, 326, y + 25, center=True)
            self.text(title, 18, INK, 362, y + 3)
            self.text(control, 15, BLUEBERRY_DARK, 545, y + 5)
            self.wrapped_text(body, 14, MUTED, pygame.Rect(362, y + 31, 570, 35))
            y += 76
        note = pygame.Rect(334, 568, 612, 43)
        pygame.draw.rect(self.screen, BLUEBERRY_DARK, note.inflate(4, 4))
        pygame.draw.rect(self.screen, PURPLE_LIGHT, note)
        self.text("스무디 판매 성공 시에만 첨부 영상 소리가 한 잔당 1번 재생됩니다.",
                  15, BLUEBERRY_DARK, note.centerx, note.centery, center=True)
        start = pygame.Rect(510, 616, 260, 55)
        pygame.draw.rect(self.screen, WOOD_DARK, start.inflate(6, 6))
        pygame.draw.rect(self.screen, BLUEBERRY, start)
        self.text("마을로 나가기", 20, WHITE, start.centerx, start.centery, center=True)

    def draw(self) -> None:
        # Drawing transparent text and sprites to an intermediate surface before
        # resizing can turn their transparent pixels into solid rectangles on
        # some macOS/SDL combinations. Draw directly to the display surface.
        self.draw_world()
        self.draw_lighting()
        self.draw_impact_flash()
        self.draw_action_effects()
        self.draw_hud()
        self.draw_prompt()
        self.draw_toast()
        if self.overlay == "shop":
            self.draw_shop_overlay()
        elif self.overlay == "blender":
            self.draw_blender_overlay()
        elif self.overlay == "blending":
            self.draw_blending_overlay()
        elif self.overlay == "bag":
            self.draw_bag_overlay()
        elif self.overlay == "help":
            self.draw_help_overlay()
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = min(0.04, self.clock.tick(FPS) / 1000.0)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
            self.update(dt)
            self.draw()
        self.save()
        pygame.quit()


def main() -> int:
    try:
        GameApp().run()
        return 0
    except pygame.error as exc:
        print(f"Pygame을 시작하지 못했습니다: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
