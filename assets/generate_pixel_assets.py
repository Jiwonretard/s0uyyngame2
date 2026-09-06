"""Regenerate the original fish, furniture, and facility pixel-art PNG assets."""

from __future__ import annotations

from pathlib import Path

import pygame


ASSET_DIR = Path(__file__).resolve().parent
FISH_DIR = ASSET_DIR / "fish"
FURNITURE_DIR = ASSET_DIR / "furniture"
FACILITY_DIR = ASSET_DIR / "facilities"
OUTLINE = (77, 47, 38)
HIGHLIGHT = (255, 239, 190)
BLUEBERRY = (76, 67, 164)
BLUEBERRY_DARK = (40, 35, 91)
GREEN = (54, 119, 61)
GREEN_DARK = (35, 82, 45)
LEAF = (64, 138, 64)
GOLD = (236, 167, 48)
WATER_LIGHT = (126, 199, 197)
WOOD = (139, 85, 48)
WOOD_LIGHT = (207, 139, 73)
CREAM = (255, 239, 190)
RED = (169, 65, 62)


def enlarged(surface: pygame.Surface, scale: int = 4) -> pygame.Surface:
    return pygame.transform.scale(
        surface,
        (surface.get_width() * scale, surface.get_height() * scale),
    )


def fish_sprite(key: str) -> pygame.Surface:
    canvas = pygame.Surface((24, 18), pygame.SRCALPHA)
    if key == "turtle":
        pygame.draw.ellipse(canvas, OUTLINE, (4, 4, 15, 11))
        pygame.draw.ellipse(canvas, GREEN_DARK, (5, 5, 13, 9))
        pygame.draw.rect(canvas, LEAF, (8, 7, 7, 5))
        pygame.draw.line(canvas, WATER_LIGHT, (9, 8), (14, 11), 1)
        pygame.draw.circle(canvas, OUTLINE, (20, 9), 3)
        pygame.draw.circle(canvas, GREEN, (20, 9), 2)
        for x, y in ((5, 4), (5, 14), (16, 4), (16, 14)):
            pygame.draw.rect(canvas, OUTLINE, (x, y, 3, 2))
        pygame.draw.rect(canvas, HIGHLIGHT, (20, 8, 1, 1))
        return enlarged(canvas)

    palettes = {
        "carp": ((215, 118, 54), (244, 171, 70), (255, 216, 119)),
        "crucian_carp": ((141, 126, 86), (195, 175, 109), (236, 215, 156)),
        "bass": ((50, 104, 72), (77, 143, 90), (153, 190, 111)),
    }
    dark, body, light = palettes[key]
    if key == "bass":
        pygame.draw.polygon(canvas, OUTLINE, [(4, 9), (1, 5), (1, 13)])
        pygame.draw.ellipse(canvas, OUTLINE, (3, 4, 19, 11))
        pygame.draw.ellipse(canvas, body, (4, 5, 17, 9))
        pygame.draw.line(canvas, dark, (5, 10), (18, 10), 2)
        pygame.draw.polygon(canvas, OUTLINE, [(9, 5), (12, 1), (15, 5)])
        pygame.draw.polygon(canvas, dark, [(10, 5), (12, 2), (14, 5)])
    else:
        pygame.draw.polygon(canvas, OUTLINE, [(5, 9), (1, 4), (1, 14)])
        pygame.draw.polygon(canvas, dark, [(5, 9), (2, 6), (2, 12)])
        body_rect = (4, 3, 17, 13) if key == "carp" else (4, 4, 17, 11)
        pygame.draw.ellipse(canvas, OUTLINE, body_rect)
        inset = (5, 4, 15, 11) if key == "carp" else (5, 5, 15, 9)
        pygame.draw.ellipse(canvas, body, inset)
        pygame.draw.polygon(canvas, dark, [(9, 4), (12, 1), (14, 5)])
    pygame.draw.rect(canvas, light, (8, 6, 3, 2))
    pygame.draw.rect(canvas, dark, (9, 11, 3, 2))
    pygame.draw.rect(canvas, light, (13, 8, 2, 2))
    pygame.draw.circle(canvas, HIGHLIGHT, (18, 7), 1)
    pygame.draw.circle(canvas, BLUEBERRY_DARK, (19, 7), 1)
    pygame.draw.rect(canvas, OUTLINE, (20, 9, 3, 1))
    return enlarged(canvas)


def furniture_sprite(key: str) -> pygame.Surface:
    canvas = pygame.Surface((32, 24), pygame.SRCALPHA)
    if key == "bed":
        pygame.draw.rect(canvas, OUTLINE, (2, 3, 28, 18))
        pygame.draw.rect(canvas, (174, 112, 63), (3, 4, 26, 16))
        pygame.draw.rect(canvas, (239, 220, 177), (5, 6, 22, 12))
        pygame.draw.rect(canvas, HIGHLIGHT, (5, 6, 6, 12))
        pygame.draw.rect(canvas, BLUEBERRY, (12, 6, 15, 12))
        pygame.draw.rect(canvas, (116, 101, 192), (14, 8, 11, 3))
        pygame.draw.rect(canvas, GOLD, (3, 3, 26, 2))
    elif key == "drawer":
        pygame.draw.rect(canvas, OUTLINE, (7, 3, 18, 18))
        pygame.draw.rect(canvas, (168, 100, 55), (8, 4, 16, 16))
        for row in range(3):
            pygame.draw.rect(canvas, (203, 135, 73), (10, 6 + row * 5, 12, 4))
            pygame.draw.rect(canvas, OUTLINE, (15, 7 + row * 5, 2, 1))
        pygame.draw.rect(canvas, GOLD, (9, 4, 14, 2))
    elif key == "desk":
        pygame.draw.rect(canvas, OUTLINE, (2, 5, 28, 14))
        pygame.draw.rect(canvas, (183, 118, 63), (3, 6, 26, 12))
        pygame.draw.rect(canvas, (222, 155, 80), (5, 8, 22, 7))
        pygame.draw.rect(canvas, BLUEBERRY_DARK, (6, 9, 8, 5))
        pygame.draw.rect(canvas, (240, 213, 158), (7, 10, 6, 3))
        pygame.draw.rect(canvas, OUTLINE, (20, 8, 6, 7))
        pygame.draw.rect(canvas, GOLD, (22, 10, 2, 2))
    elif key == "lantern":
        pygame.draw.rect(canvas, OUTLINE, (10, 2, 12, 20))
        pygame.draw.rect(canvas, GOLD, (12, 6, 8, 11))
        pygame.draw.rect(canvas, (255, 224, 112), (14, 7, 4, 9))
        pygame.draw.rect(canvas, HIGHLIGHT, (15, 8, 2, 4))
        pygame.draw.rect(canvas, OUTLINE, (8, 4, 16, 3))
        pygame.draw.rect(canvas, OUTLINE, (8, 17, 16, 3))
        pygame.draw.line(canvas, OUTLINE, (12, 3), (15, 0), 2)
        pygame.draw.line(canvas, OUTLINE, (20, 3), (17, 0), 2)
    elif key == "flowerpot":
        pygame.draw.rect(canvas, OUTLINE, (10, 14, 12, 8))
        pygame.draw.polygon(canvas, (177, 93, 51), [(11, 15), (21, 15), (20, 21), (12, 21)])
        pygame.draw.rect(canvas, GOLD, (12, 15, 8, 2))
        pygame.draw.line(canvas, GREEN_DARK, (16, 15), (16, 5), 2)
        pygame.draw.ellipse(canvas, LEAF, (7, 7, 9, 6))
        pygame.draw.ellipse(canvas, GREEN, (16, 4, 9, 7))
        pygame.draw.rect(canvas, HIGHLIGHT, (19, 6, 2, 1))
    return enlarged(canvas)


def facility_sprite(key: str) -> pygame.Surface:
    """Create readable farm facilities in the same chunky pixel style."""
    if key == "beehive":
        canvas = pygame.Surface((36, 30), pygame.SRCALPHA)
        pygame.draw.rect(canvas, OUTLINE, (3, 24, 30, 3))
        pygame.draw.rect(canvas, WOOD, (5, 24, 26, 2))
        pygame.draw.rect(canvas, OUTLINE, (6, 26, 4, 4))
        pygame.draw.rect(canvas, OUTLINE, (26, 26, 4, 4))
        pygame.draw.rect(canvas, OUTLINE, (6, 7, 24, 17))
        pygame.draw.rect(canvas, (230, 170, 57), (8, 8, 20, 15))
        pygame.draw.polygon(canvas, OUTLINE, [(4, 8), (10, 2), (26, 2), (32, 8)])
        pygame.draw.polygon(canvas, WOOD_LIGHT, [(7, 7), (11, 4), (25, 4), (29, 7)])
        pygame.draw.rect(canvas, CREAM, (10, 10, 16, 3))
        pygame.draw.rect(canvas, WOOD, (8, 14, 20, 2))
        pygame.draw.rect(canvas, CREAM, (10, 17, 16, 3))
        pygame.draw.rect(canvas, OUTLINE, (15, 18, 6, 5))
        pygame.draw.rect(canvas, (57, 45, 39), (17, 19, 3, 3))
        pygame.draw.rect(canvas, WOOD_LIGHT, (13, 22, 10, 2))
        pygame.draw.rect(canvas, OUTLINE, (30, 11, 4, 3))
        pygame.draw.rect(canvas, GOLD, (31, 12, 2, 1))
        pygame.draw.rect(canvas, HIGHLIGHT, (30, 10, 1, 1))
        return enlarged(canvas)

    if key == "ice_maker":
        canvas = pygame.Surface((40, 30), pygame.SRCALPHA)
        pygame.draw.rect(canvas, OUTLINE, (3, 2, 34, 26))
        pygame.draw.rect(canvas, (78, 137, 161), (5, 4, 30, 22))
        pygame.draw.rect(canvas, (143, 205, 211), (7, 5, 26, 3))
        pygame.draw.rect(canvas, OUTLINE, (8, 9, 24, 8))
        pygame.draw.rect(canvas, (220, 245, 239), (10, 10, 20, 6))
        pygame.draw.rect(canvas, WATER_LIGHT, (11, 11, 5, 4))
        pygame.draw.rect(canvas, HIGHLIGHT, (12, 11, 2, 1))
        pygame.draw.rect(canvas, (96, 177, 198), (18, 10, 5, 5))
        pygame.draw.rect(canvas, HIGHLIGHT, (19, 10, 2, 2))
        pygame.draw.rect(canvas, WATER_LIGHT, (25, 11, 4, 4))
        pygame.draw.rect(canvas, OUTLINE, (10, 19, 20, 7))
        pygame.draw.rect(canvas, (43, 81, 103), (12, 20, 16, 4))
        pygame.draw.rect(canvas, WATER_LIGHT, (13, 22, 5, 3))
        pygame.draw.rect(canvas, (220, 245, 239), (20, 21, 6, 4))
        pygame.draw.rect(canvas, GOLD, (32, 11, 2, 2))
        pygame.draw.rect(canvas, OUTLINE, (7, 27, 6, 3))
        pygame.draw.rect(canvas, OUTLINE, (27, 27, 6, 3))
        return enlarged(canvas)

    if key == "cow_barn":
        canvas = pygame.Surface((64, 42), pygame.SRCALPHA)
        pygame.draw.rect(canvas, OUTLINE, (4, 16, 56, 24))
        pygame.draw.rect(canvas, (224, 183, 122), (6, 18, 52, 20))
        for y in (23, 29, 35):
            pygame.draw.line(canvas, (194, 142, 91), (6, y), (58, y), 1)
        pygame.draw.polygon(canvas, OUTLINE, [(2, 18), (15, 3), (49, 3), (62, 18)])
        pygame.draw.polygon(canvas, RED, [(6, 16), (17, 5), (47, 5), (58, 16)])
        pygame.draw.line(canvas, (210, 101, 75), (11, 13), (53, 13), 2)
        pygame.draw.rect(canvas, OUTLINE, (27, 7, 10, 8))
        pygame.draw.rect(canvas, CREAM, (29, 9, 6, 4))
        pygame.draw.rect(canvas, OUTLINE, (9, 22, 11, 10))
        pygame.draw.rect(canvas, (102, 171, 184), (11, 24, 7, 6))
        pygame.draw.line(canvas, CREAM, (14, 24), (14, 30), 1)
        pygame.draw.rect(canvas, OUTLINE, (44, 22, 11, 10))
        pygame.draw.rect(canvas, (102, 171, 184), (46, 24, 7, 6))
        pygame.draw.line(canvas, CREAM, (49, 24), (49, 30), 1)
        pygame.draw.rect(canvas, OUTLINE, (22, 19, 20, 21))
        pygame.draw.rect(canvas, WOOD, (24, 21, 16, 17))
        pygame.draw.line(canvas, WOOD_LIGHT, (32, 21), (32, 38), 1)
        pygame.draw.ellipse(canvas, OUTLINE, (25, 22, 14, 12))
        pygame.draw.rect(canvas, HIGHLIGHT, (27, 23, 10, 8))
        pygame.draw.rect(canvas, (52, 42, 39), (27, 24, 4, 4))
        pygame.draw.rect(canvas, OUTLINE, (24, 24, 3, 4))
        pygame.draw.rect(canvas, OUTLINE, (38, 24, 3, 4))
        pygame.draw.ellipse(canvas, (230, 151, 158), (28, 29, 8, 5))
        pygame.draw.rect(canvas, OUTLINE, (30, 31, 1, 1))
        pygame.draw.rect(canvas, OUTLINE, (34, 31, 1, 1))
        pygame.draw.rect(canvas, BLUEBERRY_DARK, (34, 24, 2, 2))
        pygame.draw.rect(canvas, HIGHLIGHT, (35, 24, 1, 1))
        pygame.draw.rect(canvas, GOLD, (7, 36, 12, 3))
        pygame.draw.rect(canvas, (247, 201, 91), (9, 35, 8, 1))
        return enlarged(canvas)

    raise KeyError(key)


def save_group(
    keys: tuple[str, ...],
    destination: Path,
    maker,
    sheet_name: str,
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    sprites = []
    for key in keys:
        sprite = maker(key)
        pygame.image.save(sprite, destination / f"{key}.png")
        sprites.append(sprite)
    gap = 8
    sheet = pygame.Surface(
        (sum(sprite.get_width() for sprite in sprites) + gap * (len(sprites) - 1),
         max(sprite.get_height() for sprite in sprites)),
        pygame.SRCALPHA,
    )
    x = 0
    for sprite in sprites:
        sheet.blit(sprite, (x, 0))
        x += sprite.get_width() + gap
    pygame.image.save(sheet, destination / sheet_name)


def main() -> None:
    pygame.init()
    save_group(
        ("carp", "crucian_carp", "bass", "turtle"),
        FISH_DIR,
        fish_sprite,
        "fish_sheet.png",
    )
    save_group(
        ("bed", "drawer", "desk", "lantern", "flowerpot"),
        FURNITURE_DIR,
        furniture_sprite,
        "furniture_sheet.png",
    )
    save_group(
        ("beehive", "ice_maker", "cow_barn"),
        FACILITY_DIR,
        facility_sprite,
        "facility_sheet.png",
    )
    pygame.quit()


if __name__ == "__main__":
    main()
