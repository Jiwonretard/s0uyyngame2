"""Export the same code-native pixel layers used by the live wardrobe."""
from pathlib import Path
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dressup import build_frames, build_walk_frames, product_surface
from wardrobe_catalog import DEFAULT_LOOK, OUTFITS, OPTIONS, CATEGORIES, THEME_SETS, cosmetic_price, option_label


def export():
    pygame.init()
    folder = Path(__file__).resolve().parent / "wardrobe"
    folder.mkdir(exist_ok=True)
    font_path = next((str(path) for path in (
        Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    ) if path.exists()), None)
    font = pygame.font.Font(font_path, 20)
    title = pygame.font.Font(font_path, 30)
    for category, options in OPTIONS.items():
        sheet = pygame.Surface((960, 80 + 220 * ((len(options) + 3) // 4)))
        sheet.fill((255, 242, 214))
        sheet.blit(title.render("블루벨리 옷장 · " + CATEGORIES[category], True, (68, 44, 78)), (30, 20))
        for i, key in enumerate(options):
            look = {**DEFAULT_LOOK, category: key}
            if category == "outfit":
                look.update(THEME_SETS.get(key, {}))
            sprite = product_surface(category, key, scale=4)
            center = (120 + (i % 4) * 240, 165 + (i // 4) * 220)
            sheet.blit(sprite, sprite.get_rect(center=center))
            label = font.render(option_label(category, key), True, (68, 44, 78))
            sheet.blit(label, label.get_rect(center=(center[0], center[1] + 94)))
            price = cosmetic_price(category, key)
            price_label = "기본 보유" if price == 0 else f"{price:,}벨리"
            price_text = font.render(price_label, True, (103, 73, 156))
            sheet.blit(price_text, price_text.get_rect(center=(center[0], center[1] + 119)))
            if category == "outfit":
                frames = build_frames(look)
                atlas = pygame.Surface((288, 480), pygame.SRCALPHA)
                for row, direction in enumerate(("down", "left", "right", "up")):
                    for col, frame in enumerate(frames[direction]):
                        atlas.blit(frame, (col * 96, row * 120))
                pygame.image.save(atlas, folder / f"outfit_{key}.png")
                walking = build_walk_frames(look)
                frame_w, frame_h = walking["down"][0].get_size()
                gait = pygame.Surface((12 * frame_w, 4 * frame_h), pygame.SRCALPHA)
                for row, direction in enumerate(("down", "left", "right", "up")):
                    for col, frame in enumerate(walking[direction]):
                        gait.blit(frame, (col * frame_w, row * frame_h))
                pygame.image.save(gait, folder / f"walk_{key}.png")
        pygame.image.save(sheet, folder / f"catalogue_{category}.png")
    pygame.quit()


if __name__ == "__main__":
    export()
