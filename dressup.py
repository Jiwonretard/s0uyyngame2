"""Code-native pixel layers for clothes, hair and accessories in four directions.

Compose only when a look changes, then reuse its walking frames during play.
The original photo-derived character remains available through reset.
"""
import pygame
from wardrobe_catalog import DEFAULT_LOOK, OUTFITS, SHOES, HAIR_COLORS, SOCKS

INK = (48, 34, 43)
SKIN = (255, 218, 182)
WHITE = (255, 248, 231)


def character_surface(appearance, direction="down", step=0, scale=3):
    look = {**DEFAULT_LOOK, **appearance}
    _, cloth, trim, style = OUTFITS[look["outfit"]]
    hair = HAIR_COLORS[look["hair"]][1]
    shoe = SHOES[look["shoes"]][1]
    sock = SOCKS[look["socks"]][1]
    c = pygame.Surface((32, 40), pygame.SRCALPHA)

    def rect(color, x, y, w, h):
        pygame.draw.rect(c, color, (x, y, w, h))

    def poly(color, points):
        pygame.draw.polygon(c, color, points)

    def framed(color, x, y, w, h):
        rect(INK, x, y, w, h)
        rect(color, x + 1, y + 1, w - 2, h - 2)

    def berry(x, y):
        rect((48, 38, 99), x, y, 3, 3)
        rect((135, 110, 206), x, y, 1, 1)

    side = direction in ("left", "right")
    back = direction == "up"
    swing = (0, -2, 2)[step]
    # Back hair is beneath the body; front hair is applied again for rear views.
    poly(INK, [(7, 6), (11, 4), (22, 4), (26, 9), (26, 29), (22, 32), (6, 30), (6, 10)])
    rect(hair, 7, 9, 18, 21)
    # Both legs and footwear are part of every animation frame.
    for i, x in enumerate((12, 19) if not side else (13 - swing, 18 + swing)):
        lift = (swing if i == 0 else -swing) if not side else (-1 if i == (step % 2) and step else 0)
        leg_y = 30 + lift
        rect(SKIN, x, leg_y, 4, 7)
        if sock:
            sock_height = 6 if look["socks"] == "navy" else 4
            rect(sock, x, leg_y + 7 - sock_height, 4, sock_height)
            if look["socks"] in ("blueberry", "whale"):
                rect(cloth, x, leg_y + 4, 4, 1)
            if look["socks"] == "lace":
                rect(WHITE, x - 1, leg_y + 3, 6, 1)
        if style in ("overalls", "pajamas"):
            rect(cloth, x, leg_y, 4, 5)
        shoe_h = 5 if look["shoes"] == "boots" else 2
        rect(INK, x - (1 if side else 0), leg_y + 7 - shoe_h, 5, shoe_h + 1)
        rect(shoe, x, leg_y + 7 - shoe_h, 4, shoe_h)
        if look["shoes"] in ("white", "whale"):
            rect(WHITE, x, leg_y + 7, 4, 1)
    # Body, neck and silhouette distinguish dresses, shorts, coats and trousers.
    rect(SKIN, 13, 19, 8, 4)
    if style in ("shorts", "overalls", "pajamas", "sailor"):
        framed(cloth, 10, 23, 13, 10)
        rect(INK, 16, 30, 1, 3)
    else:
        poly(INK, [(11, 22), (22, 22), (23, 28), (26, 33), (8, 33), (10, 28)])
        poly(cloth, [(12, 23), (21, 23), (22, 29), (24, 32), (10, 32), (12, 28)])
    if style == "party":
        rect(trim, 9, 31, 16, 2)
        poly(trim, [(12, 27), (16, 28), (12, 30)])
        poly(trim, [(21, 27), (17, 28), (21, 30)])
    if style in ("dress", "shorts", "overalls"):
        rect(trim, 12, 22, 9, 3)
        for x in (12, 20):
            rect(cloth, x, 22, 1, 5)
        framed(trim, 14, 27, 5, 3)
    if style == "berry":
        poly((103, 161, 80), [(11, 22), (16, 23), (13, 25)])
        poly((143, 190, 112), [(22, 22), (17, 23), (20, 25)])
        for x, y in ((12, 29), (19, 27), (18, 31)):
            berry(x, y)
    elif style == "sailor":
        rect(trim, 11, 22, 11, 4)
        poly((35, 72, 127), [(11, 22), (16, 26), (22, 22), (20, 27), (13, 27)])
        rect(trim, 11, 30, 12, 1)
        poly(trim, [(15, 28), (19, 28), (20, 29), (22, 27), (22, 30), (16, 30)])
        rect(INK, 16, 28, 1, 1)
    elif style == "check":
        for y in (25, 29):
            for x in (12, 16, 20):
                rect(trim, x, y, 2, 2)
    elif style == "apron":
        rect(trim, 13, 24, 8, 8)
        rect((233, 177, 48), 15, 27, 4, 3)
        rect(INK, 17, 27, 1, 3)
        rect(WHITE, 14, 26, 2, 1)
        rect(WHITE, 19, 26, 2, 1)
    elif style in ("cardigan", "coat", "blouse"):
        rect(trim, 15, 23, 4, 7)
        rect(cloth, 16, 24, 1, 8)
        for y in (25, 28, 30):
            rect((240, 193, 93), 17, y, 1, 1)
        if style == "coat":
            poly(trim, [(11, 23), (15, 26), (13, 27)])
            rect(trim, 20, 29, 3, 1)
        if style == "blouse":
            rect(trim, 10, 29, 14, 3)
    elif style == "pajamas":
        for x, y in ((12, 25), (19, 28)):
            rect(trim, x, y, 4, 2)
            rect(trim, x + 1, y - 1, 2, 1)
    # Sleeves and hands swing independently in side views.
    for x in ((9,) if side else (8, 23)):
        arm_y = 23 + (swing // 2 if side else 0)
        rect(INK, x - 1, arm_y, 5, 9)
        rect(trim, x, arm_y, 3, 6)
        rect(SKIN, x, arm_y + 6, 3, 2)
    if back:
        rect(hair, 8, 7, 17, 23)
        poly(hair, [(8, 26), (25, 26), (23, 32), (10, 31)])
        rect(tuple(min(255, v + 15) for v in hair), 10, 10, 2, 15)
    else:
        # Keep the familiar big smile, blush and long straight hair.
        face_x, face_w = (8, 13) if side else (8, 17)
        rect(SKIN, face_x, 10, face_w, 11)
        rect(SKIN, 7 if side else 24, 14, 2, 4)
        rect(hair, 7, 7, 18, 4)
        rect(hair, 7, 10, 2, 3)
        if side:
            rect(hair, 21, 11, 4, 18)
            rect(INK, 10, 13, 3, 2)
            rect((205, 83, 110), 8, 17, 4, 3)
            rect((248, 144, 167), 16, 16, 2, 2)
        else:
            for x in (11, 20):
                rect(INK, x, 13, 3, 2)
            rect((205, 83, 110), 13, 17, 7, 3)
            for x in (9, 23):
                rect((248, 144, 167), x, 16, 2, 2)
    # Accessories sit above the same hairline in all poses.
    band = look["headband"]
    if band != "none":
        rect((104, 77, 103), 8, 7, 16, 1)
    if band in ("shark", "whale"):
        color = (51, 101, 161) if band == "shark" else (60, 151, 199)
        poly(INK, [(7, 5), (9, 2), (18, 2), (23, 5), (26, 1), (27, 6), (22, 8), (8, 8)])
        poly(color, [(8, 5), (10, 3), (18, 3), (23, 6), (26, 3), (26, 6), (21, 7), (8, 7)])
        rect(WHITE, 9, 7, 12, 1)
        rect(WHITE, 10, 4, 2, 2)
        rect(INK, 10, 4, 1, 1)
        if band == "shark":
            poly(color, [(15, 3), (18, 0), (19, 4)])
        else:
            rect((171, 229, 239), 16, 0, 1, 2)
            rect((171, 229, 239), 14, 0, 5, 1)
    elif band == "blueberry":
        for x, y in ((12, 3), (17, 2), (15, 5)):
            berry(x, y)
        poly((106, 160, 83), [(17, 3), (20, 0), (22, 1), (19, 4)])
    elif band == "ribbon":
        poly((220, 134, 171), [(10, 2), (16, 4), (10, 7)])
        poly((244, 171, 192), [(22, 2), (16, 4), (22, 7)])
        rect(WHITE, 15, 4, 3, 2)
    elif band == "flowers":
        for x in (9, 15, 21):
            rect((137, 179, 98), x - 1, 5, 6, 2)
            rect(WHITE, x, 3, 4, 3)
            rect((238, 187, 86), x + 1, 4, 2, 1)
    elif band == "star":
        poly((243, 198, 88), [(19, 0), (21, 3), (25, 3), (22, 5), (23, 8), (19, 6), (16, 8), (17, 4), (15, 3), (18, 3)])
    if direction == "right":
        c = pygame.transform.flip(c, True, False)
    # Side poses face left before mirroring. 3x nearest-neighbour keeps pixels crisp.
    return pygame.transform.scale(c, (32 * scale, 40 * scale))


def build_frames(appearance):
    return {direction: [character_surface(appearance, direction, step) for step in range(3)]
            for direction in ("down", "left", "right", "up")}
