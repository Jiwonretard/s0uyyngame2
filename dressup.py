"""Code-native pixel layers for clothes, hair and accessories in four directions.

Compose only when a look changes, then reuse its walking frames during play.
The original photo-derived character remains available through reset.
"""
import pygame
from wardrobe_catalog import DEFAULT_LOOK, HEADBANDS, OUTFITS, SHOES, HAIR_COLORS, SOCKS

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


def product_surface(category, key, scale=2):
    """Draw a shop product without a character/mannequin behind it."""
    c = pygame.Surface((48, 40), pygame.SRCALPHA)

    def rect(color, x, y, w, h):
        pygame.draw.rect(c, color, (x, y, w, h))

    def line(color, start, end, width=1):
        pygame.draw.line(c, color, start, end, width)

    def poly(color, points):
        pygame.draw.polygon(c, color, points)

    def framed(color, x, y, w, h):
        rect(INK, x, y, w, h)
        if w > 2 and h > 2:
            rect(color, x + 1, y + 1, w - 2, h - 2)

    def berry(x, y):
        rect((48, 38, 99), x, y, 5, 5)
        rect((145, 119, 215), x + 1, y + 1, 2, 2)

    if category == "outfit":
        _label, cloth, trim, style = OUTFITS[key]
        # Wooden hanger and a floating garment: there is deliberately no body.
        line((151, 103, 71), (24, 3), (24, 7), 2)
        pygame.draw.arc(c, (151, 103, 71), (21, 1, 7, 7), 0.1, 3.8, 2)
        line((151, 103, 71), (24, 7), (9, 13), 2)
        line((151, 103, 71), (24, 7), (39, 13), 2)
        poly(INK, [(14, 10), (21, 9), (24, 13), (27, 9), (34, 10), (41, 19),
                   (35, 23), (33, 18), (34, 35), (14, 35), (15, 18), (13, 23), (7, 19)])
        poly(trim, [(15, 11), (21, 10), (24, 14), (27, 10), (33, 11), (39, 19),
                    (35, 21), (32, 16), (33, 34), (15, 34), (16, 16), (13, 21), (9, 19)])
        if style in ("shorts", "overalls", "pajamas", "sailor"):
            rect(cloth, 16, 18, 16, 13)
            rect(INK, 23, 29, 2, 6)
        else:
            poly(cloth, [(16, 17), (32, 17), (32, 25), (36, 34), (12, 34), (16, 25)])
        if style in ("dress", "shorts", "overalls"):
            rect(trim, 17, 15, 14, 4)
            rect(cloth, 18, 12, 3, 10)
            rect(cloth, 27, 12, 3, 10)
            framed(trim, 20, 24, 8, 6)
        elif style == "berry":
            poly((104, 159, 82), [(16, 17), (23, 19), (18, 22)])
            poly((142, 190, 111), [(32, 17), (25, 19), (30, 22)])
            for x, y in ((16, 26), (23, 22), (28, 28)):
                berry(x, y)
        elif style == "sailor":
            poly((35, 72, 127), [(16, 14), (24, 21), (32, 14), (29, 23), (19, 23)])
            rect(trim, 16, 30, 16, 2)
            poly(trim, [(21, 24), (27, 24), (30, 28), (27, 30), (24, 27), (21, 30), (18, 28)])
        elif style == "check":
            for y in (21, 27, 32):
                for x in (15, 21, 27, 33):
                    rect(trim, x, y, 3, 3)
        elif style == "apron":
            framed(trim, 18, 18, 12, 16)
            rect((233, 177, 48), 21, 24, 7, 6)
            rect(WHITE, 20, 22, 3, 2)
            rect(WHITE, 27, 22, 3, 2)
        elif style in ("cardigan", "coat", "blouse"):
            rect(trim, 21, 14, 7, 18)
            rect(cloth, 23, 16, 2, 18)
            for y in (19, 24, 29):
                rect((240, 193, 93), 26, y, 2, 2)
            if style == "coat":
                poly(trim, [(16, 15), (23, 21), (19, 23)])
                poly(trim, [(32, 15), (25, 21), (29, 23)])
            elif style == "blouse":
                rect(trim, 15, 29, 18, 5)
        elif style == "pajamas":
            for x, y in ((17, 20), (26, 26)):
                rect(trim, x, y, 5, 3)
                rect(trim, x + 1, y - 1, 3, 1)
        elif style == "party":
            rect(trim, 13, 31, 22, 3)
            poly(trim, [(16, 24), (23, 27), (16, 30)])
            poly(trim, [(32, 24), (25, 27), (32, 30)])

    elif category == "headband":
        if key == "none":
            pygame.draw.arc(c, (165, 145, 158), (8, 10, 32, 22), 0.1, 3.05, 4)
            line((202, 92, 111), (11, 31), (38, 7), 4)
        elif key in ("shark", "whale"):
            color = (51, 101, 161) if key == "shark" else (60, 151, 199)
            poly(INK, [(6, 23), (10, 12), (28, 10), (36, 18), (43, 8), (44, 24), (34, 29), (10, 29)])
            poly(color, [(9, 22), (12, 14), (28, 13), (36, 21), (41, 14), (41, 22), (33, 26), (10, 26)])
            rect(WHITE, 11, 25, 22, 3)
            rect(WHITE, 14, 17, 4, 4)
            rect(INK, 15, 17, 2, 2)
            if key == "shark":
                poly(color, [(22, 13), (28, 4), (30, 15)])
            else:
                rect((171, 229, 239), 24, 5, 2, 7)
                line((171, 229, 239), (18, 5), (31, 5), 2)
        else:
            pygame.draw.arc(c, (104, 77, 103), (8, 12, 32, 20), 0.05, 3.1, 4)
            if key == "blueberry":
                for x, y in ((16, 11), (23, 8), (27, 13)):
                    berry(x, y)
                poly((106, 160, 83), [(25, 10), (31, 4), (35, 7), (29, 12)])
            elif key == "ribbon":
                poly((220, 134, 171), [(13, 8), (24, 14), (12, 21)])
                poly((244, 171, 192), [(35, 8), (24, 14), (36, 21)])
                rect(WHITE, 21, 12, 6, 5)
            elif key == "flowers":
                for x, color in ((14, (245, 187, 194)), (24, WHITE), (34, (194, 174, 225))):
                    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                        rect(color, x + dx, 13 + dy, 4, 4)
                    rect((238, 187, 86), x, 13, 3, 3)
            elif key == "star":
                poly((243, 198, 88), [(24, 5), (27, 11), (35, 11), (29, 16),
                                      (31, 24), (24, 19), (17, 24), (19, 16), (13, 11), (21, 11)])

    elif category == "shoes":
        color = SHOES[key][1]
        boots = key == "boots"
        for x in (7, 26):
            if boots:
                framed(color, x + 3, 8, 11, 22)
                framed(color, x, 26, 16, 9)
            else:
                poly(INK, [(x + 2, 20), (x + 12, 20), (x + 14, 26), (x + 17, 29),
                           (x + 16, 34), (x, 34), (x, 27)])
                poly(color, [(x + 3, 22), (x + 11, 22), (x + 12, 27), (x + 15, 29),
                             (x + 14, 32), (x + 2, 32), (x + 2, 28)])
                if key in ("white", "whale"):
                    rect(WHITE, x + 2, 30, 13, 3)
                if key == "blueberry":
                    berry(x + 5, 23)
                elif key == "whale":
                    line((205, 241, 242), (x + 3, 27), (x + 13, 27), 2)
                else:
                    for y in (24, 27):
                        line(WHITE, (x + 5, y), (x + 11, y), 1)

    elif category == "hair":
        color = HAIR_COLORS[key][1]
        # A dye bottle and tint brush communicate colour without drawing a head.
        framed(color, 9, 11, 22, 25)
        framed((225, 211, 228), 13, 6, 14, 7)
        rect(WHITE, 13, 22, 14, 7)
        rect(color, 16, 24, 8, 3)
        line(INK, (37, 7), (31, 34), 4)
        line(color, (40, 8), (36, 20), 6)
        line(tuple(min(255, value + 30) for value in color), (14, 15), (25, 15), 2)

    elif category == "socks":
        if key == "none":
            line((165, 145, 158), (11, 29), (37, 11), 5)
            line((202, 92, 111), (11, 10), (38, 31), 4)
        else:
            color = SOCKS[key][1]
            for x, drop in ((7, 0), (26, 4)):
                poly(INK, [(x, 6 + drop), (x + 12, 6 + drop), (x + 12, 25 + drop),
                           (x + 17, 28 + drop), (x + 16, 35 + drop), (x + 4, 35 + drop),
                           (x, 30 + drop)])
                poly(color, [(x + 2, 8 + drop), (x + 10, 8 + drop), (x + 10, 27 + drop),
                             (x + 15, 30 + drop), (x + 14, 33 + drop), (x + 5, 33 + drop),
                             (x + 2, 29 + drop)])
                if key in ("blueberry", "whale", "navy"):
                    stripe = (91, 60, 137) if key == "blueberry" else ((68, 145, 174) if key == "whale" else WHITE)
                    rect(stripe, x + 2, 13 + drop, 8, 3)
                    rect(stripe, x + 2, 20 + drop, 8, 3)
                elif key == "lace":
                    for dx in (2, 5, 8):
                        rect(WHITE, x + dx, 7 + drop, 3, 3)

    return pygame.transform.scale(c, (48 * scale, 40 * scale))
