"""Regenerate the original fish and furniture pixel-art PNG assets."""

from __future__ import annotations

from pathlib import Path

import pygame


ASSET_DIR = Path(__file__).resolve().parent
FISH_DIR = ASSET_DIR / "fish"
FURNITURE_DIR = ASSET_DIR / "furniture"
OUTLINE = (77, 47, 38)
HIGHLIGHT = (255, 239, 190)
BLUEBERRY = (76, 67, 164)
BLUEBERRY_DARK = (40, 35, 91)
GREEN = (54, 119, 61)
GREEN_DARK = (35, 82, 45)
LEAF = (64, 138, 64)
GOLD = (236, 167, 48)
WATER_LIGHT = (126, 199, 197)


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
    pygame.quit()


if __name__ == "__main__":
    main()
