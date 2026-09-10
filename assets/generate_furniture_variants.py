"""Draw the farmhouse collection using the game's existing code-native pixel style.

Run this file to regenerate only furniture PNGs and the labelled catalogue.
Plant silhouettes use botanical references listed in furniture/README.md.
"""
from pathlib import Path
import math
import sys

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from furniture_catalog import FURNITURE_CATEGORIES, FURNITURE_LABELS, FURNITURE_COSTS
from generate_pixel_assets import furniture_sprite, enlarged, FURNITURE_DIR

INK = (77, 47, 38)
CREAM = (255, 241, 206)
WOOD = (172, 108, 64)
HONEY = (223, 164, 92)
GOLD = (235, 183, 81)
PURPLE = (103, 73, 156)
LILAC = (172, 140, 202)
PINK = (210, 115, 127)
ROSE = (243, 175, 172)
SAGE = (115, 157, 118)
GREEN = (55, 114, 73)
DARK_GREEN = (37, 77, 59)
MINT = (176, 206, 153)
SKY = (127, 185, 195)
NAVY = (55, 61, 99)


def variant_sprite(key: str) -> pygame.Surface:
    c = pygame.Surface((48, 40), pygame.SRCALPHA)

    def box(x, y, w, h, fill, edge=INK):
        pygame.draw.rect(c, edge, (x, y, w, h))
        if w > 2 and h > 2:
            pygame.draw.rect(c, fill, (x + 1, y + 1, w - 2, h - 2))

    def poly(points, fill, edge=INK):
        pygame.draw.polygon(c, fill, points)
        pygame.draw.polygon(c, edge, points, 1)

    def line(start, end, color=INK, width=1):
        pygame.draw.line(c, color, start, end, width)

    def dot(x, y, color, size=2):
        pygame.draw.rect(c, color, (x, y, size, size))

    def flower(x, y, color=CREAM):
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            dot(x + dx, y + dy, color)
        dot(x, y, GOLD)

    def pot(fill, rim, wide=False):
        left, right = (10, 38) if wide else (15, 33)
        poly([(left, 27), (right, 27), (right - 3, 37), (left + 3, 37)], fill)
        box(left - 1, 25, right - left + 3, 4, rim)
        line((left + 4, 30), (left + 5, 34), CREAM, 2)

    if key == "wardrobe":
        poly([(8, 37), (8, 7), (12, 3), (36, 3), (40, 7), (40, 37)], HONEY)
        box(10, 8, 14, 26, PURPLE)
        box(24, 8, 14, 26, CREAM)
        box(26, 10, 10, 19, SKY)
        line((28, 12), (34, 18), CREAM, 2)
        line((28, 16), (31, 19), CREAM)
        box(21, 22, 2, 4, GOLD, GOLD)
        box(25, 22, 2, 4, GOLD, GOLD)
        line((13, 13), (21, 13), HONEY)
        poly([(14, 18), (17, 15), (20, 18)], LILAC)
        box(13, 18, 9, 11, LILAC)
        for x in (9, 35):
            box(x, 37, 4, 3, WOOD)
        flower(23, 5, LILAC)
    elif key.startswith("bed_"):
        frame = CREAM if key == "bed_cloud" else HONEY
        box(5, 13, 38, 21, frame)
        box(7, 33, 4, 5, WOOD)
        box(37, 33, 4, 5, WOOD)
        box(7, 15, 34, 15, CREAM)
        box(8, 16, 9, 12, (255, 249, 225))
        dot(9, 17, CREAM, 3)
        if key == "bed_gingham":
            box(18, 15, 23, 17, ROSE)
            for y in range(16, 31, 4):
                for x in range(19, 40, 4):
                    if (x // 4 + y // 4) % 2:
                        pygame.draw.rect(c, CREAM, (x, y, 3, 3))
            box(3, 8, 4, 27, HONEY)
            box(41, 12, 4, 23, HONEY)
            dot(3, 6, GOLD, 4)
            flower(28, 23, PINK)
        elif key == "bed_quilt":
            box(18, 15, 23, 17, SAGE)
            for y in (17, 24):
                for x in (20, 27, 34):
                    box(x, y, 6, 6, CREAM if (x + y) % 2 else LILAC, HONEY)
                    dot(x + 2, y + 2, PINK)
            poly([(3, 32), (3, 10), (5, 7), (8, 7), (9, 10), (9, 14), (6, 14), (6, 32)], HONEY)
            line((11, 32), (39, 32), CREAM)
        elif key == "bed_cloud":
            poly([(3, 27), (3, 14), (5, 14), (5, 10), (8, 8), (12, 8),
                  (14, 11), (17, 11), (19, 15), (19, 28)], CREAM)
            box(18, 15, 23, 17, SKY)
            for x, y in ((23, 19), (32, 26)):
                poly([(x - 2, y + 3), (x - 2, y), (x, y), (x, y - 2),
                      (x + 3, y - 2), (x + 4, y), (x + 6, y), (x + 6, y + 3)], CREAM, CREAM)
            box(8, 18, 8, 10, (255, 251, 233))
        else:
            box(18, 15, 23, 17, PURPLE)
            line((19, 17), (39, 17), LILAC, 2)
            for x, y in ((24, 23), (34, 28)):
                line((x - 2, y), (x + 2, y), GOLD)
                line((x, y - 2), (x, y + 2), GOLD)
            box(3, 4, 3, 32, HONEY)
            box(42, 4, 3, 32, HONEY)
            poly([(2, 7), (5, 2), (42, 2), (46, 7)], PURPLE)
            line((5, 4), (42, 4), LILAC)
            poly([(6, 8), (14, 8), (11, 16), (9, 27), (6, 27)], ROSE)
            poly([(34, 8), (41, 8), (41, 27), (38, 27), (36, 16)], ROSE)
            line((6, 20), (10, 20), GOLD, 2)
            line((38, 20), (41, 20), GOLD, 2)

    elif key.startswith("drawer_"):
        if key == "drawer_white":
            box(10, 6, 28, 28, (223, 211, 186))
            box(8, 4, 32, 4, CREAM)
            for y in (10, 18, 26):
                box(13, y, 22, 6, CREAM)
                box(22, y + 2, 4, 2, GOLD, GOLD)
            for x in (12, 32):
                box(x, 34, 4, 4, HONEY)
        elif key == "drawer_wicker":
            box(6, 10, 36, 24, WOOD)
            box(5, 7, 38, 4, HONEY)
            for y in (13, 23):
                box(9, y, 30, 8, HONEY)
                for x in range(11, 37, 4):
                    line((x, y + 1), (x, y + 6), WOOD)
                line((10, y + 4), (37, y + 4), CREAM)
                box(21, y + 2, 6, 3, INK)
            dot(8, 34, INK, 3)
            dot(37, 34, INK, 3)
        elif key == "drawer_apothecary":
            box(6, 4, 36, 32, WOOD)
            box(4, 3, 40, 4, HONEY)
            for y in (9, 17, 25):
                for x in (9, 19, 29):
                    box(x, y, 9, 7, HONEY)
                    dot(x + 3, y + 2, CREAM, 3)
                    dot(x + 4, y + 5, INK, 1)
            box(5, 35, 38, 3, HONEY)
        else:
            poly([(11, 36), (11, 8), (16, 3), (32, 3), (37, 8), (37, 36)], NAVY)
            for y in (12, 20, 28):
                box(14, y, 20, 7, PURPLE)
                box(22, y + 3, 4, 2, GOLD, GOLD)
            pygame.draw.circle(c, GOLD, (24, 8), 3)
            pygame.draw.circle(c, NAVY, (26, 7), 3)
            dot(15, 8, CREAM, 1)
            dot(32, 9, CREAM, 1)
            for x in (12, 33):
                box(x, 36, 3, 3, GOLD)

    elif key.startswith("desk_"):
        if key == "desk_round":
            box(21, 22, 6, 12, WOOD)
            poly([(14, 37), (20, 32), (27, 32), (34, 37)], HONEY)
            pygame.draw.ellipse(c, INK, (5, 8, 38, 21))
            pygame.draw.ellipse(c, HONEY, (6, 9, 36, 17))
            pygame.draw.arc(c, CREAM, (9, 11, 30, 13), 0.4, 2.8, 1)
            box(15, 13, 16, 9, PURPLE)
            box(16, 13, 7, 7, CREAM)
            box(24, 13, 6, 7, CREAM)
            line((18, 16), (21, 16), WOOD)
            box(34, 15, 4, 4, CREAM)
        else:
            for x in (6, 38):
                box(x, 23, 4, 14, WOOD)
            if key == "desk_studio":
                line((8, 35), (39, 26), HONEY, 2)
                poly([(3, 13), (41, 8), (45, 25), (5, 29)], WOOD)
                poly([(5, 13), (40, 10), (42, 22), (7, 26)], HONEY)
                poly([(12, 14), (31, 12), (34, 22), (15, 24)], CREAM)
                line((18, 21), (23, 16), SAGE, 2)
                flower(25, 17, LILAC)
                box(34, 19, 7, 5, PURPLE)
                for x, color in ((35, PINK), (38, SKY)):
                    line((x, 20), (x - 1, 12), INK)
                    dot(x - 2, 11, color)
            else:
                box(3, 14, 42, 13, HONEY)
                box(5, 16, 38, 8, WOOD)
                line((6, 17), (41, 17), HONEY)
                if key == "desk_writing":
                    box(30, 27, 11, 9, HONEY)
                    dot(34, 30, GOLD)
                    box(9, 10, 16, 10, CREAM)
                    for y in (12, 15, 18):
                        line((12, y), (20, y), WOOD)
                    box(31, 14, 6, 6, NAVY)
                    line((34, 16), (39, 7), INK)
                    poly([(36, 12), (36, 7), (40, 4), (40, 9)], CREAM)
                else:
                    box(4, 4, 40, 5, WOOD)
                    for x in (6, 40):
                        line((x, 7), (x, 15), WOOD, 2)
                    for x, fill in ((10, SKY), (19, SAGE), (29, LILAC)):
                        box(x, 1, 5, 6, fill)
                        line((x + 1, 1), (x + 3, 1), GOLD)
                    box(10, 12, 17, 11, CREAM)
                    line((18, 14), (18, 21), GREEN)
                    poly([(18, 17), (13, 14), (14, 18), (18, 19)], SAGE, GREEN)
                    box(32, 17, 7, 6, HONEY)
                    line((35, 17), (35, 10), GREEN, 2)
                    flower(35, 10, ROSE)

    elif key.startswith("lantern_"):
        if key == "lantern_camping":
            pygame.draw.arc(c, INK, (14, 2, 20, 20), 0, math.pi, 2)
            box(13, 14, 22, 20, GREEN)
            box(17, 15, 14, 15, GOLD)
            box(20, 16, 8, 13, CREAM, GOLD)
            poly([(11, 15), (15, 10), (33, 10), (37, 15)], SAGE)
            box(11, 32, 26, 5, GREEN)
            dot(22, 34, GOLD, 3)
        elif key == "lantern_paper":
            line((24, 2), (24, 6), INK, 2)
            poly([(17, 6), (31, 6), (37, 13), (37, 26), (31, 31),
                  (17, 31), (11, 26), (11, 13)], CREAM)
            for y in (11, 16, 21, 26):
                line((13, y), (35, y), HONEY)
            line((18, 7), (18, 29), GOLD)
            line((30, 7), (30, 29), GOLD)
            box(16, 30, 16, 4, WOOD)
            line((24, 34), (24, 38), PINK, 2)
            dot(22, 37, PINK, 4)
        elif key == "lantern_star":
            line((24, 1), (24, 7), GOLD, 2)
            points = [(24, 5), (29, 15), (41, 17), (32, 25), (34, 37),
                      (24, 31), (14, 37), (16, 25), (7, 17), (19, 15)]
            poly(points, GOLD)
            poly([(24, 10), (27, 18), (35, 19), (29, 24), (30, 31),
                  (24, 27), (18, 31), (19, 24), (13, 19), (21, 18)], CREAM, HONEY)
            for point in ((24, 10), (35, 19), (30, 31), (18, 31), (13, 19)):
                line((24, 22), point, HONEY)
        else:
            box(17, 21, 14, 14, CREAM)
            line((20, 25), (20, 31), GOLD, 2)
            poly([(9, 37), (12, 33), (36, 33), (39, 37)], SAGE)
            poly([(5, 22), (7, 14), (12, 8), (20, 5), (28, 5),
                  (36, 8), (41, 14), (43, 22)], PINK)
            line((7, 22), (41, 22), GOLD, 2)
            for x, y, size in ((13, 13, 5), (24, 8, 4), (30, 15, 6), (8, 19, 3)):
                dot(x, y, CREAM, size)

    elif key == "plant_monstera":
        for x, y in ((13, 12), (31, 6), (36, 17)):
            line((24, 27), (x, y + 5), DARK_GREEN, 2)
        # Split, asymmetric heart-shaped leaves with cut margins.
        for x, y, fill in ((7, 7, GREEN), (25, 2, SAGE), (30, 13, GREEN)):
            poly([(x, y + 3), (x + 3, y), (x + 7, y + 2), (x + 11, y),
                  (x + 15, y + 3), (x + 14, y + 8), (x + 7, y + 14), (x + 1, y + 8)], fill, DARK_GREEN)
            line((x + 7, y + 3), (x + 7, y + 12), MINT)
            for dy in (5, 8):
                poly([(x, y + dy), (x + 5, y + dy + 2), (x, y + dy + 2)], (0, 0, 0, 0), (0, 0, 0, 0))
                poly([(x + 15, y + dy), (x + 10, y + dy + 2), (x + 15, y + dy + 2)], (0, 0, 0, 0), (0, 0, 0, 0))
        pot(CREAM, HONEY)
        line((21, 33), (28, 33), SAGE, 2)
    elif key == "plant_snake":
        # Upright sword leaves, yellow edges and dark horizontal bands.
        for x, y, lean in ((17, 7, -4), (24, 2, 0), (29, 6, 5), (20, 13, -2)):
            poly([(x - 2, 27), (x - 3 + lean, y + 6), (x + lean, y),
                  (x + 3 + lean, y + 6), (x + 3, 27)], GOLD, DARK_GREEN)
            line((x, 26), (x + lean, y + 5), GREEN, 3)
            for dy in range(y + 7, 25, 5):
                dot(x + round(lean * (27 - dy) / 25) - 1, dy, MINT, 2)
        pot((194, 118, 86), HONEY)
    elif key == "plant_echeveria":
        pot((170, 128, 182), LILAC, wide=True)
        # Concentric rosette of thick, pointed blue-green succulent leaves.
        for radius, length, count, fill in ((8, 9, 8, SAGE), (4, 7, 6, MINT)):
            for i in range(count):
                a = i * math.tau / count
                x, y = 24 + round(math.cos(a) * radius), 20 + round(math.sin(a) * radius * .65)
                tip = (24 + round(math.cos(a) * (radius + length)),
                       20 + round(math.sin(a) * (radius + length) * .65))
                tangent = (-math.sin(a) * 4, math.cos(a) * 3)
                poly([(24, 20), (round(x + tangent[0]), round(y + tangent[1])), tip,
                      (round(x - tangent[0]), round(y - tangent[1]))], fill, GREEN)
                dot(tip[0], tip[1], ROSE, 1)
        dot(23, 19, CREAM, 3)
    elif key == "plant_lavender":
        for x, y in ((12, 9), (18, 4), (25, 2), (31, 6), (36, 11)):
            line((24, 28), (x, y + 3), SAGE, 1)
            for dy in (0, 3, 6):
                box(x - 2, y + dy, 4, 4, LILAC, PURPLE)
                dot(x - 1, y + dy, ROSE, 1)
        for x in (12, 17, 28, 34):
            poly([(24, 28), (x, 19), (x + 2, 25)], SAGE, GREEN)
        pot((151, 183, 185), CREAM)
        box(22, 30, 6, 4, LILAC)
    else:
        return furniture_sprite(key)
    return enlarged(c)


def save_furniture_catalog() -> None:
    pygame.font.init()
    FURNITURE_DIR.mkdir(parents=True, exist_ok=True)
    font_path = next((path for path in (
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "C:/Windows/Fonts/malgun.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ) if Path(path).exists()), None)
    label_font = pygame.font.Font(font_path, 18)
    title_font = pygame.font.Font(font_path, 26)
    sheet = pygame.Surface((1200, 70 + 218 * len(FURNITURE_CATEGORIES)))
    sheet.fill((242, 228, 201))
    sheet.blit(title_font.render(f"블루벨리 · 농장집 가구 {len(FURNITURE_COSTS)}종", True, INK), (30, 18))
    for row, keys in enumerate(FURNITURE_CATEGORIES.values()):
        for column, key in enumerate(keys):
            sprite = variant_sprite(key)
            pygame.image.save(sprite, FURNITURE_DIR / f"{key}.png")
            card = pygame.Rect(16 + column * 238, 62 + row * 218, 228, 208)
            pygame.draw.rect(sheet, (255, 248, 228), card)
            pygame.draw.rect(sheet, (204, 177, 138), card, 2)
            cropped = sprite.subsurface(sprite.get_bounding_rect())
            fitted = pygame.transform.scale(cropped, (
                round(cropped.get_width() * min(184 / cropped.get_width(), 144 / cropped.get_height())),
                round(cropped.get_height() * min(184 / cropped.get_width(), 144 / cropped.get_height())),
            ))
            sheet.blit(fitted, fitted.get_rect(center=(card.centerx, card.y + 80)))
            for y, label in ((164, FURNITURE_LABELS[key]), (187, f"{FURNITURE_COSTS[key]:,} 벨리")):
                rendered = label_font.render(label, True, INK)
                sheet.blit(rendered, rendered.get_rect(center=(card.centerx, card.y + y)))
    pygame.image.save(sheet, FURNITURE_DIR / "furniture_sheet.png")


if __name__ == "__main__":
    save_furniture_catalog()
