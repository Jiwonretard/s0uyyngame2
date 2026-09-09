"""Wardrobe screen and controls, shared with the game's live character renderer."""
import pygame
from dressup import product_surface
from wardrobe_catalog import CATEGORIES, OPTIONS, DEFAULT_LOOK, option_label, cosmetic_price, theme_price

INK = (55, 39, 69)
CREAM = (255, 242, 210)
PURPLE = (94, 70, 153)
MUTED = (122, 101, 113)
TABS = tuple(CATEGORIES)
RETURN_RECT = pygame.Rect(920, 605, 270, 45)
RESET_RECT = pygame.Rect(80, 605, 260, 45)
BLUEBERRY_RECT = pygame.Rect(80, 483, 280, 42)
WHALE_RECT = pygame.Rect(80, 535, 280, 42)


def tab_rect(index):
    return pygame.Rect(80 + index * 224, 108, 208, 38)


def item_rect(index):
    return pygame.Rect(430 + (index % 4) * 190, 175 + (index // 4) * 135, 180, 125)


class WardrobeUI:
    def open_wardrobe(self):
        if not self.state.wardrobe_available:
            self.home_category = "wardrobe"
            if "wardrobe" not in self.state.furniture_owned:
                self.notify("옷장을 1,500코인에 구입해 집에 놓아 주세요.", True)
            else:
                self.select_furniture("wardrobe")
                self.home_edit_mode = True
                self.notify("바닥을 클릭해 옷장을 놓으면 옷을 갈아입을 수 있어요.")
            return
        self.home_edit_mode = False
        self.wardrobe_category = "outfit"
        self.wardrobe_direction = "down"
        self.wardrobe_thumbnails = {}
        self.overlay = "wardrobe"

    def apply_wardrobe_option(self, key):
        if not self.state.owns_cosmetic(self.wardrobe_category, key):
            bought, message = self.state.buy_cosmetic(self.wardrobe_category, key)
            self.notify(message, not bought)
            if not bought:
                return
        if self.state.equip_cosmetic(self.wardrobe_category, key):
            self.refresh_appearance()
            self.save()

    def handle_wardrobe_key(self, event):
        if event.key in (pygame.K_ESCAPE, pygame.K_RETURN) or self.is_interaction_key(event):
            self.overlay = "home"
        elif pygame.K_1 <= event.key <= pygame.K_5:
            self.wardrobe_category = TABS[event.key - pygame.K_1]
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            directions = ("down", "left", "up", "right")
            index = directions.index(self.wardrobe_direction)
            self.wardrobe_direction = directions[(index + (1 if event.key == pygame.K_RIGHT else -1)) % 4]

    def handle_wardrobe_click(self, position):
        if RETURN_RECT.collidepoint(position):
            self.overlay = "home"
            return
        if RESET_RECT.collidepoint(position):
            self.state.appearance = {}
            self.refresh_appearance()
            self.save()
            return
        for rect, theme in ((BLUEBERRY_RECT, "blueberry"), (WHALE_RECT, "whale")):
            if rect.collidepoint(position):
                if not self.state.owns_theme(theme):
                    bought, message = self.state.buy_theme(theme)
                    self.notify(message, not bought)
                    if not bought:
                        return
                if self.state.equip_theme(theme):
                    self.refresh_appearance()
                    self.save()
                return
        for index, category in enumerate(TABS):
            if tab_rect(index).collidepoint(position):
                self.wardrobe_category = category
                return
        for index, key in enumerate(OPTIONS[self.wardrobe_category]):
            if item_rect(index).collidepoint(position):
                self.apply_wardrobe_option(key)
                return

    def draw_wardrobe_overlay(self):
        self.draw_screen_shade((31, 26, 39, 190))
        room = pygame.Rect(45, 30, 1190, 650)
        pygame.draw.rect(self.screen, INK, room.inflate(10, 10), border_radius=12)
        pygame.draw.rect(self.screen, CREAM, room, border_radius=8)
        self.text("블루벨리 옷장", 28, INK, 80, 50)
        self.text(f"상품을 구입해 자유롭게 조합 · 보유 {self.state.money:,}코인 · 착용 자동 저장", 15, MUTED, 420, 62)
        for index, category in enumerate(TABS):
            rect = tab_rect(index)
            selected = category == self.wardrobe_category
            pygame.draw.rect(self.screen, PURPLE if selected else (226, 211, 228), rect, border_radius=8)
            self.text(f"{index + 1}  {CATEGORIES[category]}", 17, CREAM if selected else INK,
                      rect.centerx, rect.centery, center=True)

        mirror = pygame.Rect(80, 167, 280, 260)
        pygame.draw.rect(self.screen, (205, 170, 123), mirror.inflate(10, 10), border_radius=20)
        pygame.draw.rect(self.screen, (219, 237, 231), mirror, border_radius=15)
        phase = (0, 1, 0, 2)[int(self.frame_time * 5) % 4]
        frames = self.player_frames[self.wardrobe_direction]
        sprite = frames[phase]
        sprite = pygame.transform.scale(sprite, (sprite.get_width() * 2, sprite.get_height() * 2))
        self.screen.blit(sprite, sprite.get_rect(midbottom=(220, 420)))
        self.text("← → 방향 보기 · 걷기 미리보기", 14, MUTED, 220, 452, center=True)
        look = {**DEFAULT_LOOK, **self.state.appearance}
        for index, key in enumerate(OPTIONS[self.wardrobe_category]):
            rect = item_rect(index)
            selected = look[self.wardrobe_category] == key
            owned = self.state.owns_cosmetic(self.wardrobe_category, key)
            pygame.draw.rect(self.screen, (223, 236, 201) if selected else (250, 229, 192), rect, border_radius=8)
            pygame.draw.rect(self.screen, PURPLE if selected else (185, 150, 109), rect, 3 if selected else 1, border_radius=8)
            cache_key = (self.wardrobe_category, key)
            if cache_key not in self.wardrobe_thumbnails:
                if len(self.wardrobe_thumbnails) >= 128:
                    self.wardrobe_thumbnails.clear()
                self.wardrobe_thumbnails[cache_key] = product_surface(
                    self.wardrobe_category, key, scale=2
                )
            thumbnail = self.wardrobe_thumbnails[cache_key]
            self.screen.blit(thumbnail, thumbnail.get_rect(center=(rect.centerx, rect.y + 46)))
            self.text(option_label(self.wardrobe_category, key), 14, INK, rect.centerx, rect.y + 91, center=True)
            status = "보유" if owned else f"{cosmetic_price(self.wardrobe_category, key):,}코인"
            self.text(status, 13, PURPLE if owned else MUTED, rect.centerx, rect.y + 111, center=True)
            if selected:
                self.text("착용", 13, PURPLE, rect.right - 23, rect.y + 12, center=True)
        blueberry_action = ("입기" if self.state.owns_theme("blueberry") else
                            f"구매 {theme_price('blueberry', self.state.owned_cosmetics):,}")
        whale_action = ("입기" if self.state.owns_theme("whale") else
                        f"구매 {theme_price('whale', self.state.owned_cosmetics):,}")
        for rect, label in ((BLUEBERRY_RECT, f"블루베리 세트 {blueberry_action}"),
                            (WHALE_RECT, f"고래 세트 {whale_action}"),
                            (RESET_RECT, "처음 캐릭터로 되돌리기"),
                            (RETURN_RECT, "입고 나가기  E / Esc")):
            pygame.draw.rect(self.screen, PURPLE, rect, border_radius=8)
            self.text(label, 16, CREAM, rect.centerx, rect.centery, center=True)
