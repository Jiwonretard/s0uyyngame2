"""Review-only profile concepts in the same code-native pixel style as dressup.

This module is not imported by the game. Choose a concept before applying it.
"""
import math
import os
from pathlib import Path
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dressup import CHARACTER_SCALE

INK = (43, 32, 46)
HAIR = (32, 27, 37)
SKIN = (255, 219, 185)
CREAM = (255, 246, 226)
PURPLE = (111, 73, 158)


def profile(variant, phase=0, right=False):
    c = pygame.Surface((96, 120), pygame.SRCALPHA)

    def box(color, x, y, w, h):
        pygame.draw.rect(c, color, (round(x*3), round(y*3), round(w*3), round(h*3)))

    def poly(color, points):
        pygame.draw.polygon(c, color, [(round(x*3), round(y*3)) for x, y in points])

    stride = math.sin(phase)
    # Hair follows the skull and tapers behind the shoulder rather than forming
    # a solid rectangle beside the face. Variants retain long black hair.
    hairline = {
        1: [(9, 10), (11, 7), (20, 6), (24, 9), (25, 13), (25, 28), (23, 31), (17, 30), (16, 17)],
        2: [(7, 11), (9, 7), (18, 6), (23, 8), (25, 12), (25, 27), (23, 31), (16, 30), (16, 18)],
        3: [(8, 10), (10, 7), (21, 6), (25, 10), (26, 15), (25, 29), (23, 31), (17, 30), (16, 17)],
    }[variant]
    poly(INK, hairline)
    poly(HAIR, [(18, 9), (23, 10), (24, 15), (24, 28), (22, 30), (18, 28)])
    box((47, 39, 51), 22, 13, 1, 14)
    # Small forward/backward steps and a sleeve swing around the shoulder.
    for index in (1, 0):
        s = stride * (1 if index == 0 else -1)
        x = 15 + (1 if index else 0) + s*2
        lift = max(0, s)*1.4
        box(SKIN if index == 0 else (224, 183, 156), x, 30, 3, 6-lift)
        box(INK, x-1, 35-lift, 5, 2)
        box((92, 59, 43), x-0.4, 35-lift, 3.7, 1.4)
    box(SKIN, 14, 19, 5, 5)
    poly(INK, [(13, 22), (20, 22), (21, 28), (24, 33), (10, 33), (12, 27)])
    poly(PURPLE, [(14, 23), (19, 23), (20, 29), (22, 32), (12, 32), (13, 27)])
    box((150, 111, 188), 12, 31, 10, 1)
    box(CREAM, 13, 22, 7, 3)
    box(PURPLE, 13, 22, 1.5, 8)
    box((84, 50, 125), 12.5, 27, 2, 2)
    arm_x = 17 - stride*1.1
    box(INK, arm_x-0.7, 23, 4, 8)
    box(CREAM, arm_x, 23, 2.6, 5.5)
    box(SKIN, arm_x, 28.5, 2.6, 1.8)
    if variant == 1:
        poly(SKIN, [(10, 11), (18, 10), (20, 13), (20, 18), (17, 21), (12, 20), (10, 18), (10, 16), (8.5, 16), (10, 14)])
        poly(HAIR, [(9, 11), (10, 9), (18, 8), (21, 11), (20, 18), (18, 15), (18, 11), (14, 12)])
        box(INK, 11, 13, 1.7, 2)
        box(CREAM, 11, 13, 0.6, 0.6)
        box((247, 154, 174), 13, 16, 2.4, 1.6)
        box((197, 87, 109), 10, 18, 2, 0.7)
    elif variant == 2:
        poly(SKIN, [(9, 11), (18, 10), (21, 13), (21, 18), (18, 21), (12, 21), (9, 19), (8, 17), (9, 14)])
        poly(HAIR, [(8, 11), (9, 9), (18, 8), (22, 11), (21, 18), (19, 15), (19, 12), (16, 12), (14, 13), (10, 12)])
        box(INK, 10.5, 14, 2.3, 2.3)
        box(CREAM, 10.7, 14, 0.8, 0.8)
        box((247, 154, 174), 13, 17, 3, 1.8)
        poly((202, 88, 113), [(9.5, 18), (12, 18), (11.5, 19.5), (10, 19.2)])
    else:
        poly(SKIN, [(9, 11), (20, 10), (22, 13), (22, 18), (19, 21), (12, 21), (9, 19)])
        poly(HAIR, [(8, 11), (10, 8), (20, 8), (24, 11), (23, 20), (20, 17), (20, 12), (14, 12)])
        box(INK, 10, 14, 1.5, 1.8)
        box(INK, 16, 13.8, 2.3, 2)
        box(CREAM, 16.2, 13.8, 0.7, 0.7)
        box((247, 154, 174), 18, 16.8, 2.2, 1.6)
        box((247, 154, 174), 9.5, 17, 1.3, 1)
        poly((202, 88, 113), [(11, 18), (16, 18), (15, 20), (12, 20)])
    # Identical whale headband and outfit make the face/silhouette comparison fair.
    poly(INK, [(8, 7), (10, 4), (18, 4), (23, 7), (26, 3), (26, 8), (21, 10), (9, 10)])
    poly((59, 149, 190), [(9, 7), (11, 5), (18, 5), (23, 8), (25, 5), (25, 8), (20, 9), (9, 9)])
    box(CREAM, 10, 8, 10, 1)
    box(CREAM, 11, 6, 1, 1)
    box((160, 222, 228), 16, 2, 1, 2)
    box((160, 222, 228), 14, 2, 5, 0.7)
    return pygame.transform.flip(c, True, False) if right else c


def export():
    pygame.init()
    folder = Path(__file__).resolve().parent / 'side_candidates'
    folder.mkdir(exist_ok=True)
    font_path = next((str(p) for p in (Path('/System/Library/Fonts/AppleSDGothicNeo.ttc'),
        Path('C:/Windows/Fonts/malgun.ttf'), Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')) if p.exists()), None)
    sheet = pygame.Surface((1200, 680))
    sheet.fill((255, 244, 218))
    def label(text, size, center, color=INK):
        rendered = pygame.font.Font(font_path, size).render(text, True, color)
        sheet.blit(rendered, rendered.get_rect(center=center))
    label('블루벨리 · 옆모습 후보 3가지', 30, (600, 40))
    label('같은 머리띠와 의상으로 비교 · 아래 작은 캐릭터는 축소 후 게임 크기', 18, (600, 78))
    titles = ('1  자연스러운 옆얼굴', '2  동글동글 인형형', '3  살짝 돌아본 ¾형')
    details = ('작은 입 · 완만한 턱선 · 슬림한 옆선', '둥근 볼 · 또렷한 눈 · 짧은 턱', '기존 웃는 표정 · 얼굴이 조금 더 보임')
    for i in range(3):
        cx = 200+i*400
        pygame.draw.rect(sheet, (244, 228, 200), (20+i*400, 112, 360, 543), border_radius=16)
        label(titles[i], 24, (cx, 146))
        label(details[i], 16, (cx, 181), (108, 84, 105))
        for right, dx in ((False, -79), (True, 79)):
            sprite = pygame.transform.scale(profile(i+1, right=right), (192, 240))
            sheet.blit(sprite, sprite.get_rect(midbottom=(cx+dx, 446)))
        label('왼쪽 / 오른쪽', 16, (cx, 467))
        for step, phase in enumerate((0, math.pi/2, math.pi*1.5)):
            sprite = profile(i+1, phase)
            sprite = pygame.transform.scale(sprite, (round(96*CHARACTER_SCALE), round(120*CHARACTER_SCALE)))
            sheet.blit(sprite, sprite.get_rect(midbottom=(cx-92+step*92, 595)))
        label('서 있기 / 걸음 1 / 걸음 2', 16, (cx, 622))
        atlas = pygame.Surface((96*12, 120*2), pygame.SRCALPHA)
        for row in range(2):
            for col in range(12):
                atlas.blit(profile(i+1, col*math.tau/12, bool(row)), (col*96,row*120))
        pygame.image.save(atlas, folder/f'candidate_{i+1}_walk.png')
    pygame.image.save(sheet, folder/'side_candidates.png')
    pygame.quit()


if __name__ == '__main__':
    export()
