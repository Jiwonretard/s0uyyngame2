"""House drawers: a 4x4 bag alongside a separate 5x5 storage grid."""
import pygame
from furniture_catalog import FURNITURE_CATEGORIES, FURNITURE_LABELS
from game_state import BAG_ITEM_LABELS, BAG_SLOT_COUNT, DRAWER_SLOT_COUNT

INK = (55, 39, 69)
CREAM = (255, 242, 210)
PURPLE = (94, 70, 153)
RETURN_RECT = pygame.Rect(995, 625, 200, 40)


def slot_rect(index, deposit):
    columns, left = (4, 85) if deposit else (5, 650)
    return pygame.Rect(left + (index % columns) * 104, 175 + (index // columns) * 84, 96, 76)


class StorageUI:
    def open_drawer(self, key=None):
        placed = [k for k in FURNITURE_CATEGORIES["drawer"] if self.state.drawer_available(k)]
        if not placed:
            self.home_category = "drawer"
            self.notify("서랍을 구입한 뒤 집 바닥에 배치해 주세요.", True)
            return
        self.active_drawer = key if key in placed else placed[0]
        self.home_edit_mode = False
        self.storage_message = "물건을 클릭하면 한 묶음, Shift + 클릭은 1개를 옮깁니다."
        self.overlay = "storage"

    def handle_storage_key(self, event):
        if event.key in (pygame.K_ESCAPE, pygame.K_RETURN) or self.is_interaction_key(event):
            self.overlay = "home"

    def handle_storage_click(self, position):
        if RETURN_RECT.collidepoint(position):
            self.overlay = "home"
            return
        for i, key in enumerate(FURNITURE_CATEGORIES["drawer"]):
            if pygame.Rect(85 + i * 224, 95, 210, 38).collidepoint(position):
                if self.state.drawer_available(key):
                    self.active_drawer = key
                else:
                    self.storage_message = "이 서랍은 집에 배치한 뒤 사용할 수 있어요."
                return
        for deposit, stacks in ((True, self.state.bag_stacks()),
                                (False, self.state.drawer_stacks(self.active_drawer))):
            for index, (key, amount) in enumerate(stacks[:BAG_SLOT_COUNT if deposit else DRAWER_SLOT_COUNT]):
                if slot_rect(index, deposit).collidepoint(position):
                    quantity = 1 if pygame.key.get_mods() & pygame.KMOD_SHIFT else amount
                    ok, self.storage_message = self.state.transfer_drawer(
                        self.active_drawer, key, quantity, deposit=deposit)
                    if ok:
                        self.save()
                    return

    def draw_storage_overlay(self):
        self.draw_screen_shade((31, 26, 39, 190))
        pygame.draw.rect(self.screen, INK, (40, 25, 1200, 670), border_radius=12)
        pygame.draw.rect(self.screen, CREAM, (45, 30, 1190, 660), border_radius=8)
        self.text("나의 서랍 보관함", 28, INK, 85, 48)
        self.text("클릭: 한 묶음 이동 · Shift + 클릭: 1개 · 한 칸 최대 16개", 15, INK, 540, 60)
        for i, key in enumerate(FURNITURE_CATEGORIES["drawer"]):
            rect = pygame.Rect(85 + i * 224, 95, 210, 38)
            active = key == self.active_drawer
            enabled = self.state.drawer_available(key)
            pygame.draw.rect(self.screen, PURPLE if active else (224, 207, 190), rect, border_radius=7)
            self.text(FURNITURE_LABELS[key] + ("" if enabled else " · 미배치"), 15,
                      CREAM if active else INK, rect.centerx, rect.centery, center=True)
        for deposit, stacks in ((True, self.state.bag_stacks()),
                                (False, self.state.drawer_stacks(self.active_drawer))):
            capacity = BAG_SLOT_COUNT if deposit else DRAWER_SLOT_COUNT
            self.text(f"{'가방' if deposit else '서랍'}  {len(stacks)}/{capacity}칸", 18, INK,
                      85 if deposit else 650, 145)
            for index in range(capacity):
                rect = slot_rect(index, deposit)
                pygame.draw.rect(self.screen, (238, 215, 177), rect, border_radius=6)
                pygame.draw.rect(self.screen, (176, 137, 94), rect, 2, border_radius=6)
                if index >= len(stacks):
                    continue
                key, amount = stacks[index]
                self.draw_item_icon(key, (rect.centerx, rect.y + 24), small=True)
                self.text(BAG_ITEM_LABELS[key], 13, INK, rect.centerx, rect.y + 49, center=True)
                suffix = str(amount)
                if key == "fishing_rod":
                    durability = self.state.fishing_rod_durability if deposit else self.state.drawer_rod_durability.get(self.active_drawer, 40)
                    suffix = f"내구도 {durability}/40"
                self.text(suffix, 13, PURPLE, rect.centerx, rect.y + 64, center=True)
        self.text(self.storage_message, 15, INK, 85, 633)
        pygame.draw.rect(self.screen, PURPLE, RETURN_RECT, border_radius=8)
        self.text("집으로 E / Esc", 16, CREAM, RETURN_RECT.centerx, RETURN_RECT.centery, center=True)
