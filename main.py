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
    DAYS_PER_SEASON,
    FACILITY_CONFIG,
    FACILITY_KEYS,
    FISHING_ROD_COST,
    FISHING_ROD_MAX_DURABILITY,
    FISH_PRICES,
    FURNITURE_COSTS,
    FURNITURE_GRID_COLUMNS,
    FURNITURE_GRID_ROWS,
    FURNITURE_LABELS,
    GAME_DAY_SECONDS,
    GOLDEN_BLUEBERRY_PRICE,
    ITEM_COSTS,
    MAX_FACILITY_LEVEL,
    MAX_PLOTS,
    ORGANIC_BLUEBERRY_PRICE,
    SPECIAL_SMOOTHIE_BONUS,
    STREETLIGHT_COST,
    STREETLIGHT_COUNT,
    WEATHER_LABELS,
    GameState,
    is_blueberry_festival,
    season_for_day,
)


SCREEN_W, SCREEN_H = 1280, 720
WORLD_W, WORLD_H = 2200, 1500
# Walkable grass around the original map gives edge scenery room to breathe.
# It also lets the camera scroll above the HUD instead of pinning treetops
# underneath it when the player visits the northern edge.
WORLD_EDGE_MARGIN = 160
WORLD_LEFT = -WORLD_EDGE_MARGIN
WORLD_TOP = -WORLD_EDGE_MARGIN
WORLD_RIGHT = WORLD_W + WORLD_EDGE_MARGIN
WORLD_BOTTOM = WORLD_H + WORLD_EDGE_MARGIN
FPS = 120
PLAYER_SPEED = 235.0
DAY_SECONDS = GAME_DAY_SECONDS
CUSTOMER_RETURN_SECONDS = 14.0
BLENDER_DURATION = 3.0
AUTOSAVE_SECONDS = 5.0
BASE_DIR = Path(__file__).resolve().parent
SAVE_PATH = BASE_DIR / "save_game.json"
SALE_SOUND_PATH = BASE_DIR / "assets" / "smoothie_sale.wav"
BLENDER_SOUND_PATH = BASE_DIR / "assets" / "blender_grind.wav"
BGM_PATH = BASE_DIR / "assets" / "blueberry_morning.ogg"
PLAYER_SHEET_PATH = BASE_DIR / "assets" / "player_reference_sheet.png"
INGREDIENT_SOURCE_PATHS = {
    "milk": BASE_DIR / "assets" / "ingredient_milk_source.png",
    "blueberries": BASE_DIR / "assets" / "ingredient_blueberry_source.png",
    "ice": BASE_DIR / "assets" / "ingredient_ice_source.png",
    "honey": BASE_DIR / "assets" / "ingredient_honey_source.png",
}
FISH_ASSET_PATHS = {
    key: BASE_DIR / "assets" / "fish" / f"{key}.png"
    for key in FISH_PRICES
}
FURNITURE_ASSET_PATHS = {
    key: BASE_DIR / "assets" / "furniture" / f"{key}.png"
    for key in FURNITURE_COSTS
}
BGM_NORMAL_VOLUME = 0.28
BGM_DUCK_VOLUME = 0.055
BGM_VOLUME_CHANGE_SPEED = 2.8
FISHING_MIN_WAIT = 3.0
FISHING_MAX_WAIT = 7.0
FISHING_BITE_SECONDS = 1.5
GAME_START_MINUTES = 6 * 60
GAME_CLOCK_MINUTES = 24 * 60
RAIN_DROP_COUNT = 72

# A fixed, independently scattered layout avoids the diagonal bands created
# when both x and y are simple multiples of the same drop index.
_rain_layout_rng = random.Random(20260906)
RAIN_DROP_LAYOUT = tuple(
    (
        _rain_layout_rng.randrange(-40, SCREEN_W + 40),
        _rain_layout_rng.randrange(0, SCREEN_H + 50),
        _rain_layout_rng.randrange(5, 9),
        _rain_layout_rng.randrange(18, 29),
    )
    for _ in range(RAIN_DROP_COUNT)
)
del _rain_layout_rng

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
BEEHIVE = pygame.Rect(245, 1000, 135, 105)
ICE_MAKER = pygame.Rect(455, 1000, 155, 105)
COW_BARN = pygame.Rect(680, 945, 250, 160)
FACILITY_RECTS = {
    "beehive": BEEHIVE,
    "ice_maker": ICE_MAKER,
    "cow_barn": COW_BARN,
}

# These five sites match the player's standing positions in the supplied
# reference screenshots. No other streetlight sites are active.
STREETLIGHT_POSITIONS: tuple[tuple[int, int], ...] = (
    (1550, 630),
    (1525, 50),
    (1280, 185),
    (-10, 570),
    (-10, 970),
)
STREETLIGHT_SITE_LABELS: tuple[str, ...] = ("가로등",) * STREETLIGHT_COUNT

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
    (-70, 250), (-80, 760), (-60, 1260),
    (650, 60), (970, 50), (1290, 60),
    (1450, 560), (2160, 190), (2180, 650),
    (2150, 1040), (2160, 1450), (1420, 1420),
    (1080, 1390), (700, 1420), (320, 1380),
]

FISH_KEYS = tuple(FISH_PRICES)
FURNITURE_KEYS = tuple(FURNITURE_COSTS)
SHOP_CLOSE_RECT = pygame.Rect(765, 578, 190, 48)
SHOP_FISH_BUTTON = pygame.Rect(325, 578, 260, 48)
HUD_HELP_RECT = pygame.Rect(1193, 15, 66, 25)
HOME_BUILD_AREA = pygame.Rect(80, 155, 1120, 320)
HOME_GRID_CELL = HOME_BUILD_AREA.width // FURNITURE_GRID_COLUMNS
HOME_EDIT_BUTTON = pygame.Rect(865, 96, 160, 42)
HOME_EXIT_BUTTON = pygame.Rect(1040, 96, 160, 42)
HOME_ROTATE_BUTTON = pygame.Rect(845, 490, 110, 42)
HOME_STORE_BUTTON = pygame.Rect(965, 490, 110, 42)
HOME_DONE_BUTTON = pygame.Rect(1085, 490, 110, 42)


def furniture_card_rect(index: int) -> pygame.Rect:
    return pygame.Rect(115 + index * 210, 548, 190, 112)


def fish_sale_card_rect(index: int) -> pygame.Rect:
    return pygame.Rect(195 + index * 225, 260, 205, 235)


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


def day_period_for_phase(phase: float) -> str:
    """Map a farm day from 06:00 through the following dawn."""
    normalized = max(0.0, min(0.999999, float(phase)))
    if normalized < 2 / 24:
        return "아침"
    if normalized < 12 / 24:
        return "낮"
    if normalized < 14 / 24:
        return "저녁"
    if normalized < 22 / 24:
        return "밤"
    return "새벽"


def clock_minutes_for_phase(phase: float) -> int:
    normalized = max(0.0, min(0.999999, float(phase)))
    return (GAME_START_MINUTES + int(normalized * GAME_CLOCK_MINUTES)) % GAME_CLOCK_MINUTES


def lighting_color_for_phase(phase: float) -> tuple[int, int, int, int]:
    """Smoothly interpolate dawn, daylight, sunset, midnight, and dawn again."""
    normalized = max(0.0, min(0.999999, float(phase)))
    keyframes = (
        (0.0, (102, 78, 116, 45)),       # 06:00 sunrise
        (2 / 24, (116, 91, 125, 0)),     # 08:00 clear daylight
        (11 / 24, (245, 166, 100, 0)),   # 17:00 sunset begins
        (12 / 24, (143, 76, 101, 30)),   # 18:00 sunset
        (14 / 24, (52, 48, 91, 86)),     # 20:00 night
        (18 / 24, (22, 30, 70, 134)),    # 00:00 deepest night
        (22 / 24, (51, 52, 92, 92)),     # 04:00 dawn begins
        (1.0, (102, 78, 116, 45)),       # 06:00 sunrise again
    )
    for (start, start_color), (end, end_color) in zip(keyframes, keyframes[1:]):
        if normalized <= end:
            span = max(0.000001, end - start)
            amount = (normalized - start) / span
            return tuple(
                round(left + (right - left) * amount)
                for left, right in zip(start_color, end_color)
            )
    return keyframes[-1][1]


def celestial_position_for_phase(phase: float) -> tuple[str, int, int, float]:
    """Move the sun and moon east-to-west along matching half-day arcs."""
    normalized = max(0.0, min(0.999999, float(phase)))
    if normalized < 0.5:
        body = "sun"
        progress = normalized / 0.5
    else:
        body = "moon"
        progress = (normalized - 0.5) / 0.5
    x = round(-55 + progress * (SCREEN_W + 110))
    y = round(260 - math.sin(progress * math.pi) * 130)
    return body, x, y, progress


def roof_detail_segment(
    rect: pygame.Rect,
    row: int,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return a horizontal detail line clipped inside the triangular roof."""
    apex_y = rect.top - 82
    base_y = rect.top + 43
    y = rect.top + 32 - max(0, int(row)) * 25
    slope_progress = max(0.0, min(1.0, (y - apex_y) / (base_y - apex_y)))
    half_width = (rect.width / 2 + 28) * slope_progress
    edge_padding = 12
    left = round(rect.centerx - half_width + edge_padding)
    right = round(rect.centerx + half_width - edge_padding)
    return (left, y), (right, y)


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


@dataclass
class TreeDrop:
    x: float
    y: float
    key: str
    amount: int
    life: float = 1.35
    duration: float = 1.35

    def update(self, dt: float) -> None:
        self.life -= dt
        self.y += 24 * dt


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
        if not self.state.tutorial_seen:
            self.overlay: str | None = "help"
        elif self.state.pending_daily_report is not None:
            self.overlay = "daily_report"
        else:
            self.overlay = None
        self.toast = "이제 캐릭터를 직접 움직여 농장을 운영하세요!"
        if load_errors:
            self.toast = "저장 파일을 읽지 못해 새 농장으로 시작했어요."
        self.toast_error = bool(load_errors)
        self.toast_until = time.time() + 4.5
        self.last_autosave = time.time()
        self.sale_sound: pygame.mixer.Sound | None = None
        self.sale_channel: pygame.mixer.Channel | None = None
        self.blender_sound: pygame.mixer.Sound | None = None
        self.blender_channel: pygame.mixer.Channel | None = None
        self.pending_sale_sounds = 0
        self.audio_error = ""
        self.music_error = ""
        self.current_bgm_volume = BGM_NORMAL_VOLUME
        self.bgm_duck_until = 0.0
        self.bgm_muted = False
        self.particles: list[Particle] = []
        self.action_effects: list[ActionEffect] = []
        self.departing_customers: list[DepartingCustomer] = []
        self.tree_drops: list[TreeDrop] = []
        self.tree_shake_timers: dict[int, float] = {}
        self.next_customer_at = time.time() + CUSTOMER_RETURN_SECONDS
        self.action_timer = 0.0
        self.impact_timer = 0.0
        self.shake_offset = pygame.Vector2()
        self.rng = random.Random(17)
        self.flowers = self._make_flowers()
        self.shop_buttons = self._make_shop_buttons()
        self.blender_mix = {key: 0 for key, _label, _color in BLENDER_INGREDIENTS}
        self.blender_specials = {"premium_honey": False, "low_fat_milk": False}
        self.blender_message = "재료의 + 버튼을 눌러 맨 앞 손님의 주문과 똑같이 맞추세요."
        self.blender_message_error = False
        self.blender_animation_remaining = 0.0
        self.blender_complete_message = ""
        self.blender_cards = self._make_blender_cards()
        self.fishing_phase = "idle"
        self.fishing_bite_at = 0.0
        self.fishing_escape_at = 0.0
        self.fishing_bobber = (POND.centerx, POND.centery)
        self.selected_facility = "beehive"
        self.ingredient_icons: dict[str, pygame.Surface] = {}
        self.ingredient_icons_small: dict[str, pygame.Surface] = {}
        self.ingredient_icon_error = ""
        self.fish_icons: dict[str, pygame.Surface] = {}
        self.fish_icons_small: dict[str, pygame.Surface] = {}
        self.furniture_sprites: dict[str, pygame.Surface] = {}
        self.decor_asset_error = ""
        self.home_edit_mode = False
        self.selected_furniture: str | None = None
        self.home_rotation = 0
        self._load_ingredient_icons()
        self._load_decor_assets()
        self._load_audio()
        self.player_frames: dict[str, list[pygame.Surface]] = {}
        self.player_sprite_error = ""
        self._load_player_frames()
        # Reuse full-screen alpha surfaces instead of allocating them every
        # frame. This noticeably lowers pressure on macOS' scaled display.
        self._lighting_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self._rain_veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self._rain_veil.fill((62, 90, 126, 22))
        self._heat_veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self._heat_veil.fill((255, 167, 68, 18))
        self._lamp_glow = pygame.Surface((150, 150), pygame.SRCALPHA)
        pygame.draw.circle(self._lamp_glow, (255, 195, 80, 12), (75, 75), 70)
        pygame.draw.circle(self._lamp_glow, (255, 218, 118, 24), (75, 75), 39)
        pygame.draw.circle(self._lamp_glow, (255, 240, 177, 62), (75, 75), 12)

    def _make_flowers(self) -> list[tuple[int, int, tuple[int, int, int]]]:
        flowers = []
        colors = [(255, 238, 130), (247, 177, 197), (217, 229, 255), (255, 255, 240)]
        rng = random.Random(43)
        for _ in range(175):
            x = rng.randint(WORLD_LEFT + 35, WORLD_RIGHT - 35)
            y = rng.randint(WORLD_TOP + 35, WORLD_BOTTOM - 35)
            point = (x, y)
            blocked = any(
                rect.inflate(60, 60).collidepoint(point)
                for rect in (
                    HOUSE, SHOP, CAFE, MARKET, SMOOTHIE_CART, POND,
                    BEEHIVE, ICE_MAKER, COW_BARN,
                )
            )
            if not blocked and not pygame.Rect(215, 340, 730, 560).collidepoint(point):
                flowers.append((x, y, rng.choice(colors)))
        return flowers

    @staticmethod
    def _make_shop_buttons() -> list[tuple[pygame.Rect, str, str, tuple[int, int, int]]]:
        return [
            (pygame.Rect(325, 218, 290, 82), "seeds", "씨앗", GREEN),
            (pygame.Rect(665, 218, 290, 82), "honey", "꿀", GOLD),
            (pygame.Rect(325, 318, 290, 82), "milk", "우유", (84, 149, 183)),
            (pygame.Rect(665, 318, 290, 82), "ice", "얼음", (79, 169, 194)),
            (pygame.Rect(325, 418, 290, 82), "fertilizer", "비료", (135, 105, 61)),
            (pygame.Rect(665, 418, 290, 82), "fishing_rod", "낚싯대", WATER),
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
            self.blender_sound = pygame.mixer.Sound(str(BLENDER_SOUND_PATH))
            self.blender_sound.set_volume(0.58)
            self.blender_channel = pygame.mixer.Channel(1)
        except (pygame.error, FileNotFoundError) as exc:
            self.audio_error = f"{self.audio_error}; {exc}".strip("; ")
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

    def _load_decor_assets(self) -> None:
        """Load the original PNG catalogue used by fishing and home decorating."""
        errors: list[str] = []
        for key, path in FISH_ASSET_PATHS.items():
            try:
                sprite = pygame.image.load(str(path)).convert_alpha()
                self.fish_icons[key] = self._scale_icon_to_cell(sprite, 68)
                self.fish_icons_small[key] = self._scale_icon_to_cell(sprite, 38)
            except (pygame.error, FileNotFoundError, ValueError) as exc:
                errors.append(f"{path.name}: {exc}")
        for key, path in FURNITURE_ASSET_PATHS.items():
            try:
                sprite = pygame.image.load(str(path)).convert_alpha()
                bounds = sprite.get_bounding_rect(min_alpha=1)
                self.furniture_sprites[key] = sprite.subsurface(bounds).copy()
            except (pygame.error, FileNotFoundError, ValueError) as exc:
                errors.append(f"{path.name}: {exc}")
        self.decor_asset_error = "; ".join(errors)

    def draw_item_icon(
        self,
        key: str,
        center: tuple[int, int],
        *,
        small: bool = False,
    ) -> bool:
        if key in FISH_KEYS:
            icons = self.fish_icons_small if small else self.fish_icons
            icon = icons.get(key)
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=center))
                return True
        if key == "coins":
            radius = 13 if small else 20
            pygame.draw.circle(self.screen, WOOD_DARK, center, radius + 3)
            pygame.draw.circle(self.screen, GOLD, center, radius)
            pygame.draw.circle(self.screen, (255, 220, 91), center, max(4, radius - 7))
            return True
        if key == "seeds":
            scale = 0.72 if small else 1.0
            seed_w = max(9, round(16 * scale))
            seed_h = max(14, round(23 * scale))
            pygame.draw.ellipse(
                self.screen,
                WOOD_DARK,
                (
                    center[0] - seed_w // 2 - 2,
                    center[1] - seed_h // 2 - 2,
                    seed_w + 4,
                    seed_h + 4,
                ),
            )
            pygame.draw.ellipse(
                self.screen,
                GOLD,
                (
                    center[0] - seed_w // 2,
                    center[1] - seed_h // 2,
                    seed_w,
                    seed_h,
                ),
            )
            stem_end = (
                center[0] + round(11 * scale),
                center[1] - round(17 * scale),
            )
            pygame.draw.line(
                self.screen,
                GREEN_DARK,
                (center[0] + round(2 * scale), center[1] - round(7 * scale)),
                stem_end,
                max(2, round(4 * scale)),
            )
            pygame.draw.ellipse(
                self.screen,
                LEAF,
                (
                    stem_end[0] - 2,
                    stem_end[1] - 5,
                    max(8, round(14 * scale)),
                    max(6, round(9 * scale)),
                ),
            )
            return True
        if key == "fertilizer":
            scale = 0.7 if small else 1.0
            width, height = round(32 * scale), round(38 * scale)
            rect = pygame.Rect(0, 0, width, height)
            rect.center = center
            pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(5, 5), border_radius=5)
            pygame.draw.rect(self.screen, (191, 151, 82), rect, border_radius=4)
            pygame.draw.rect(self.screen, CREAM, (rect.x + 5, rect.y + 9, width - 10, 12))
            pygame.draw.circle(self.screen, LEAF, rect.center, max(3, round(6 * scale)))
            return True
        if key == "fishing_rod":
            scale = 0.72 if small else 1.0
            x, y = center
            pygame.draw.line(
                self.screen, WOOD_DARK,
                (x - round(16 * scale), y + round(18 * scale)),
                (x + round(14 * scale), y - round(18 * scale)),
                max(3, round(5 * scale)),
            )
            pygame.draw.line(
                self.screen, WATER_LIGHT,
                (x + round(14 * scale), y - round(18 * scale)),
                (x + round(19 * scale), y + round(10 * scale)),
                max(1, round(2 * scale)),
            )
            pygame.draw.arc(
                self.screen, INK,
                pygame.Rect(x + round(13 * scale), y + round(6 * scale),
                            round(12 * scale), round(14 * scale)),
                0.2, 3.4, max(1, round(2 * scale)),
            )
            return True
        if key in FISH_KEYS:
            x, y = center
            scale = 0.72 if small else 1.0
            if key == "turtle":
                shell = (72, 137, 79)
                pygame.draw.ellipse(
                    self.screen, WOOD_DARK,
                    (x - round(18 * scale), y - round(13 * scale),
                     round(36 * scale), round(27 * scale)),
                )
                pygame.draw.ellipse(
                    self.screen, shell,
                    (x - round(15 * scale), y - round(10 * scale),
                     round(30 * scale), round(21 * scale)),
                )
                pygame.draw.circle(self.screen, LEAF,
                                   (x + round(20 * scale), y - round(2 * scale)),
                                   max(3, round(6 * scale)))
                return True
            colors = {
                "carp": (216, 135, 68),
                "crucian_carp": (188, 170, 104),
                "bass": (79, 132, 95),
            }
            body = colors[key]
            pygame.draw.polygon(
                self.screen, WOOD_DARK,
                [(x - round(17 * scale), y),
                 (x - round(28 * scale), y - round(11 * scale)),
                 (x - round(28 * scale), y + round(11 * scale))],
            )
            pygame.draw.ellipse(
                self.screen, WOOD_DARK,
                (x - round(18 * scale), y - round(13 * scale),
                 round(40 * scale), round(27 * scale)),
            )
            pygame.draw.ellipse(
                self.screen, body,
                (x - round(15 * scale), y - round(10 * scale),
                 round(34 * scale), round(21 * scale)),
            )
            pygame.draw.circle(self.screen, WHITE,
                               (x + round(10 * scale), y - round(3 * scale)),
                               max(2, round(3 * scale)))
            pygame.draw.circle(self.screen, INK,
                               (x + round(11 * scale), y - round(3 * scale)),
                               max(1, round(2 * scale)))
            return True
        base_key = {
            "golden_blueberries": "blueberries",
            "organic_blueberries": "blueberries",
            "premium_honey": "honey",
            "low_fat_milk": "milk",
        }.get(key, key)
        icons = self.ingredient_icons_small if small else self.ingredient_icons
        icon = icons.get(base_key)
        if icon is None:
            return False
        self.screen.blit(icon, icon.get_rect(center=center))
        badge_radius = 7 if small else 10
        badge_center = (
            center[0] + (10 if small else 18),
            center[1] - (10 if small else 18),
        )
        if key in ("golden_blueberries", "premium_honey"):
            pygame.draw.circle(self.screen, WOOD_DARK, badge_center, badge_radius + 2)
            pygame.draw.circle(self.screen, GOLD, badge_center, badge_radius)
            pygame.draw.line(
                self.screen, WHITE,
                (badge_center[0] - badge_radius // 2, badge_center[1]),
                (badge_center[0] + badge_radius // 2, badge_center[1]), 2,
            )
            pygame.draw.line(
                self.screen, WHITE,
                (badge_center[0], badge_center[1] - badge_radius // 2),
                (badge_center[0], badge_center[1] + badge_radius // 2), 2,
            )
        elif key in ("low_fat_milk", "organic_blueberries"):
            pygame.draw.circle(self.screen, WOOD_DARK, badge_center, badge_radius + 2)
            badge_color = WATER if key == "low_fat_milk" else LEAF
            pygame.draw.circle(self.screen, badge_color, badge_center, badge_radius)
            if key == "low_fat_milk" and not small:
                self.text("L", 13, WHITE, badge_center[0], badge_center[1], center=True)
            elif key == "organic_blueberries":
                pygame.draw.line(
                    self.screen, WHITE,
                    (badge_center[0] - 3, badge_center[1] + 2),
                    (badge_center[0] + 3, badge_center[1] - 3), 2,
                )
        return True

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
        self.camera.update(self._camera_target())

    def _camera_target(self) -> pygame.Vector2:
        return pygame.Vector2(
            max(
                WORLD_LEFT,
                min(WORLD_RIGHT - SCREEN_W, self.player.x - SCREEN_W / 2),
            ),
            max(
                WORLD_TOP,
                min(WORLD_BOTTOM - SCREEN_H, self.player.y - SCREEN_H / 2),
            ),
        )

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
        obstacles = [
            HOUSE, SHOP, CAFE, MARKET, SMOOTHIE_CART, POND.inflate(-34, -30),
            BEEHIVE, ICE_MAKER, COW_BARN,
        ]
        obstacles.extend(pygame.Rect(x - 14, y - 8, 28, 32) for x, y in TREE_POSITIONS)
        return obstacles

    def _collides(self, x: float, y: float) -> bool:
        feet = self._feet_rect(x, y)
        if (
            feet.left < WORLD_LEFT + 8
            or feet.right > WORLD_RIGHT - 8
            or feet.top < WORLD_TOP + 8
            or feet.bottom > WORLD_BOTTOM - 8
        ):
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
            self.state.tick_customer_wait(dt)
            self.state.game_elapsed_seconds += max(0.0, dt)
            new_day = self.state.current_day
            if new_day > self.state.tracked_day:
                report = self.state.advance_to_day(new_day)
                if report is not None:
                    self.overlay = "daily_report"
                    self.save()
        target = self._camera_target()
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
        for drop in self.tree_drops:
            drop.update(dt)
        self.tree_drops = [drop for drop in self.tree_drops if drop.life > 0]
        self.tree_shake_timers = {
            index: timer - dt
            for index, timer in self.tree_shake_timers.items()
            if timer - dt > 0
        }
        now = time.time()
        if self.overlay is None and self.fishing_phase == "waiting" and now >= self.fishing_bite_at:
            self.fishing_phase = "bite"
            self.fishing_escape_at = now + FISHING_BITE_SECONDS
            self.notify("입질이 왔어요! 연못가에서 E를 눌러 낚아 올리세요!")
        elif self.overlay is None and self.fishing_phase == "bite" and now > self.fishing_escape_at:
            self.fishing_phase = "idle"
            self.notify("물고기가 미끼를 물고 달아났어요. 다시 던져 보세요.", True)
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
                (
                    self.sale_channel
                    and (self.sale_channel.get_busy() or self.pending_sale_sounds)
                )
                or (self.blender_channel and self.blender_channel.get_busy())
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
                if self.blender_channel:
                    self.blender_channel.fadeout(120)
                self.overlay = None
                self.notify(self.blender_complete_message)
                self.spawn_particles(
                    (CAFE.centerx, CAFE.bottom + 42), (192, 102, 186), 30
                )
        if time.time() - self.last_autosave > AUTOSAVE_SECONDS:
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
                    crop_name = "유기농 블루베리" if plot.fertilized else "블루베리"
                    prompt = f"{crop_name} 수확하기 (+{self.state.harvest_yield_for_day()})"
                else:
                    fertilizer_note = " · 유기농 수확 예정" if plot.fertilized else " · F 비료 사용"
                    prompt = f"자라는 중 · {int(plot.remaining(now)) + 1}초 남음{fertilizer_note}"
                candidates.append((gap, {"kind": "plot", "index": index, "prompt": prompt,
                                         "point": rect.center}))

        for index, point in enumerate(TREE_POSITIONS):
            gap = distance(position, point)
            if gap <= 78:
                prompt = (
                    "오늘 이미 흔든 나무"
                    if self.state.tree_shaken_today(index)
                    else "나무 흔들기 · 랜덤 아이템"
                )
                candidates.append((gap, {
                    "kind": "tree",
                    "index": index,
                    "prompt": prompt,
                    "point": point,
                }))

        for index, point in enumerate(STREETLIGHT_POSITIONS):
            gap = distance(position, point)
            if gap <= 78:
                installed = self.state.streetlights_installed[index]
                site_name = STREETLIGHT_SITE_LABELS[index]
                prompt = (
                    "가로등 · 저녁부터 새벽까지 자동 점등"
                    if installed
                    else f"가로등 설치 ({STREETLIGHT_COST:,}코인)"
                )
                candidates.append((gap, {
                    "kind": "streetlight",
                    "index": index,
                    "prompt": prompt,
                    "point": point,
                }))

        order = self.state.current_order
        craft_prompt = (
            f"주문 스무디 만들기 · {order.short_text()}"
            if order is not None
            else "새 주문을 기다리는 중"
        )
        sell_prompt = (
            f"주문 스무디 판매 (+{self.state.smoothie_sale_price(order)}코인 · 대기 {self.state.customers_waiting}명)"
            if order is not None
            else "새 손님을 기다리는 중"
        )
        fixed = [
            ("home", (HOUSE.centerx, HOUSE.bottom + 37), 82, "농장집 들어가기 · 저장과 가구 꾸미기"),
            ("shop", (SHOP.centerx, SHOP.bottom + 42), 90, "상점 들어가기"),
            ("craft", (CAFE.centerx, CAFE.bottom + 42), 90, craft_prompt),
            ("sell_raw", (MARKET.centerx, MARKET.bottom + 38), 88,
             f"생과 시장 열기 · 블루베리 {self.state.blueberries} · 황금 {self.state.golden_blueberries}"),
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
        pond_gap = distance_to_rect(position, POND)
        if pond_gap <= 88:
            pond_point = (
                max(POND.left, min(position[0], POND.right)),
                max(POND.top, min(position[1], POND.bottom)),
            )
            if self.fishing_phase == "bite":
                fishing_prompt = "입질! 지금 E로 낚아 올리기"
            elif self.fishing_phase == "waiting":
                fishing_prompt = "찌를 지켜보는 중 · 입질을 기다리세요"
            elif not self.state.fishing_rod:
                fishing_prompt = "낚시하려면 상점에서 낚싯대 구입"
            else:
                fishing_prompt = (
                    "낚싯대 던지기 · "
                    f"내구도 {self.state.fishing_rod_durability}/"
                    f"{FISHING_ROD_MAX_DURABILITY}"
                )
            candidates.append((pond_gap, {
                "kind": "fishing",
                "prompt": fishing_prompt,
                "point": pond_point,
            }))
        for key, rect in FACILITY_RECTS.items():
            point = (rect.centerx, rect.bottom + 38)
            gap = distance(position, point)
            if gap > 88:
                continue
            config = FACILITY_CONFIG[key]
            level = self.state.facility_level(key)
            if level <= 0:
                if self.state.farm_rank < int(config["unlock_rank"]):
                    prompt = f"{config['name']} 잠김 · 농장 등급 {config['unlock_rank']} 필요"
                else:
                    prompt = f"{config['name']} 건설하기 ({self.state.facility_build_cost(key):,}코인)"
            elif self.state.facility_is_ready(key):
                prompt = f"{config['product_name']} {self.state.facility_yield(key)}개 준비됨 · 시설 관리"
            else:
                ready_day = self.state.facility_ready_days[key]
                prompt = f"{config['name']} {level}단계 · {ready_day}일차 생산 · 시설 관리"
            candidates.append((gap, {
                "kind": "facility",
                "key": key,
                "prompt": prompt,
                "point": point,
            }))
        return min(candidates, key=lambda item: item[0])[1] if candidates else None

    def interact(self) -> None:
        target = self.nearest_interaction()
        if target is None:
            self.notify("상호작용할 곳에 조금 더 가까이 가세요.", True)
            return
        kind = target["kind"]
        if kind == "plot":
            before_harvested = self.state.berries_harvested
            ok, message = self.state.use_plot(target["index"])
            if ok and self.state.berries_harvested > before_harvested:
                self.spawn_harvest_impact(
                    target["point"], self.state.berries_harvested - before_harvested
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
        elif kind == "tree":
            ok, message, drop_key, amount = self.state.shake_tree(
                target["index"], self.rng
            )
            if ok and drop_key is not None:
                self.tree_shake_timers[target["index"]] = 0.65
                self.tree_drops.append(
                    TreeDrop(
                        target["point"][0] + self.rng.randint(-32, 32),
                        target["point"][1] - 88,
                        drop_key,
                        amount,
                    )
                )
                self.spawn_particles(
                    (target["point"][0], target["point"][1] - 65),
                    GOLD if drop_key in ("coins", "golden_blueberries", "premium_honey") else LEAF,
                    18,
                )
        elif kind == "shop":
            self.overlay = "shop"
            return
        elif kind == "home":
            self.save()
            self.home_edit_mode = False
            self.selected_furniture = (
                self.state.furniture_owned[0]
                if self.state.furniture_owned
                else None
            )
            if self.selected_furniture is not None:
                layout = self.state.furniture_layout.get(self.selected_furniture)
                self.home_rotation = int(layout[2]) % 2 if layout else 0
            self.overlay = "home"
            return
        elif kind == "fishing":
            self.use_fishing(target["point"])
            return
        elif kind == "facility":
            self.selected_facility = target["key"]
            self.overlay = "facility"
            return
        elif kind == "streetlight":
            ok, message = self.state.buy_streetlight(target["index"])
            if ok:
                self.spawn_particles(
                    (target["point"][0], target["point"][1] - 82), GOLD, 24
                )
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
            self.blender_specials = {"premium_honey": False, "low_fat_milk": False}
            self.blender_message = "재료의 + 버튼을 눌러 주문 수량을 직접 맞추세요."
            self.blender_message_error = False
            self.overlay = "blender"
            return
        elif kind == "sell_raw":
            self.overlay = "market"
            return
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
        if key == "fishing_rod":
            ok, message = self.state.buy_fishing_rod()
        else:
            ok, message = self.state.buy_item(key)
        self.notify(message, not ok)
        if ok:
            self.save()

    def sell_market_item(self, key: str) -> None:
        if key == "golden_blueberries":
            ok, message = self.state.sell_golden_blueberry()
            color = GOLD
        elif key == "organic_blueberries":
            ok, message = self.state.sell_organic_blueberry()
            color = LEAF
        else:
            ok, message = self.state.sell_blueberry()
            color = BLUEBERRY
        self.notify(message, not ok)
        if ok:
            self.spawn_particles((MARKET.centerx, MARKET.bottom + 20), color, 18)
            self.save()

    def sell_fish(self, key: str) -> None:
        ok, message = self.state.sell_fish(key)
        self.notify(message, not ok)
        if ok:
            self.spawn_particles((SHOP.centerx, SHOP.bottom + 20), WATER_LIGHT, 18)
            self.save()

    def buy_furniture(self, key: str) -> None:
        ok, message = self.state.buy_furniture(key)
        self.notify(message, not ok)
        if ok:
            self.selected_furniture = key
            self.home_rotation = 0
            self.save()

    def select_furniture(self, key: str) -> bool:
        if key not in self.state.furniture_owned:
            self.notify("먼저 이 가구를 구입해 주세요.", True)
            return False
        self.selected_furniture = key
        layout = self.state.furniture_layout.get(key)
        self.home_rotation = int(layout[2]) % 2 if layout else 0
        return True

    def toggle_home_edit(self) -> None:
        if self.home_edit_mode:
            self.home_edit_mode = False
            self.notify("가구 배치를 저장했어요.")
            self.save()
            return
        if not self.state.furniture_owned:
            self.notify("배치할 가구를 먼저 구입해 주세요.", True)
            return
        self.home_edit_mode = True
        selected = self.selected_furniture
        if selected not in self.state.furniture_owned:
            selected = self.state.furniture_owned[0]
        self.select_furniture(selected)
        self.notify("가구를 고른 뒤 바닥을 클릭해 놓아 보세요.")

    @staticmethod
    def furniture_grid_rect(
        key: str,
        column: int,
        row: int,
        rotation: int,
    ) -> pygame.Rect:
        width, height = GameState.furniture_footprint(key, rotation)
        return pygame.Rect(
            HOME_BUILD_AREA.x + column * HOME_GRID_CELL,
            HOME_BUILD_AREA.y + row * HOME_GRID_CELL,
            width * HOME_GRID_CELL,
            height * HOME_GRID_CELL,
        )

    def place_selected_furniture(self, column: int, row: int) -> None:
        if self.selected_furniture is None:
            self.notify("먼저 아래 보관함에서 가구를 선택해 주세요.", True)
            return
        ok, message = self.state.place_furniture(
            self.selected_furniture,
            column,
            row,
            self.home_rotation,
        )
        self.notify(message, not ok)
        if ok:
            self.save()

    def move_selected_furniture(self, column_delta: int, row_delta: int) -> None:
        key = self.selected_furniture
        if key is None:
            self.notify("움직일 가구를 선택해 주세요.", True)
            return
        layout = self.state.furniture_layout.get(key)
        if layout is None:
            self.notify("보관 중인 가구는 바닥을 클릭해 먼저 놓아 주세요.", True)
            return
        ok, message = self.state.place_furniture(
            key,
            layout[0] + column_delta,
            layout[1] + row_delta,
            layout[2],
        )
        self.notify(message, not ok)
        if ok:
            self.save()

    def rotate_selected_furniture(self) -> None:
        key = self.selected_furniture
        if key is None:
            self.notify("회전할 가구를 선택해 주세요.", True)
            return
        next_rotation = (self.home_rotation + 1) % 2
        layout = self.state.furniture_layout.get(key)
        if layout is None:
            self.home_rotation = next_rotation
            self.notify("놓기 전 방향을 바꿨어요.")
            return
        ok, message = self.state.place_furniture(
            key,
            layout[0],
            layout[1],
            next_rotation,
        )
        self.notify(message, not ok)
        if ok:
            self.home_rotation = next_rotation
            self.save()

    def store_selected_furniture(self) -> None:
        key = self.selected_furniture
        if key is None:
            self.notify("보관할 가구를 선택해 주세요.", True)
            return
        ok, message = self.state.store_furniture(key)
        self.notify(message, not ok)
        if ok:
            self.save()

    def use_fertilizer_nearby(self) -> None:
        position = (self.player.x, self.player.y)
        choices = [
            (distance_to_rect(position, rect), index, rect.center)
            for index, rect in enumerate(PLOT_RECTS[:self.state.active_plots])
            if distance_to_rect(position, rect) <= 84
        ]
        if not choices:
            self.notify("비료를 사용할 블루베리 밭 가까이 가세요.", True)
            return
        _gap, index, point = min(choices)
        ok, message = self.state.fertilize(index)
        self.notify(message, not ok)
        if ok:
            self.spawn_particles(point, LEAF, 20)
            self.action_effects.append(
                ActionEffect(point[0], point[1] - 76, "유기농 수확 예정!", GREEN_DARK)
            )
            self.save()

    def use_fishing(self, pond_edge: tuple[float, float]) -> None:
        if self.fishing_phase == "idle" and not self.state.fishing_rod:
            self.notify("낚싯대가 없어요. 상점에서 2,000코인에 구입하세요.", True)
            return
        now = time.time()
        if self.fishing_phase == "idle":
            ok, durability_message, broke = self.state.use_fishing_rod()
            if not ok:
                self.notify(durability_message, True)
                return
            edge_x, edge_y = pond_edge
            if edge_x <= POND.left:
                self.fishing_bobber = (POND.left + 55, max(POND.top + 35, min(edge_y, POND.bottom - 35)))
            elif edge_x >= POND.right:
                self.fishing_bobber = (POND.right - 55, max(POND.top + 35, min(edge_y, POND.bottom - 35)))
            elif edge_y <= POND.top:
                self.fishing_bobber = (max(POND.left + 45, min(edge_x, POND.right - 45)), POND.top + 55)
            else:
                self.fishing_bobber = (max(POND.left + 45, min(edge_x, POND.right - 45)), POND.bottom - 55)
            wait = self.rng.uniform(FISHING_MIN_WAIT, FISHING_MAX_WAIT)
            if self.state.weather == "rain":
                wait *= 0.7
            self.fishing_phase = "waiting"
            self.fishing_bite_at = now + wait
            if broke:
                self.notify("마지막 찌를 던졌고 낚싯대가 부서졌어요. 이번 입질은 잡을 수 있어요!", True)
            else:
                self.notify(
                    "찌를 던졌어요. 물속으로 잠길 때 E를 누르세요. · "
                    + durability_message
                )
            self.save()
            return
        if self.fishing_phase == "waiting":
            self.fishing_phase = "idle"
            self.notify("너무 일찍 감았어요. 물고기가 다가올 때까지 기다리세요.", True)
            return

        ok, message, fish_key = self.state.catch_fish(
            self.rng,
            active_cast=True,
        )
        self.fishing_phase = "idle"
        self.notify(message, not ok)
        if ok and fish_key is not None:
            self.tree_drops.append(
                TreeDrop(self.fishing_bobber[0], self.fishing_bobber[1] - 12, fish_key, 1)
            )
            self.spawn_particles(self.fishing_bobber, WATER_LIGHT, 24)
            self.save()

    def use_facility_main_action(self) -> None:
        key = self.selected_facility
        if self.state.facility_level(key) <= 0:
            ok, message = self.state.build_facility(key)
        else:
            ok, message = self.state.collect_facility(key)
        self.notify(message, not ok)
        if ok:
            product = str(FACILITY_CONFIG[key]["product"])
            color = {
                "honey": GOLD,
                "ice": WATER_LIGHT,
                "milk": WHITE,
            }[product]
            rect = FACILITY_RECTS[key]
            self.spawn_particles((rect.centerx, rect.bottom + 10), color, 22)
            self.save()

    def upgrade_selected_facility(self) -> None:
        key = self.selected_facility
        ok, message = self.state.upgrade_facility(key)
        self.notify(message, not ok)
        if ok:
            rect = FACILITY_RECTS[key]
            self.spawn_particles((rect.centerx, rect.centery), GOLD, 28)
            self.save()

    def close_daily_report(self) -> None:
        self.state.clear_daily_report()
        self.overlay = None
        self.save()

    def change_blender_ingredient(self, key: str, amount: int) -> None:
        if key not in self.blender_mix:
            return
        self.blender_mix[key] = max(0, min(9, self.blender_mix[key] + amount))
        self.blender_message = "주문표와 넣은 수량을 비교한 뒤 완성 버튼을 누르세요."
        self.blender_message_error = False

    def toggle_blender_special(self, key: str) -> None:
        if key not in self.blender_specials:
            return
        turning_on = not self.blender_specials[key]
        if turning_on and self.state.inventory(key) < 1:
            label = BAG_ITEM_LABELS[key]
            self.blender_message = f"{label}이 없어요. 나무를 흔들어 찾아보세요."
            self.blender_message_error = True
            return
        self.blender_specials[key] = turning_on
        label = BAG_ITEM_LABELS[key]
        action = "추가했어요" if turning_on else "뺐어요"
        self.blender_message = f"{label}을(를) {action}. 판매 보너스를 확인하세요."
        self.blender_message_error = False

    def blender_special_button(self, special_key: str) -> pygame.Rect:
        ingredient_key = "honey" if special_key == "premium_honey" else "milk"
        card = next(rect for rect, key, _label, _color in self.blender_cards if key == ingredient_key)
        return pygame.Rect(card.right - 128, card.y + 10, 116, 34)

    def finish_blender_mix(self) -> None:
        ok, message = self.state.make_smoothie(self.blender_mix, self.blender_specials)
        if not ok:
            self.blender_message = message
            self.blender_message_error = True
            return
        self.blender_animation_remaining = BLENDER_DURATION
        self.blender_complete_message = message
        self.overlay = "blending"
        if self.blender_sound and self.blender_channel:
            self.blender_channel.play(self.blender_sound)
            self.duck_background_music(BLENDER_DURATION + 0.2)
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
            if self.overlay == "home" and self.home_edit_mode:
                self.home_edit_mode = False
                self.save()
                self.notify("가구 배치를 저장했어요.")
                return
            if self.overlay:
                if self.overlay == "help":
                    self.close_help()
                elif self.overlay == "daily_report":
                    self.close_daily_report()
                else:
                    self.overlay = None
            else:
                self.running = False
            return
        if (
            event.key == pygame.K_h
            or getattr(event, "scancode", None) == pygame.KSCAN_H
        ):
            if self.overlay == "blending":
                return
            if self.overlay == "help":
                self.close_help()
            else:
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
        if self.overlay == "daily_report":
            if self.is_interaction_key(event):
                self.close_daily_report()
            return
        if self.overlay == "facility":
            if self.is_interaction_key(event):
                self.use_facility_main_action()
            elif (
                event.key == pygame.K_u
                or getattr(event, "scancode", None) == pygame.KSCAN_U
            ):
                self.upgrade_selected_facility()
            return
        if self.overlay == "market":
            if event.key == pygame.K_1:
                self.sell_market_item("blueberries")
            elif event.key == pygame.K_2:
                self.sell_market_item("golden_blueberries")
            elif event.key == pygame.K_3:
                self.sell_market_item("organic_blueberries")
            elif self.is_interaction_key(event):
                self.overlay = None
            return
        if self.overlay == "fish_market":
            shortcuts = {
                pygame.K_1: "carp",
                pygame.K_2: "crucian_carp",
                pygame.K_3: "bass",
                pygame.K_4: "turtle",
            }
            if event.key in shortcuts:
                self.sell_fish(shortcuts[event.key])
            elif self.is_interaction_key(event):
                self.overlay = "shop"
            return
        if self.overlay == "home":
            shortcuts = {
                pygame.K_1: "bed",
                pygame.K_2: "drawer",
                pygame.K_3: "desk",
                pygame.K_4: "lantern",
                pygame.K_5: "flowerpot",
            }
            if (
                event.key == pygame.K_g
                or getattr(event, "scancode", None) == pygame.KSCAN_G
            ):
                self.toggle_home_edit()
            elif self.home_edit_mode:
                if event.key in shortcuts:
                    self.select_furniture(shortcuts[event.key])
                elif event.key == pygame.K_r:
                    self.rotate_selected_furniture()
                elif event.key == pygame.K_x:
                    self.store_selected_furniture()
                elif event.key == pygame.K_LEFT:
                    self.move_selected_furniture(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.move_selected_furniture(1, 0)
                elif event.key == pygame.K_UP:
                    self.move_selected_furniture(0, -1)
                elif event.key == pygame.K_DOWN:
                    self.move_selected_furniture(0, 1)
                elif self.is_interaction_key(event):
                    self.toggle_home_edit()
            elif event.key in shortcuts:
                key = shortcuts[event.key]
                if key in self.state.furniture_owned:
                    self.select_furniture(key)
                    self.notify("G를 누르면 선택한 가구를 옮길 수 있어요.")
                else:
                    self.buy_furniture(key)
            elif self.is_interaction_key(event):
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
            elif event.key == pygame.K_5:
                self.toggle_blender_special("premium_honey")
            elif event.key == pygame.K_6:
                self.toggle_blender_special("low_fat_milk")
            elif event.key == pygame.K_r:
                self.blender_mix = {
                    key: 0 for key, _label, _color in BLENDER_INGREDIENTS
                }
                self.blender_specials = {"premium_honey": False, "low_fat_milk": False}
                self.blender_message = "재료를 모두 비웠어요. 다시 직접 넣어 보세요."
                self.blender_message_error = False
            elif event.key == pygame.K_RETURN:
                self.finish_blender_mix()
            return
        if self.overlay == "shop":
            shortcuts = {
                pygame.K_1: "seeds",
                pygame.K_2: "honey",
                pygame.K_3: "milk",
                pygame.K_4: "ice",
                pygame.K_5: "fertilizer",
                pygame.K_6: "fishing_rod",
            }
            if event.key in shortcuts:
                self.buy_item(shortcuts[event.key])
            elif (
                event.key == pygame.K_f
                or getattr(event, "scancode", None) == pygame.KSCAN_F
            ):
                self.overlay = "fish_market"
            elif self.is_interaction_key(event):
                self.overlay = None
            return
        if (
            self.overlay is None
            and (
                event.key == pygame.K_f
                or getattr(event, "scancode", None) == pygame.KSCAN_F
            )
        ):
            self.use_fertilizer_nearby()
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
                self.blender_specials = {"premium_honey": False, "low_fat_milk": False}
                self.blender_message = "재료를 모두 비웠어요. 다시 직접 넣어 보세요."
                self.blender_message_error = False
                return
            if pygame.Rect(900, 550, 110, 56).collidepoint(position):
                self.overlay = None
                return
            for special_key in self.blender_specials:
                if self.blender_special_button(special_key).collidepoint(position):
                    self.toggle_blender_special(special_key)
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
            if SHOP_CLOSE_RECT.collidepoint(position):
                self.overlay = None
                return
            if SHOP_FISH_BUTTON.collidepoint(position):
                self.overlay = "fish_market"
                return
            for rect, key, _label, _color in self.shop_buttons:
                if rect.collidepoint(position):
                    self.buy_item(key)
                    return
        if self.overlay == "fish_market":
            for index, key in enumerate(FISH_KEYS):
                if fish_sale_card_rect(index).collidepoint(position):
                    self.sell_fish(key)
                    return
            if pygame.Rect(510, 555, 260, 52).collidepoint(position):
                self.overlay = "shop"
            return
        if self.overlay == "home":
            if HOME_EXIT_BUTTON.collidepoint(position):
                self.home_edit_mode = False
                self.save()
                self.overlay = None
                return
            if HOME_EDIT_BUTTON.collidepoint(position):
                self.toggle_home_edit()
                return
            if self.home_edit_mode:
                if HOME_ROTATE_BUTTON.collidepoint(position):
                    self.rotate_selected_furniture()
                    return
                if HOME_STORE_BUTTON.collidepoint(position):
                    self.store_selected_furniture()
                    return
                if HOME_DONE_BUTTON.collidepoint(position):
                    self.toggle_home_edit()
                    return
                if HOME_BUILD_AREA.collidepoint(position):
                    column = (position[0] - HOME_BUILD_AREA.x) // HOME_GRID_CELL
                    row = (position[1] - HOME_BUILD_AREA.y) // HOME_GRID_CELL
                    self.place_selected_furniture(column, row)
                    return
            for index, key in enumerate(FURNITURE_KEYS):
                if furniture_card_rect(index).collidepoint(position):
                    if key in self.state.furniture_owned:
                        self.select_furniture(key)
                        self.home_edit_mode = True
                        self.notify("바닥을 클릭하거나 방향키로 위치를 바꿔 보세요.")
                    else:
                        self.buy_furniture(key)
                    return
            return
        if self.overlay == "market":
            products = ("blueberries", "golden_blueberries", "organic_blueberries")
            for index, key in enumerate(products):
                if pygame.Rect(250 + index * 270, 275, 240, 170).collidepoint(position):
                    self.sell_market_item(key)
                    return
            if pygame.Rect(510, 520, 260, 52).collidepoint(position):
                self.overlay = None
            return
        if self.overlay == "facility":
            if pygame.Rect(370, 530, 240, 56).collidepoint(position):
                self.use_facility_main_action()
                return
            if pygame.Rect(630, 530, 240, 56).collidepoint(position):
                self.upgrade_selected_facility()
                return
            if pygame.Rect(510, 610, 260, 48).collidepoint(position):
                self.overlay = None
                return
            return
        if self.overlay == "daily_report":
            if pygame.Rect(510, 610, 260, 48).collidepoint(position):
                self.close_daily_report()
            return
        if self.overlay == "bag":
            if pygame.Rect(510, 614, 260, 48).collidepoint(position):
                self.overlay = None
            return
        if self.overlay is None and HUD_HELP_RECT.collidepoint(position):
            self.overlay = "help"

    def draw_ground(self) -> None:
        ground_palettes = {
            "봄": ((119, 177, 83), (124, 182, 85), (154, 202, 98)),
            "여름": ((104, 169, 70), (111, 177, 76), (145, 195, 86)),
            "가을": ((150, 164, 72), (158, 171, 77), (191, 190, 91)),
            "겨울": ((178, 196, 184), (188, 205, 194), (217, 226, 215)),
        }
        base_grass, tile_grass, grass_detail = ground_palettes[self.state.season]
        self.screen.fill(base_grass)
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
                    pygame.draw.rect(self.screen, tile_grass, (sx, sy, tile, tile))
                if value in (2, 9):
                    pygame.draw.rect(self.screen, grass_detail, (sx + 8, sy + 12, 3, 8))
                    pygame.draw.rect(self.screen, GRASS_DARK, (sx + 14, sy + 8, 3, 12))
                    pygame.draw.rect(self.screen, grass_detail, (sx + 19, sy + 14, 3, 6))
        for x, y, color in self.flowers:
            if self.state.season == "겨울":
                continue
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
            pygame.Rect(300, 925, 610, 70),
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

    def draw_fishing_line(self) -> None:
        if self.fishing_phase == "idle":
            return
        hand = self.world_to_screen((self.player.x + 10, self.player.y - 48))
        bobber_x, bobber_y = self.world_to_screen(self.fishing_bobber)
        if self.fishing_phase == "bite":
            bobber_y += 8
        pygame.draw.line(self.screen, (235, 231, 215), hand, (bobber_x, bobber_y), 2)
        pygame.draw.circle(self.screen, WOOD_DARK, (bobber_x, bobber_y), 7)
        pygame.draw.rect(self.screen, WHITE, (bobber_x - 4, bobber_y - 5, 8, 5))
        pygame.draw.rect(self.screen, RED, (bobber_x - 4, bobber_y, 8, 5))
        ripple = 18 if self.fishing_phase == "bite" else 11
        pygame.draw.ellipse(
            self.screen, WATER_LIGHT,
            (bobber_x - ripple, bobber_y + 4, ripple * 2, max(5, ripple // 2)), 2,
        )

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
        for row in range(4):
            start, end = roof_detail_segment(rect, row)
            pygame.draw.line(
                self.screen,
                tuple(max(0, c - 24) for c in roof),
                start,
                end,
                4,
            )
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
        self.text(f"한 알 {self.state.raw_blueberry_price()}코인", 15, MUTED,
                  rect.centerx, rect.y + 161, center=True)

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

    def draw_festival_decorations(self) -> None:
        if not is_blueberry_festival(self.state.current_day):
            return
        left = self.world_to_screen((980, 870))
        right = self.world_to_screen((1510, 870))
        pygame.draw.line(self.screen, WOOD_DARK, left, right, 5)
        festival_colors = (BLUEBERRY, GOLD, (207, 102, 171), WATER_LIGHT)
        for index, world_x in enumerate(range(1000, 1510, 55)):
            x, y = self.world_to_screen((world_x, 872))
            pygame.draw.polygon(
                self.screen,
                festival_colors[index % len(festival_colors)],
                [(x - 19, y), (x + 19, y), (x, y + 31)],
            )
        sign_center = self.world_to_screen((1245, 832))
        sign = pygame.Rect(sign_center[0] - 165, sign_center[1] - 27, 330, 54)
        rounded_rect(self.screen, sign, CREAM, 12, WOOD_DARK, 4)
        self.text("블루베리 축제 · 판매 금액 2배!", 18, BLUEBERRY_DARK,
                  sign.centerx, sign.centery, center=True)
        for world_x, color in ((990, BLUEBERRY), (1495, GOLD)):
            x, y = self.world_to_screen((world_x, 815))
            pygame.draw.line(self.screen, WOOD_DARK, (x, y + 18), (x, y + 72), 3)
            pygame.draw.circle(self.screen, color, (x, y), 19)
            pygame.draw.circle(self.screen, WHITE, (x - 6, y - 7), 5)

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
        if order is not None and order.vip and not departing:
            pygame.draw.polygon(
                self.screen,
                GOLD,
                [(x - 18, y - 91), (x - 13, y - 105), (x - 4, y - 94),
                 (x + 5, y - 106), (x + 16, y - 92)],
            )
            pygame.draw.rect(self.screen, (183, 116, 34), (x - 18, y - 94, 34, 6))
        elif order is not None and order.regular and not departing:
            pygame.draw.circle(self.screen, BLUEBERRY, (x + 23, y - 91), 9)
            pygame.draw.circle(self.screen, (223, 195, 244), (x + 23, y - 91), 5)

        if order is not None and not front and not departing:
            name = order.customer_name
            name_width = max(58, self.fonts[13].size(name)[0] + 16)
            name_tag = pygame.Rect(x - name_width // 2, y - 135, name_width, 24)
            tag_color = (
                (255, 229, 145) if order.vip
                else (232, 211, 248) if order.regular
                else (255, 247, 218)
            )
            rounded_rect(self.screen, name_tag, tag_color, 8, WOOD_DARK, 2)
            self.text(name, 13, BLUEBERRY_DARK, name_tag.centerx, name_tag.centery,
                      center=True)

        if front and order is not None and not departing:
            bubble = pygame.Rect(x - 149, y - 204, 298, 96)
            bubble_color = (255, 242, 183) if order.vip else (255, 250, 225)
            rounded_rect(self.screen, bubble, bubble_color, 12, WOOD_DARK, 3)
            pygame.draw.polygon(
                self.screen,
                bubble_color,
                [(x - 10, bubble.bottom - 2), (x + 8, bubble.bottom - 2), (x, bubble.bottom + 14)],
            )
            pygame.draw.lines(
                self.screen,
                WOOD_DARK,
                False,
                [(x - 10, bubble.bottom), (x, bubble.bottom + 14), (x + 8, bubble.bottom)],
                3,
            )
            if order.vip:
                vip_role = f" · {order.vip_title}" if order.vip_title else ""
                customer_title = f"VIP{vip_role} · {order.customer_name}님의 주문"
            elif order.regular:
                customer_title = f"단골 · {order.customer_name}님의 주문"
            else:
                customer_title = f"{order.customer_name}님의 주문"
            self.text(customer_title, 13, BLUEBERRY_DARK, bubble.centerx, bubble.y + 17,
                      center=True)
            self.text(
                f"블루베리 3  꿀 {order.honey}  우유 {order.milk}  얼음 {order.ice}",
                14,
                INK,
                bubble.centerx,
                bubble.y + 43,
                center=True,
            )
            sale_price = self.state.smoothie_sale_price(order)
            bonus = " · 축제 2배" if is_blueberry_festival(self.state.current_day) else ""
            self.text(f"받을 돈  {sale_price}코인{bonus}", 13, RED,
                      bubble.centerx, bubble.y + 64,
                      center=True)
            mood_label = "아주 만족" if order.satisfaction >= 85 else (
                "기다리는 중" if order.satisfaction >= 50 else "많이 기다렸어요"
            )
            self.text(f"만족도 {order.satisfaction}% · {mood_label}", 13,
                      GREEN_DARK if order.satisfaction >= 70 else RED,
                      bubble.centerx, bubble.y + 83, center=True)

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

    def draw_bush(
        self,
        rect: pygame.Rect,
        progress: float,
        ready: bool,
        fertilized: bool = False,
    ) -> None:
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
        if fertilized:
            badge = (rect.left + 15, rect.top + 13)
            pygame.draw.circle(self.screen, WOOD_DARK, badge, 12)
            pygame.draw.circle(self.screen, LEAF, badge, 9)
            pygame.draw.line(
                self.screen,
                WHITE,
                (badge[0] - 4, badge[1] + 3),
                (badge[0] + 4, badge[1] - 4),
                2,
            )
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
                self.draw_bush(
                    rect,
                    plot.progress(now),
                    plot.is_ready(now),
                    plot.fertilized,
                )
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

    def draw_streetlight(self, index: int, point: tuple[int, int]) -> None:
        x, y = self.world_to_screen(point)
        if not (-100 < x < SCREEN_W + 100 and -150 < y < SCREEN_H + 80):
            return
        installed = self.state.streetlights_installed[index]
        site_name = STREETLIGHT_SITE_LABELS[index]
        pygame.draw.ellipse(self.screen, (61, 105, 50), (x - 25, y - 7, 50, 14))
        if not installed:
            pygame.draw.circle(self.screen, WOOD_DARK, (x, y), 15)
            pygame.draw.circle(self.screen, (187, 142, 78), (x, y), 10)
            pygame.draw.rect(self.screen, WOOD_DARK, (x - 3, y - 31, 6, 28))
            sign_width = max(142, self.fonts[13].size(site_name)[0] + 34)
            sign = pygame.Rect(x - sign_width // 2, y - 93, sign_width, 54)
            rounded_rect(self.screen, sign, (244, 216, 151), 8, WOOD_DARK, 3)
            self.text(site_name, 14, INK, sign.centerx, sign.y + 16, center=True)
            self.text(f"{STREETLIGHT_COST:,}코인", 13, BLUEBERRY_DARK,
                      sign.centerx, sign.y + 38, center=True)
            return

        period = day_period_for_phase(self.game_clock()[3])
        is_lit = period in ("저녁", "밤", "새벽")
        post_color = (69, 66, 75)
        pygame.draw.rect(self.screen, (39, 38, 45), (x - 8, y - 82, 16, 84))
        pygame.draw.rect(self.screen, post_color, (x - 4, y - 79, 8, 78))
        pygame.draw.rect(self.screen, (42, 40, 47), (x - 17, y - 7, 34, 9))
        pygame.draw.line(self.screen, (39, 38, 45), (x, y - 78), (x + 22, y - 91), 7)
        pygame.draw.line(self.screen, post_color, (x, y - 78), (x + 21, y - 91), 3)
        pygame.draw.rect(self.screen, (43, 40, 47), (x + 13, y - 98, 25, 8))
        pygame.draw.polygon(
            self.screen,
            (58, 54, 60),
            [(x + 15, y - 90), (x + 36, y - 90), (x + 31, y - 76), (x + 20, y - 76)],
        )
        bulb_color = (255, 220, 112) if is_lit else (218, 210, 174)
        pygame.draw.rect(self.screen, bulb_color, (x + 20, y - 89, 11, 12))
        if is_lit:
            pygame.draw.circle(self.screen, (255, 235, 150), (x + 25, y - 82), 5)

    def draw_streetlights(self) -> None:
        for index, point in enumerate(STREETLIGHT_POSITIONS):
            self.draw_streetlight(index, point)

    def draw_facility(self, key: str, world_rect: pygame.Rect) -> None:
        rect = self.rect_to_screen(world_rect)
        if rect.right < -80 or rect.left > SCREEN_W + 80 or rect.bottom < -100 or rect.top > SCREEN_H + 80:
            return
        config = FACILITY_CONFIG[key]
        level = self.state.facility_level(key)
        pygame.draw.rect(self.screen, (74, 105, 55), rect.move(7, 8), border_radius=8)
        pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(8, 8), border_radius=9)
        pygame.draw.rect(self.screen, (213, 172, 104), rect, border_radius=7)
        pygame.draw.rect(self.screen, (236, 201, 137), rect.inflate(-8, -8), border_radius=5)

        if level <= 0:
            pygame.draw.rect(self.screen, (151, 105, 66), rect.inflate(-22, -24), 3)
            for offset in range(12, rect.width - 12, 20):
                pygame.draw.line(
                    self.screen,
                    (173, 126, 76),
                    (rect.x + offset, rect.y + 14),
                    (rect.x + offset - 10, rect.bottom - 14),
                    2,
                )
            locked = self.state.farm_rank < int(config["unlock_rank"])
            self.text("잠김" if locked else "건설 부지", 15, RED if locked else INK,
                      rect.centerx, rect.centery - 8, center=True)
            self.text(
                f"등급 {config['unlock_rank']}" if locked else f"{self.state.facility_build_cost(key):,}코인",
                13,
                MUTED,
                rect.centerx,
                rect.centery + 18,
                center=True,
            )
        elif key == "beehive":
            hive = pygame.Rect(rect.centerx - 33, rect.y + 23, 66, 55)
            pygame.draw.rect(self.screen, (113, 70, 39), hive.inflate(6, 6), border_radius=15)
            for index, width in enumerate((42, 57, 66, 57)):
                band = pygame.Rect(rect.centerx - width // 2, hive.y + index * 12, width, 15)
                pygame.draw.rect(self.screen, (235, 177, 49), band, border_radius=7)
            pygame.draw.circle(self.screen, (72, 50, 34), (rect.centerx, hive.bottom - 7), 7)
            for bee_index in range(level + 1):
                angle = time.time() * 2.2 + bee_index * 2.4
                bx = rect.centerx + round(math.cos(angle) * (38 + bee_index * 5))
                by = rect.centery - 13 + round(math.sin(angle) * 18)
                pygame.draw.circle(self.screen, INK, (bx, by), 4)
                pygame.draw.rect(self.screen, GOLD, (bx - 3, by - 2, 6, 4))
        elif key == "ice_maker":
            machine = pygame.Rect(rect.x + 25, rect.y + 17, rect.width - 50, rect.height - 34)
            pygame.draw.rect(self.screen, (49, 98, 121), machine.inflate(6, 6), border_radius=7)
            pygame.draw.rect(self.screen, (99, 184, 203), machine, border_radius=5)
            window = pygame.Rect(machine.x + 13, machine.y + 11, machine.width - 26, 31)
            pygame.draw.rect(self.screen, (229, 248, 245), window)
            for index in range(level + 1):
                cube_x = window.x + 8 + (index % 3) * 23
                pygame.draw.rect(self.screen, WATER_LIGHT, (cube_x, window.y + 7, 15, 15), 3)
            pygame.draw.circle(self.screen, GOLD, (machine.centerx, machine.bottom - 12), 5)
        else:
            wall = pygame.Rect(rect.x + 16, rect.y + 48, rect.width - 32, rect.height - 61)
            pygame.draw.rect(self.screen, (165, 76, 61), wall)
            roof = [(rect.x + 5, rect.y + 53), (rect.centerx, rect.y + 10), (rect.right - 5, rect.y + 53)]
            pygame.draw.polygon(self.screen, (112, 55, 49), roof)
            pygame.draw.polygon(self.screen, (205, 101, 75), roof, 5)
            door = pygame.Rect(rect.centerx - 35, wall.y + 23, 70, wall.height - 23)
            pygame.draw.rect(self.screen, CREAM, door)
            pygame.draw.circle(self.screen, WHITE, (door.centerx, door.y + 22), 21)
            pygame.draw.ellipse(self.screen, (237, 180, 190), (door.centerx - 14, door.y + 20, 28, 18))
            pygame.draw.circle(self.screen, INK, (door.centerx - 8, door.y + 18), 3)
            pygame.draw.circle(self.screen, INK, (door.centerx + 8, door.y + 18), 3)
            for index in range(level):
                pygame.draw.rect(self.screen, GOLD, (rect.x + 24 + index * 24, rect.bottom - 24, 15, 15))

        label_y = rect.bottom + 19
        label_width = max(112, self.fonts[14].size(str(config["name"]))[0] + 58)
        label = pygame.Rect(rect.centerx - label_width // 2, label_y - 15, label_width, 30)
        rounded_rect(self.screen, label, CREAM, 9, WOOD_DARK, 2)
        suffix = "부지" if level <= 0 else f"Lv.{level}"
        self.text(f"{config['name']} {suffix}", 14, INK, label.centerx, label.centery, center=True)
        if self.state.facility_is_ready(key):
            pygame.draw.circle(self.screen, WOOD_DARK, (rect.right - 5, rect.top - 5), 17)
            pygame.draw.circle(self.screen, GOLD, (rect.right - 5, rect.top - 5), 13)
            self.text("!", 16, INK, rect.right - 5, rect.top - 5, center=True)

    def draw_facilities(self) -> None:
        for key in FACILITY_KEYS:
            self.draw_facility(key, FACILITY_RECTS[key])

    def draw_tree(self, point: tuple[int, int]) -> None:
        x, y = self.world_to_screen(point)
        tree_index = TREE_POSITIONS.index(point)
        shake_timer = self.tree_shake_timers.get(tree_index, 0.0)
        if shake_timer > 0:
            x += round(math.sin((0.65 - shake_timer) * 48) * 7 * (shake_timer / 0.65))
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
            step_index = 0
            bob = 0
            if self.is_moving:
                step_index = int(self.walk_phase) % 4
                frame_index = (0, 1, 0, 2)[step_index]
                bob = -2 if step_index in (1, 3) else 0
            frame = self.player_frames[self.direction][frame_index]
            self.screen.blit(frame, frame.get_rect(midbottom=(x, y + 2 + bob)))
            if self.is_moving and self.direction in ("left", "right", "up"):
                self.draw_walking_feet(x, y, step_index)
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

    def draw_walking_feet(self, x: int, y: int, step_index: int) -> None:
        """Emphasize the stride in the photo-derived side/back sprites."""
        swing = 5 if step_index in (1, 2) else -5
        shoe = (45, 35, 75)
        sole = (27, 25, 43)
        if self.direction in ("left", "right"):
            facing = 1 if self.direction == "right" else -1
            back_x = x - facing * 7
            front_x = x + facing * (7 + swing)
            pygame.draw.rect(self.screen, sole, (back_x - 6, y - 6, 13, 7))
            pygame.draw.rect(self.screen, shoe, (back_x - 5, y - 8, 11, 5))
            pygame.draw.rect(self.screen, sole, (front_x - 6, y - 5, 14, 7))
            pygame.draw.rect(self.screen, shoe, (front_x - 5, y - 8, 12, 6))
        else:
            left_y = y - 6 + swing
            right_y = y - 6 - swing
            pygame.draw.rect(self.screen, sole, (x - 15, left_y, 12, 7))
            pygame.draw.rect(self.screen, shoe, (x - 14, left_y - 3, 10, 5))
            pygame.draw.rect(self.screen, sole, (x + 3, right_y, 12, 7))
            pygame.draw.rect(self.screen, shoe, (x + 4, right_y - 3, 10, 5))

    def draw_particles(self) -> None:
        for particle in self.particles:
            x, y = self.world_to_screen((particle.x, particle.y))
            pygame.draw.circle(self.screen, particle.color, (x, y), max(1, int(particle.size * particle.life)))

    def draw_tree_drops(self) -> None:
        for drop in self.tree_drops:
            x, y = self.world_to_screen((drop.x, drop.y))
            progress = 1.0 - drop.life / drop.duration
            y -= round(math.sin(min(1.0, progress) * math.pi) * 35)
            self.draw_item_icon(drop.key, (x, y), small=True)
            label = (
                f"+{drop.amount}코인"
                if drop.key == "coins"
                else f"{BAG_ITEM_LABELS[drop.key]} +{drop.amount}"
            )
            width = self.fonts[13].size(label)[0] + 18
            badge = pygame.Rect(x - width // 2, y + 21, width, 24)
            rounded_rect(self.screen, badge, CREAM, 7, WOOD_DARK, 2)
            self.text(label, 13, INK, badge.centerx, badge.centery, center=True)

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
            ((SHOP.centerx, SHOP.bottom + 34), "상점"),
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
        self.draw_fishing_line()
        self.draw_farm_fence()
        self.draw_plots()
        self.draw_expansion_sign()
        self.draw_facilities()
        self.draw_house(HOUSE, "블루베리 농장집", (244, 210, 151), (112, 73, 72))
        self.draw_house(SHOP, "상점", (240, 223, 174), (64, 124, 101))
        self.draw_house(CAFE, "블루베리 블렌더", (229, 205, 238), (112, 79, 157))
        self.draw_market()
        self.draw_smoothie_cart()
        self.draw_festival_decorations()
        self.draw_streetlights()
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
        # Drops are short-lived feedback, so keep them above the world sprites.
        self.draw_tree_drops()
        self.draw_interaction_marker()

    def current_objective(self) -> str:
        state = self.state
        for key in FACILITY_KEYS:
            if state.facility_is_ready(key):
                config = FACILITY_CONFIG[key]
                return f"{config['name']}에 {config['product_name']}이 준비됐어요. 가까이 가서 E를 누르세요."
        if state.berries_harvested == 0:
            return "익은 블루베리 나무 가까이 가서 E로 수확하세요."
        if state.blueberries < 3 and state.smoothies_sold == 0:
            return "밭을 돌보거나 남쪽 시장에서 생과를 팔아 보세요."
        if (
            state.money >= STREETLIGHT_COST
            and not all(state.streetlights_installed)
        ):
            return f"사진으로 지정한 가로등 부지에서 E를 누르면 {STREETLIGHT_COST:,}코인에 설치할 수 있어요."
        if state.active_plots < MAX_PLOTS and state.money >= state.land_cost:
            return f"확장 간판에서 다음 텃밭을 {state.land_cost:,}코인에 살 수 있어요."
        order = state.current_order
        if order is None:
            return "새 손님과 주문을 기다리고 있어요."
        if state.smoothies < 1:
            return (
                f"앞 주문: 블루베리 3 · 꿀 {order.honey} · 우유 {order.milk} · "
                f"얼음 {order.ice} → {state.smoothie_sale_price(order)}코인"
            )
        return f"완성된 주문 스무디를 카트에서 팔면 {state.smoothie_sale_price(order)}코인을 받아요."

    def game_clock(self) -> tuple[int, int, int, float]:
        elapsed = max(0.0, self.state.game_elapsed_seconds)
        day = int(elapsed // DAY_SECONDS) + 1
        phase = (elapsed % DAY_SECONDS) / DAY_SECONDS
        total_minutes = clock_minutes_for_phase(phase)
        return day, total_minutes // 60, total_minutes % 60, phase

    def draw_lighting(self) -> None:
        _day, _hour, _minute, phase = self.game_clock()
        period = day_period_for_phase(phase)
        red, green, blue, alpha = lighting_color_for_phase(phase)
        if alpha <= 0:
            return
        color_rgb = (red, green, blue)
        overlay = self._lighting_overlay
        overlay.fill((*color_rgb, alpha))

        if period in ("저녁", "밤", "새벽"):
            for installed, point in zip(
                self.state.streetlights_installed,
                STREETLIGHT_POSITIONS,
            ):
                if not installed:
                    continue
                lamp_x, lamp_y = self.world_to_screen((point[0] + 25, point[1] - 82))
                if not (-170 < lamp_x < SCREEN_W + 170 and -170 < lamp_y < SCREEN_H + 170):
                    continue
                pygame.draw.circle(
                    overlay,
                    (*color_rgb, round(alpha * 0.80)),
                    (lamp_x, lamp_y),
                    155,
                )
                pygame.draw.circle(
                    overlay,
                    (*color_rgb, round(alpha * 0.45)),
                    (lamp_x, lamp_y),
                    112,
                )
                pygame.draw.circle(
                    overlay,
                    (*color_rgb, round(alpha * 0.10)),
                    (lamp_x, lamp_y),
                    67,
                )
        self.screen.blit(overlay, (0, 0))

        if period in ("저녁", "밤", "새벽"):
            for installed, point in zip(
                self.state.streetlights_installed,
                STREETLIGHT_POSITIONS,
            ):
                if not installed:
                    continue
                lamp_x, lamp_y = self.world_to_screen((point[0] + 25, point[1] - 82))
                if not (-120 < lamp_x < SCREEN_W + 120 and -120 < lamp_y < SCREEN_H + 120):
                    continue
                self.screen.blit(self._lamp_glow, (lamp_x - 75, lamp_y - 75))

    def draw_celestial_cycle(self) -> None:
        day, _hour, _minute, phase = self.game_clock()
        body, x, y, progress = celestial_position_for_phase(phase)

        if body == "moon":
            star_strength = max(0.0, math.sin(progress * math.pi))
            if star_strength > 0.03:
                stars = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                for index in range(24):
                    star_x = (index * 137 + 61) % SCREEN_W
                    star_y = 108 + (index * 73) % 270
                    twinkle = 0.72 + 0.28 * math.sin(time.time() * 2.4 + index)
                    alpha = round(145 * star_strength * twinkle)
                    size = 2 if index % 4 else 3
                    pygame.draw.rect(
                        stars,
                        (223, 232, 255, alpha),
                        (star_x, star_y, size, size),
                    )
                self.screen.blit(stars, (0, 0))

        if not (-80 < x < SCREEN_W + 80):
            return
        halo = pygame.Surface((112, 112), pygame.SRCALPHA)
        if body == "sun":
            pygame.draw.circle(halo, (255, 203, 73, 18), (56, 56), 52)
            pygame.draw.circle(halo, (255, 222, 104, 30), (56, 56), 38)
            self.screen.blit(halo, (x - 56, y - 56))
            pygame.draw.rect(self.screen, (224, 143, 37), (x - 21, y - 21, 42, 42))
            pygame.draw.rect(self.screen, (255, 205, 66), (x - 17, y - 17, 34, 34))
            pygame.draw.rect(self.screen, (255, 235, 126), (x - 11, y - 11, 22, 22))
            for ray_x, ray_y in ((-30, -4), (26, -4), (-4, -30), (-4, 26)):
                pygame.draw.rect(self.screen, (255, 211, 75), (x + ray_x, y + ray_y, 8, 8))
        else:
            pygame.draw.circle(halo, (165, 196, 239, 16), (56, 56), 50)
            pygame.draw.circle(halo, (205, 222, 246, 28), (56, 56), 35)
            self.screen.blit(halo, (x - 56, y - 56))
            pygame.draw.rect(self.screen, (135, 160, 201), (x - 20, y - 20, 40, 40))
            pygame.draw.rect(self.screen, (224, 234, 238), (x - 16, y - 16, 32, 32))
            moon_phase = day % 4
            if moon_phase in (1, 3):
                cover_x = x - 4 if moon_phase == 1 else x - 14
                pygame.draw.rect(self.screen, (94, 108, 148), (cover_x, y - 16, 18, 32))
            elif moon_phase == 2:
                pygame.draw.rect(self.screen, (94, 108, 148), (x, y - 16, 16, 32))
            pygame.draw.rect(self.screen, (183, 197, 211), (x - 12, y - 10, 6, 6))
            pygame.draw.rect(self.screen, (183, 197, 211), (x + 5, y + 6, 7, 7))

    def draw_weather_effects(self) -> None:
        weather = self.state.weather
        tick = int(time.time() * 100)
        if weather == "rain":
            self.screen.blit(self._rain_veil, (0, 0))
            for x, y_offset, speed, length in RAIN_DROP_LAYOUT:
                # X never changes while each drop gets its own unrelated
                # starting height and speed. This makes the rain both fall
                # vertically and remain naturally scattered.
                y = (y_offset + tick * speed) % (SCREEN_H + 50) - 25
                pygame.draw.line(
                    self.screen,
                    (173, 210, 231),
                    (x, y),
                    (x, y + length),
                    2,
                )
        elif weather == "snow":
            for index in range(58):
                x = (index * 97 + tick) % (SCREEN_W + 30) - 15
                y = (index * 61 + tick * (1 + index % 3)) % (SCREEN_H + 30) - 15
                pygame.draw.circle(self.screen, WHITE, (x, y), 2 + index % 3)
        elif weather == "wind":
            for index in range(18):
                x = (index * 131 + tick * 4) % (SCREEN_W + 80) - 40
                y = 115 + (index * 79) % 500 + round(math.sin(tick / 15 + index) * 20)
                pygame.draw.ellipse(self.screen, (190, 154, 65), (x, y, 11, 6))
        elif weather == "heat":
            self.screen.blit(self._heat_veil, (0, 0))

    def draw_hud(self) -> None:
        left = pygame.Rect(12, 10, 382, 64)
        pygame.draw.rect(self.screen, (45, 43, 39), left.move(4, 5))
        pygame.draw.rect(self.screen, WOOD_DARK, left.inflate(5, 5))
        pygame.draw.rect(self.screen, (247, 218, 148), left)
        self.text("블루베리 밸리", 18, BLUEBERRY_DARK, 24, 18)
        stats = [
            ("코인", self.state.money, GOLD),
            ("열매", self.state.blueberries, BLUEBERRY),
            ("씨앗", self.state.seeds, GREEN),
            ("스무디", self.state.smoothies, (182, 82, 160)),
        ]
        x = 161
        for label, value, color in stats:
            pygame.draw.rect(self.screen, WOOD_DARK, (x, 25, 11, 11))
            pygame.draw.rect(self.screen, color, (x + 2, 27, 7, 7))
            self.text(label, 13, MUTED, x + 14, 16)
            self.text(str(value), 16, INK, x + 14, 38)
            x += 56

        objective = pygame.Rect(407, 10, 462, 64)
        pygame.draw.rect(self.screen, (45, 43, 39), objective.move(4, 5))
        pygame.draw.rect(self.screen, WOOD_DARK, objective.inflate(5, 5))
        pygame.draw.rect(self.screen, (246, 224, 165), objective)
        goal = self.state.daily_goal()
        goal_progress = min(self.state.daily_goal_progress(), int(goal["target"]))
        self.text(
            f"오늘 목표 · {goal['label']}  {goal_progress}/{goal['target']}",
            13, BLUEBERRY_DARK, 423, 18,
        )
        objective_text = self.current_objective()
        if len(objective_text) > 47:
            objective_text = objective_text[:46] + "…"
        self.text(objective_text, 13, INK, 423, 43)

        right = pygame.Rect(882, 10, 386, 64)
        pygame.draw.rect(self.screen, (45, 43, 39), right.move(4, 5))
        pygame.draw.rect(self.screen, WOOD_DARK, right.inflate(5, 5))
        pygame.draw.rect(self.screen, (247, 218, 148), right)
        day, hour, minute, phase = self.game_clock()
        season, season_day, _year = season_for_day(day)
        day_label = f"{day}일차"
        period = day_period_for_phase(phase)
        time_label = f"{hour:02d}:{minute:02d} {period}"
        season_label = (
            f"{season} {season_day}/{DAYS_PER_SEASON} · "
            f"{WEATHER_LABELS[self.state.weather]}"
        )
        rank_label = f"등급 {self.state.farm_rank} · 평판 {self.state.reputation}"
        inventory_label = f"꿀{self.state.honey} 우{self.state.milk} 얼{self.state.ice}"
        self.text(day_label, 13, MUTED, 895, 17)
        self.text(season_label, 13, INK, 951, 17)
        self.text(time_label, 16, INK, 895, 43)
        self.text(rank_label, 13, BLUEBERRY_DARK, 994, 45)
        inventory_x = HUD_HELP_RECT.right - 7 - self.fonts[13].size(inventory_label)[0]
        self.text(inventory_label, 13, INK, inventory_x, 45)
        pygame.draw.rect(self.screen, WOOD_DARK, HUD_HELP_RECT.inflate(3, 3))
        pygame.draw.rect(self.screen, PURPLE_LIGHT, HUD_HELP_RECT)
        self.text("도움말 H", 13, BLUEBERRY_DARK,
                  HUD_HELP_RECT.centerx, HUD_HELP_RECT.centery, center=True)

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

    def draw_market_overlay(self) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((31, 26, 39, 172))
        self.screen.blit(shade, (0, 0))
        card = pygame.Rect(190, 100, 900, 500)
        pygame.draw.rect(self.screen, (28, 25, 30), card.move(11, 11))
        pygame.draw.rect(self.screen, WOOD_DARK, card.inflate(14, 14))
        pygame.draw.rect(self.screen, WOOD, card)
        pygame.draw.rect(self.screen, CREAM, card.inflate(-18, -18))
        self.text("블루베리 생과 시장", 32, BLUEBERRY_DARK,
                  card.centerx, 145, center=True)
        self.text("일반·황금·유기농 블루베리를 한 알씩 바로 판매할 수 있어요.",
                  15, MUTED, card.centerx, 188, center=True)

        products = [
            (pygame.Rect(250, 275, 240, 170), "blueberries", "일반 블루베리",
             self.state.raw_blueberry_price(), self.state.blueberries, BLUEBERRY),
            (pygame.Rect(520, 275, 240, 170), "golden_blueberries", "황금 블루베리",
             GOLDEN_BLUEBERRY_PRICE, self.state.golden_blueberries, GOLD),
            (pygame.Rect(790, 275, 240, 170), "organic_blueberries", "유기농 블루베리",
             ORGANIC_BLUEBERRY_PRICE, self.state.organic_blueberries, LEAF),
        ]
        for index, (rect, key, label, price, amount, color) in enumerate(products, start=1):
            rounded_rect(self.screen, rect, (255, 244, 207), 14, WOOD_DARK, 4)
            self.draw_item_icon(key, (rect.centerx, rect.y + 48))
            self.text(f"[{index}] {label}", 18, INK,
                      rect.centerx, rect.y + 92, center=True)
            self.text(f"보유 {amount}개", 14, MUTED,
                      rect.centerx, rect.y + 119, center=True)
            price_badge = pygame.Rect(rect.centerx - 76, rect.y + 137, 152, 29)
            rounded_rect(self.screen, price_badge, color, 8, WOOD_DARK, 2)
            self.text(f"1개 판매 +{price}코인", 14, WHITE,
                      price_badge.centerx, price_badge.centery, center=True)

        close = pygame.Rect(510, 520, 260, 52)
        rounded_rect(self.screen, close, BLUEBERRY, 10, WOOD_DARK, 4)
        self.text("시장 나가기  E", 18, WHITE,
                  close.centerx, close.centery, center=True)

    def draw_shop_overlay(self) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((31, 26, 39, 165))
        self.screen.blit(shade, (0, 0))
        card = pygame.Rect(280, 55, 720, 620)
        pygame.draw.rect(self.screen, (32, 30, 31), card.move(10, 10))
        pygame.draw.rect(self.screen, WOOD_DARK, card.inflate(14, 14))
        pygame.draw.rect(self.screen, WOOD, card)
        pygame.draw.rect(self.screen, CREAM, card.inflate(-18, -18))
        self.text("상점", 32, BLUEBERRY_DARK, card.centerx, 91, center=True)
        self.text(f"보유 코인  {self.state.money}", 18, INK, card.centerx, 128, center=True)
        self.text("숫자 1~6 구매 · F 물고기 판매", 14, MUTED,
                  card.centerx, 160, center=True)
        amounts = {
            "seeds": self.state.seeds,
            "honey": self.state.honey,
            "milk": self.state.milk,
            "ice": self.state.ice,
            "fertilizer": self.state.fertilizer,
            "fishing_rod": 1 if self.state.fishing_rod else 0,
        }
        for index, (rect, key, label, color) in enumerate(self.shop_buttons, start=1):
            price = FISHING_ROD_COST if key == "fishing_rod" else ITEM_COSTS[key]
            already_owned = key == "fishing_rod" and self.state.fishing_rod
            affordable = self.state.money >= price and not already_owned
            fill = color if affordable else (174, 168, 177)
            pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(6, 6))
            pygame.draw.rect(self.screen, fill, rect)
            pygame.draw.rect(self.screen, tuple(min(255, channel + 18) for channel in fill), rect.inflate(-8, -8), 3)
            icon = self.ingredient_icons.get(key)
            text_center_x = rect.centerx
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=(rect.x + 39, rect.centery)))
                text_center_x += 25
            elif self.draw_item_icon(key, (rect.x + 39, rect.centery)):
                text_center_x += 25
            self.text(f"[{index}] {label} 1개", 18, WHITE,
                      text_center_x, rect.y + 24, center=True)
            status = (
                f"내구도 {self.state.fishing_rod_durability}/{FISHING_ROD_MAX_DURABILITY}"
                if already_owned
                else f"{price:,}코인 · 보유 {amounts[key]}"
            )
            self.text(status, 14, WHITE,
                      text_center_x, rect.y + 53, center=True)
        rounded_rect(self.screen, SHOP_FISH_BUTTON, WATER, 10, WOOD_DARK, 4)
        self.text("물고기 판매  F", 18, WHITE,
                  SHOP_FISH_BUTTON.centerx, SHOP_FISH_BUTTON.centery, center=True)
        rounded_rect(self.screen, SHOP_CLOSE_RECT, BLUEBERRY, 10, WOOD_DARK, 4)
        self.text("가게 나가기  E", 18, WHITE,
                  SHOP_CLOSE_RECT.centerx, SHOP_CLOSE_RECT.centery, center=True)

    def draw_fish_market_overlay(self) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((25, 34, 43, 178))
        self.screen.blit(shade, (0, 0))
        card = pygame.Rect(145, 65, 990, 600)
        pygame.draw.rect(self.screen, (28, 25, 30), card.move(11, 11))
        pygame.draw.rect(self.screen, WOOD_DARK, card.inflate(14, 14))
        pygame.draw.rect(self.screen, WATER, card)
        pygame.draw.rect(self.screen, CREAM, card.inflate(-18, -18))
        self.text("오늘 잡은 물고기 판매", 32, BLUEBERRY_DARK,
                  card.centerx, 108, center=True)
        self.text("연못의 찌가 물속으로 잠길 때 E를 눌러 낚아 올리세요.",
                  15, MUTED, card.centerx, 150, center=True)
        self.text(f"보유 코인  {self.state.money:,}", 17, INK,
                  card.centerx, 186, center=True)

        for index, key in enumerate(FISH_KEYS):
            rect = fish_sale_card_rect(index)
            rounded_rect(self.screen, rect, (245, 235, 201), 14, WOOD_DARK, 4)
            self.draw_item_icon(key, (rect.centerx, rect.y + 63))
            self.text(f"[{index + 1}] {BAG_ITEM_LABELS[key]}", 18, INK,
                      rect.centerx, rect.y + 116, center=True)
            self.text(f"가방에 {self.state.inventory(key)}마리", 14, MUTED,
                      rect.centerx, rect.y + 151, center=True)
            badge = pygame.Rect(rect.x + 22, rect.bottom - 58, rect.width - 44, 36)
            rounded_rect(self.screen, badge, WATER, 9, WOOD_DARK, 2)
            self.text(f"1마리 +{FISH_PRICES[key]:,}코인", 15, WHITE,
                      badge.centerx, badge.centery, center=True)

        back = pygame.Rect(510, 555, 260, 52)
        rounded_rect(self.screen, back, BLUEBERRY, 10, WOOD_DARK, 4)
        self.text("상점으로 돌아가기  E", 18, WHITE,
                  back.centerx, back.centery, center=True)

    def draw_furniture(
        self,
        key: str,
        center: tuple[int, int],
        scale: float = 1.0,
        *,
        rotation: int = 0,
        fit_rect: pygame.Rect | None = None,
    ) -> None:
        """Draw the first original pixel-art design for each farmhouse item."""
        sprite = self.furniture_sprites.get(key)
        if sprite is not None:
            if rotation % 2:
                sprite = pygame.transform.rotate(sprite, -90)
            if fit_rect is None:
                width = max(1, round(sprite.get_width() * scale))
                height = max(1, round(sprite.get_height() * scale))
            else:
                available_width = max(1, fit_rect.width - 8)
                available_height = max(1, fit_rect.height - 8)
                fit_scale = min(
                    available_width / sprite.get_width(),
                    available_height / sprite.get_height(),
                )
                width = max(1, round(sprite.get_width() * fit_scale))
                height = max(1, round(sprite.get_height() * fit_scale))
            rendered = pygame.transform.scale(sprite, (width, height))
            self.screen.blit(rendered, rendered.get_rect(center=center))
            return
        x, y = center
        if key == "bed":
            w, h = round(200 * scale), round(84 * scale)
            rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
            pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(8, 8), border_radius=5)
            pygame.draw.rect(self.screen, (161, 105, 64), rect, border_radius=4)
            pygame.draw.rect(self.screen, (236, 211, 169), rect.inflate(-12, -12))
            pygame.draw.rect(self.screen, (130, 91, 161),
                             (rect.x + round(58 * scale), rect.y + round(12 * scale),
                              rect.width - round(70 * scale), rect.height - round(24 * scale)))
            pygame.draw.rect(self.screen, WHITE,
                             (rect.x + round(12 * scale), rect.y + round(12 * scale),
                              round(44 * scale), rect.height - round(24 * scale)))
        elif key == "drawer":
            rect = pygame.Rect(x - round(38 * scale), y - round(48 * scale),
                               round(76 * scale), round(96 * scale))
            pygame.draw.rect(self.screen, WOOD_DARK, rect.inflate(7, 7))
            pygame.draw.rect(self.screen, (157, 92, 53), rect)
            for row in range(3):
                drawer = pygame.Rect(rect.x + 8, rect.y + 8 + row * round(29 * scale),
                                     rect.width - 16, round(23 * scale))
                pygame.draw.rect(self.screen, (194, 127, 70), drawer)
                pygame.draw.circle(self.screen, GOLD, drawer.center, max(2, round(3 * scale)))
        elif key == "desk":
            pygame.draw.rect(self.screen, WOOD_DARK,
                             (x - round(72 * scale), y - round(28 * scale),
                              round(144 * scale), round(21 * scale)))
            pygame.draw.rect(self.screen, (180, 116, 61),
                             (x - round(68 * scale), y - round(25 * scale),
                              round(136 * scale), round(14 * scale)))
            for leg_x in (x - round(58 * scale), x + round(47 * scale)):
                pygame.draw.rect(self.screen, WOOD_DARK,
                                 (leg_x, y - round(10 * scale),
                                  round(11 * scale), round(55 * scale)))
        elif key == "lantern":
            pygame.draw.line(self.screen, WOOD_DARK,
                             (x, y - round(56 * scale)), (x, y + round(32 * scale)),
                             max(3, round(7 * scale)))
            pygame.draw.rect(self.screen, WOOD_DARK,
                             (x - round(25 * scale), y - round(47 * scale),
                              round(50 * scale), round(49 * scale)))
            pygame.draw.rect(self.screen, (255, 219, 105),
                             (x - round(18 * scale), y - round(40 * scale),
                              round(36 * scale), round(35 * scale)))
            pygame.draw.rect(self.screen, WOOD_DARK,
                             (x - round(32 * scale), y + round(28 * scale),
                              round(64 * scale), round(9 * scale)))
        elif key == "flowerpot":
            pygame.draw.rect(self.screen, (173, 94, 55),
                             (x - round(23 * scale), y, round(46 * scale), round(36 * scale)))
            pygame.draw.rect(self.screen, WOOD_DARK,
                             (x - round(28 * scale), y - round(4 * scale),
                              round(56 * scale), round(9 * scale)))
            pygame.draw.line(self.screen, GREEN_DARK,
                             (x, y), (x, y - round(46 * scale)), max(3, round(6 * scale)))
            pygame.draw.ellipse(self.screen, LEAF,
                                (x - round(31 * scale), y - round(43 * scale),
                                 round(34 * scale), round(21 * scale)))
            pygame.draw.ellipse(self.screen, GREEN,
                                (x, y - round(55 * scale),
                                 round(34 * scale), round(23 * scale)))

    def draw_home_overlay(self) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((31, 26, 39, 178))
        self.screen.blit(shade, (0, 0))
        room = pygame.Rect(45, 30, 1190, 660)
        pygame.draw.rect(self.screen, (31, 27, 32), room.move(10, 10))
        pygame.draw.rect(self.screen, WOOD_DARK, room.inflate(12, 12))
        pygame.draw.rect(self.screen, (246, 228, 187), room)
        self.text("나의 농장집", 28, BLUEBERRY_DARK, 78, 49)
        subtitle = (
            "보관함에서 가구 선택 → 바닥 클릭 · 초록색이면 배치 가능"
            if self.home_edit_mode
            else f"가구를 구입한 뒤 G로 꾸미기 · 보유 {self.state.money:,}코인"
        )
        self.text(subtitle, 14, MUTED, 80, 91)
        rounded_rect(
            self.screen,
            HOME_EDIT_BUTTON,
            GREEN if self.home_edit_mode else (136, 102, 166),
            9,
            WOOD_DARK,
            3,
        )
        self.text(
            "배치 완료 G" if self.home_edit_mode else "꾸미기 모드 G",
            15,
            WHITE,
            HOME_EDIT_BUTTON.centerx,
            HOME_EDIT_BUTTON.centery,
            center=True,
        )
        rounded_rect(self.screen, HOME_EXIT_BUTTON, BLUEBERRY, 9, WOOD_DARK, 3)
        self.text("집 나가기 E", 15, WHITE,
                  HOME_EXIT_BUTTON.centerx, HOME_EXIT_BUTTON.centery, center=True)

        # The house is a top-down, snapped building canvas.  Its proportions
        # deliberately match the state grid so a saved cell always maps to the
        # same visible point on every frame.
        pygame.draw.rect(self.screen, WOOD_DARK, HOME_BUILD_AREA.inflate(8, 8))
        pygame.draw.rect(self.screen, (203, 151, 91), HOME_BUILD_AREA)
        for row in range(FURNITURE_GRID_ROWS):
            strip = pygame.Rect(
                HOME_BUILD_AREA.x,
                HOME_BUILD_AREA.y + row * HOME_GRID_CELL,
                HOME_BUILD_AREA.width,
                HOME_GRID_CELL,
            )
            pygame.draw.rect(
                self.screen,
                (211, 164, 101) if row % 2 == 0 else (196, 143, 86),
                strip,
            )
            pygame.draw.line(
                self.screen,
                (159, 105, 67),
                strip.bottomleft,
                strip.bottomright,
                2,
            )
        if self.home_edit_mode:
            for column in range(FURNITURE_GRID_COLUMNS + 1):
                x = HOME_BUILD_AREA.x + column * HOME_GRID_CELL
                pygame.draw.line(
                    self.screen,
                    (232, 199, 143),
                    (x, HOME_BUILD_AREA.top),
                    (x, HOME_BUILD_AREA.bottom),
                    1,
                )
            for row in range(FURNITURE_GRID_ROWS + 1):
                y = HOME_BUILD_AREA.y + row * HOME_GRID_CELL
                pygame.draw.line(
                    self.screen,
                    (232, 199, 143),
                    (HOME_BUILD_AREA.left, y),
                    (HOME_BUILD_AREA.right, y),
                    1,
                )

        for key in FURNITURE_KEYS:
            layout = self.state.furniture_layout.get(key)
            if layout is None:
                continue
            furniture_rect = self.furniture_grid_rect(key, *layout)
            if self.home_edit_mode and key == self.selected_furniture:
                pygame.draw.rect(self.screen, CREAM, furniture_rect.inflate(5, 5), 3)
            self.draw_furniture(
                key,
                furniture_rect.center,
                rotation=layout[2],
                fit_rect=furniture_rect,
            )

        if self.home_edit_mode and self.selected_furniture is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if HOME_BUILD_AREA.collidepoint((mouse_x, mouse_y)):
                column = (mouse_x - HOME_BUILD_AREA.x) // HOME_GRID_CELL
                row = (mouse_y - HOME_BUILD_AREA.y) // HOME_GRID_CELL
                preview_rect = self.furniture_grid_rect(
                    self.selected_furniture,
                    column,
                    row,
                    self.home_rotation,
                )
                valid = self.state.can_place_furniture(
                    self.selected_furniture,
                    column,
                    row,
                    self.home_rotation,
                )
                preview = pygame.Surface(preview_rect.size, pygame.SRCALPHA)
                preview.fill((86, 194, 100, 82) if valid else (211, 83, 77, 94))
                self.screen.blit(preview, preview_rect)
                pygame.draw.rect(
                    self.screen,
                    GREEN_DARK if valid else RED,
                    preview_rect,
                    4,
                )
                self.draw_furniture(
                    self.selected_furniture,
                    preview_rect.center,
                    rotation=self.home_rotation,
                    fit_rect=preview_rect,
                )

        selected_label = (
            FURNITURE_LABELS[self.selected_furniture]
            if self.selected_furniture is not None
            else "없음"
        )
        if self.home_edit_mode:
            self.text(
                f"선택: {selected_label} · 방향키 이동 · R 회전 · X 보관",
                14,
                BLUEBERRY_DARK,
                82,
                503,
            )
            for rect, label in (
                (HOME_ROTATE_BUTTON, "회전 R"),
                (HOME_STORE_BUTTON, "보관 X"),
                (HOME_DONE_BUTTON, "완료 Enter"),
            ):
                rounded_rect(self.screen, rect, (136, 102, 166), 8, WOOD_DARK, 3)
                self.text(label, 14, WHITE, rect.centerx, rect.centery, center=True)
        else:
            self.text(
                "한 종류당 하나씩 구입할 수 있고, 배치한 위치와 방향은 자동 저장됩니다.",
                14,
                MUTED,
                82,
                503,
            )

        for index, key in enumerate(FURNITURE_KEYS):
            rect = furniture_card_rect(index)
            owned = key in self.state.furniture_owned
            placed = key in self.state.furniture_layout
            selected = key == self.selected_furniture
            fill = (222, 237, 196) if owned else (255, 240, 198)
            rounded_rect(
                self.screen,
                rect,
                fill,
                11,
                BLUEBERRY_DARK if selected else WOOD_DARK,
                5 if selected else 3,
            )
            self.draw_furniture(key, (rect.centerx, rect.y + 39), 0.42)
            self.text(f"[{index + 1}] {FURNITURE_LABELS[key]}", 15, INK,
                      rect.centerx, rect.y + 75, center=True)
            status = (
                "배치됨" if placed
                else "보관 중" if owned
                else f"{FURNITURE_COSTS[key]:,}코인"
            )
            self.text(status, 13, GREEN_DARK if owned else BLUEBERRY_DARK,
                      rect.centerx, rect.y + 97, center=True)

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
        self.text("+ / -로 주문 맞추기 · 숫자 5 고급 꿀 · 숫자 6 저지방 우유",
                  14, MUTED, card.centerx, 119, center=True)

        order = self.state.current_order
        ticket = pygame.Rect(280, 143, 730, 100)
        rounded_rect(self.screen, ticket, (255, 247, 211), 12, WOOD_DARK, 3)
        if order is not None:
            customer_type = (
                f"VIP · {order.vip_title}" if order.vip and order.vip_title
                else "VIP" if order.vip
                else "단골" if order.regular
                else "손님"
            )
            self.text(f"{order.customer_name} · {customer_type} 주문표 · 만족도 {order.satisfaction}%",
                      15, BLUEBERRY_DARK, ticket.centerx, ticket.y + 17, center=True)
            self.text(f"“{order.story}”", 13, MUTED,
                      ticket.centerx, ticket.y + 38, center=True)
            self.text(
                f"블루베리 3   꿀 {order.honey}   우유 {order.milk}   얼음 {order.ice}",
                20,
                INK,
                ticket.centerx,
                ticket.y + 64,
                center=True,
            )
            selected_bonus = (
                sum(self.blender_specials.values()) * SPECIAL_SMOOTHIE_BONUS
            )
            displayed_price = self.state.smoothie_sale_price(order) + selected_bonus
            bonus_note = f" · 특수 재료 +{selected_bonus}" if selected_bonus else ""
            self.text(f"완성 판매가  {displayed_price}코인{bonus_note}", 14, RED,
                      ticket.centerx, ticket.y + 87, center=True)
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
            special_key = {
                "honey": "premium_honey",
                "milk": "low_fat_milk",
            }.get(key)
            if special_key is not None:
                special = self.blender_special_button(special_key)
                selected = self.blender_specials[special_key]
                special_color = GOLD if special_key == "premium_honey" else WATER
                rounded_rect(
                    self.screen,
                    special,
                    special_color if selected else (202, 190, 164),
                    8,
                    WOOD_DARK,
                    2,
                )
                shortcut = "5" if special_key == "premium_honey" else "6"
                short_label = "고급" if special_key == "premium_honey" else "저지방"
                selected_mark = "✓" if selected else "+"
                self.text(
                    f"[{shortcut}] {short_label} {selected_mark} x{self.state.inventory(special_key)}",
                    13,
                    WHITE if selected else INK,
                    special.centerx,
                    special.centery,
                    center=True,
                )
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
        selected_bonus = sum(self.blender_specials.values()) * SPECIAL_SMOOTHIE_BONUS
        blend_note = (
            f"특수 재료 보너스 +{selected_bonus}코인 · 3초 동안 갈아요."
            if selected_bonus
            else "재료가 부드러워질 때까지 3초만 기다려 주세요."
        )
        self.text(blend_note, 16, MUTED,
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
        for key, selected in self.blender_specials.items():
            if selected:
                bubbles.append((key, 0))
        for index, (key, _count) in enumerate(bubbles):
            angle = elapsed * (4.2 + index % 3) + index * 1.7
            radius_x = 28 + (index * 17) % 63
            radius_y = 42 + (index * 11) % 78
            bubble_x = center_x + round(math.cos(angle) * radius_x)
            bubble_y = 350 + round(math.sin(angle * 1.15) * radius_y)
            if not self.draw_item_icon(key, (bubble_x, bubble_y), small=True):
                radius = 7 if key == "blueberries" else 9
                pygame.draw.circle(self.screen, WOOD_DARK, (bubble_x, bubble_y), radius + 2)
                pygame.draw.circle(
                    self.screen, ingredient_colors.get(key, GOLD), (bubble_x, bubble_y), radius
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

    def draw_facility_overlay(self) -> None:
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((31, 26, 39, 178))
        self.screen.blit(shade, (0, 0))
        card = pygame.Rect(280, 55, 720, 620)
        pygame.draw.rect(self.screen, (28, 25, 30), card.move(11, 11))
        pygame.draw.rect(self.screen, WOOD_DARK, card.inflate(14, 14))
        pygame.draw.rect(self.screen, WOOD, card)
        pygame.draw.rect(self.screen, CREAM, card.inflate(-18, -18))

        key = self.selected_facility
        config = FACILITY_CONFIG[key]
        level = self.state.facility_level(key)
        required_rank = int(config["unlock_rank"])
        unlocked = self.state.farm_rank >= required_rank
        self.text(f"{config['name']} 관리", 32, BLUEBERRY_DARK,
                  card.centerx, 96, center=True)
        self.text(
            f"농장 등급 {self.state.farm_rank} · 평판 {self.state.reputation}",
            16, MUTED, card.centerx, 132, center=True,
        )

        product = str(config["product"])
        icon = self.ingredient_icons.get(product)
        icon_panel = pygame.Rect(350, 168, 180, 205)
        rounded_rect(self.screen, icon_panel, (248, 228, 181), 15, WOOD_DARK, 4)
        if icon is not None:
            self.screen.blit(icon, icon.get_rect(center=(icon_panel.centerx, icon_panel.y + 70)))
        self.text(str(config["product_name"]), 25, INK,
                  icon_panel.centerx, icon_panel.y + 125, center=True)
        if level > 0:
            self.text(f"하루 {self.state.facility_yield(key)}개", 17, BLUEBERRY_DARK,
                      icon_panel.centerx, icon_panel.y + 159, center=True)
            self.text(f"보유 {self.state.inventory(product)}개", 14, MUTED,
                      icon_panel.centerx, icon_panel.y + 185, center=True)
        else:
            self.text("아직 생산하지 않음", 15, MUTED,
                      icon_panel.centerx, icon_panel.y + 167, center=True)

        status_panel = pygame.Rect(555, 168, 355, 205)
        rounded_rect(self.screen, status_panel, (255, 247, 215), 15, WOOD_DARK, 4)
        self.text("시설 상태", 20, BLUEBERRY_DARK,
                  status_panel.centerx, status_panel.y + 29, center=True)
        stars = "★" * level + "☆" * (MAX_FACILITY_LEVEL - level)
        self.text(stars, 25, GOLD if level else MUTED,
                  status_panel.centerx, status_panel.y + 68, center=True)
        if level <= 0:
            status = (
                f"건설 가능 · {self.state.facility_build_cost(key):,}코인"
                if unlocked
                else f"잠김 · 농장 등급 {required_rank} 필요"
            )
            detail = "건설하면 다음 날부터 생산을 시작해요."
        elif self.state.facility_is_ready(key):
            status = f"{config['product_name']} {self.state.facility_yield(key)}개 준비 완료!"
            detail = "받기를 누르면 재료 가방으로 옮겨져요."
        else:
            ready_day = self.state.facility_ready_days[key]
            status = f"생산 중 · {ready_day}일차에 준비"
            detail = "게임 날짜가 바뀌면 다시 찾아오세요."
        self.text(status, 17, RED if level <= 0 and not unlocked else INK,
                  status_panel.centerx, status_panel.y + 116, center=True)
        self.wrapped_text(detail, 14, MUTED,
                          pygame.Rect(status_panel.x + 24, status_panel.y + 148,
                                      status_panel.width - 48, 45), center=True)

        info = pygame.Rect(350, 397, 560, 95)
        rounded_rect(self.screen, info, PURPLE_LIGHT, 12, WOOD_DARK, 3)
        if level <= 0:
            main_text = f"{config['name']} 건설"
            upgrade_text = "건설 후 업그레이드"
        else:
            main_text = f"{config['product_name']} 받기  E"
            upgrade_cost = self.state.facility_upgrade_cost(key)
            if upgrade_cost is None:
                upgrade_text = "최고 단계"
            else:
                next_rank = required_rank + level
                upgrade_text = f"Lv.{level + 1} 업그레이드 · {upgrade_cost:,}코인 · 등급 {next_rank}"
        self.text(main_text, 18, BLUEBERRY_DARK, info.centerx, info.y + 28, center=True)
        self.text(upgrade_text, 15, MUTED, info.centerx, info.y + 64, center=True)

        main_button = pygame.Rect(370, 530, 240, 56)
        upgrade_button = pygame.Rect(630, 530, 240, 56)
        close = pygame.Rect(510, 610, 260, 48)
        rounded_rect(self.screen, main_button, GREEN if unlocked else (151, 142, 139),
                     10, WOOD_DARK, 4)
        rounded_rect(self.screen, upgrade_button, GOLD if level > 0 else (184, 166, 132),
                     10, WOOD_DARK, 4)
        rounded_rect(self.screen, close, BLUEBERRY, 10, WOOD_DARK, 4)
        self.text("건설하기" if level <= 0 else "생산품 받기", 18, WHITE,
                  main_button.centerx, main_button.centery, center=True)
        self.text("업그레이드  U", 18, INK,
                  upgrade_button.centerx, upgrade_button.centery, center=True)
        self.text("시설 화면 닫기", 17, WHITE, close.centerx, close.centery, center=True)

    def draw_daily_report_overlay(self) -> None:
        report = self.state.pending_daily_report
        if not report:
            return
        shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        shade.fill((28, 24, 38, 188))
        self.screen.blit(shade, (0, 0))
        card = pygame.Rect(300, 42, 680, 638)
        pygame.draw.rect(self.screen, (28, 25, 30), card.move(12, 12))
        pygame.draw.rect(self.screen, WOOD_DARK, card.inflate(14, 14))
        pygame.draw.rect(self.screen, (131, 88, 54), card)
        pygame.draw.rect(self.screen, CREAM, card.inflate(-18, -18))

        finished_day = int(report["day"])
        self.text(f"{finished_day}일차 농장 정산", 32, BLUEBERRY_DARK,
                  card.centerx, 84, center=True)
        self.text("오늘도 농장과 스무디 가게를 잘 운영했어요!", 16, MUTED,
                  card.centerx, 122, center=True)

        metrics = [
            ("판매 수입", f"+{int(report['earned']):,}코인", GREEN_DARK),
            ("사용한 돈", f"-{int(report['spent']):,}코인", RED),
            ("블루베리 수확", f"{int(report['harvested'])}개", BLUEBERRY_DARK),
            ("스무디 판매", f"{int(report['smoothies_sold'])}잔", (139, 69, 148)),
        ]
        for index, (label, value, color) in enumerate(metrics):
            column, row = index % 2, index // 2
            rect = pygame.Rect(365 + column * 285, 158 + row * 94, 255, 72)
            rounded_rect(self.screen, rect, (255, 247, 215), 11, WOOD_DARK, 3)
            self.text(label, 14, MUTED, rect.centerx, rect.y + 20, center=True)
            self.text(value, 22, color, rect.centerx, rect.y + 48, center=True)

        profit = int(report["profit"])
        self.text(f"오늘의 순이익  {profit:+,}코인", 22,
                  GREEN_DARK if profit >= 0 else RED, card.centerx, 365, center=True)
        goal_box = pygame.Rect(365, 398, 550, 86)
        goal_complete = bool(report["goal_complete"])
        rounded_rect(
            self.screen, goal_box,
            (221, 239, 187) if goal_complete else (239, 219, 187),
            12, WOOD_DARK, 3,
        )
        self.text("일일 목표 달성!" if goal_complete else "일일 목표 미달성",
                  18, GREEN_DARK if goal_complete else RED,
                  goal_box.centerx, goal_box.y + 22, center=True)
        self.text(
            f"{report['goal_label']}  {report['goal_progress']}/{report['goal_target']}",
            15, INK, goal_box.centerx, goal_box.y + 48, center=True,
        )
        reward_text = (
            f"보상 +{report['reward']}코인 · 평판 +{report['reputation_reward']}"
            if goal_complete else "내일 다시 도전해 보세요."
        )
        self.text(reward_text, 14, MUTED, goal_box.centerx, goal_box.y + 70, center=True)

        next_day = int(report["next_day"])
        season, season_day, year = season_for_day(next_day)
        weather = WEATHER_LABELS[self.state.weather]
        next_box = pygame.Rect(365, 505, 550, 77)
        rounded_rect(self.screen, next_box, PURPLE_LIGHT, 12, WOOD_DARK, 3)
        self.text(f"{year}년차 {season} {season_day}/{DAYS_PER_SEASON}일 · {weather}",
                  18, BLUEBERRY_DARK, next_box.centerx, next_box.y + 25, center=True)
        next_note = (
            "오늘은 블루베리 축제! 스무디 판매 금액이 2배예요."
            if is_blueberry_festival(next_day)
            else str(self.state.daily_goal(next_day)["label"])
        )
        self.text(next_note, 14, RED if is_blueberry_festival(next_day) else MUTED,
                  next_box.centerx, next_box.y + 53, center=True)

        close = pygame.Rect(510, 610, 260, 48)
        rounded_rect(self.screen, close, BLUEBERRY, 10, WOOD_DARK, 4)
        self.text("새로운 하루 시작  E", 18, WHITE,
                  close.centerx, close.centery, center=True)

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
            icon_center = (rect.x + 38, rect.y + 50)
            if self.draw_item_icon(key, icon_center):
                pass
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
            label_size = 13 if key in ("golden_blueberries", "premium_honey", "low_fat_milk") else 15
            self.text(BAG_ITEM_LABELS[key], label_size, INK, rect.x + 65, rect.y + 24)
            badge = pygame.Rect(rect.x + 68, rect.y + 49, 48, 29)
            rounded_rect(self.screen, badge, BLUEBERRY_DARK, 8)
            badge_text = (
                f"{self.state.fishing_rod_durability}/{FISHING_ROD_MAX_DURABILITY}"
                if key == "fishing_rod"
                else f"×{amount}"
            )
            self.text(badge_text, 14 if key == "fishing_rod" else 16,
                      WHITE, badge.centerx, badge.centery, center=True)

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
            self.text("일반 재료와 나무에서 얻은 희귀 재료가 종류별로 자동 정리됩니다.",
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
            ("이동·메뉴", "WASD · B 가방 · H 도움말", "한글 입력 상태에서도 물리 키로 메뉴를 열 수 있어요."),
            ("농사·비료", "밭 E · 자랄 때 F", "수확 뒤 60초 재성장, 비료를 주면 유기농 열매를 얻어요."),
            ("낚시", "상점 낚싯대 → 연못 E", "찌를 던질 때 내구도 1이 줄고 40번째 사용 뒤 부서져요."),
            ("집·가구", "농장집 문 앞 E", "집에 들어가 침대·서랍·책상·랜턴·화분을 구입해 꾸며요."),
            ("제조·판매", "블렌더 E → +/- · 5/6", "주문 재료를 맞추면 3초 동안 소리와 함께 직접 갈아요."),
            ("낮·밤·가로등", "하루 24분 · 부지 E", "지정된 5곳의 가로등은 저녁부터 새벽까지 자동으로 켜져요."),
        ]
        y = 176
        for title, control, body in rows:
            pygame.draw.circle(self.screen, BLUEBERRY, (326, y + 25), 20)
            self.text(title[0], 17, WHITE, 326, y + 25, center=True)
            self.text(title, 18, INK, 362, y + 3)
            self.text(control, 15, BLUEBERRY_DARK, 545, y + 5)
            self.wrapped_text(body, 14, MUTED, pygame.Rect(362, y + 31, 570, 35))
            y += 64
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
        self.draw_celestial_cycle()
        self.draw_weather_effects()
        self.draw_impact_flash()
        self.draw_action_effects()
        self.draw_hud()
        self.draw_prompt()
        self.draw_toast()
        if self.overlay == "market":
            self.draw_market_overlay()
        elif self.overlay == "shop":
            self.draw_shop_overlay()
        elif self.overlay == "fish_market":
            self.draw_fish_market_overlay()
        elif self.overlay == "home":
            self.draw_home_overlay()
        elif self.overlay == "blender":
            self.draw_blender_overlay()
        elif self.overlay == "blending":
            self.draw_blending_overlay()
        elif self.overlay == "facility":
            self.draw_facility_overlay()
        elif self.overlay == "daily_report":
            self.draw_daily_report_overlay()
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
