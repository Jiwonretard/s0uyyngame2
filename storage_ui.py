"""Upgradeable house storage: the bag and each placed drawer side by side."""
import pygame
from furniture_catalog import FURNITURE_CATEGORIES, FURNITURE_LABELS
from game_state import BAG_ITEM_LABELS, STORAGE_UPGRADE_COST

INK = (55, 39, 69)
CREAM = (255, 242, 210)
PURPLE = (94, 70, 153)
RETURN_RECT = pygame.Rect(995, 625, 200, 40)
BAG_UPGRADE_RECT = pygame.Rect(85, 625, 225, 40)
DRAWER_UPGRADE_RECT = pygame.Rect(650, 625, 225, 40)


def slot_rect(index, deposit, columns=None):
    columns = columns or (4 if deposit else 5)
    if deposit or columns == 5:
        left = 85 if columns == 4 else (65 if deposit else 650)
        return pygame.Rect(
            left + (index % columns) * 104,
            175 + (index // columns) * 84,
            96,
            76,
        )
    return pygame.Rect(
        650 + (index % columns) * 90,
        175 + (index // columns) * 70,
        82,
        64,
    )


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
        if event.key == pygame.K_u or getattr(event, "scancode", None) == pygame.KSCAN_U:
            self.request_drawer_upgrade()
        elif event.key in (pygame.K_ESCAPE, pygame.K_RETURN) or self.is_interaction_key(event):
            self.overlay = "home"

    def handle_storage_click(self, position):
        if RETURN_RECT.collidepoint(position):
            self.overlay = "home"
            return
        if BAG_UPGRADE_RECT.collidepoint(position) and not self.state.bag_upgraded:
            self.request_bag_upgrade()
            return
        if DRAWER_UPGRADE_RECT.collidepoint(position) and not self.state.drawer_upgraded:
            self.request_drawer_upgrade()
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
            capacity = self.state.bag_slot_count if deposit else self.state.drawer_slot_count
            columns = self.state.bag_columns if deposit else self.state.drawer_columns
            for index, (key, amount) in enumerate(stacks[:capacity]):
                if slot_rect(index, deposit, columns).collidepoint(position):
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
            capacity = self.state.bag_slot_count if deposit else self.state.drawer_slot_count
            columns = self.state.bag_columns if deposit else self.state.drawer_columns
            self.text(f"{'가방' if deposit else '서랍'}  {len(stacks)}/{capacity}칸", 18, INK,
                      85 if deposit else 650, 145)
            for index in range(capacity):
                rect = slot_rect(index, deposit, columns)
                pygame.draw.rect(self.screen, (238, 215, 177), rect, border_radius=6)
                pygame.draw.rect(self.screen, (176, 137, 94), rect, 2, border_radius=6)
                if index >= len(stacks):
                    continue
                key, amount = stacks[index]
                compact = rect.height < 70
                icon_y = rect.y + (18 if compact else 24)
                label_y = rect.y + (37 if compact else 49)
                suffix_y = rect.y + (53 if compact else 64)
                self.draw_item_icon(key, (rect.centerx, icon_y), small=True)
                label = self.fitted_text(BAG_ITEM_LABELS[key], 13, rect.width - 6)
                self.text(label, 13, INK, rect.centerx, label_y, center=True)
                suffix = str(amount)
                if key == "fishing_rod":
                    durability = self.state.fishing_rod_durability if deposit else self.state.drawer_rod_durability.get(self.active_drawer, 40)
                    suffix = f"내구도 {durability}/40"
                self.text(self.fitted_text(suffix, 13, rect.width - 6), 13,
                          PURPLE, rect.centerx, suffix_y, center=True)
        for rect, upgraded, label in (
            (BAG_UPGRADE_RECT, self.state.bag_upgraded, "가방 5×5"),
            (DRAWER_UPGRADE_RECT, self.state.drawer_upgraded, "서랍 6×6"),
        ):
            color = (172, 165, 155) if upgraded else (221, 162, 68)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            text = f"{label} 완료" if upgraded else f"{label} 확장 {STORAGE_UPGRADE_COST:,}벨리"
            self.text(text, 14, INK, rect.centerx, rect.centery, center=True)
        self.text(self.fitted_text(self.storage_message, 13, 1100), 13, INK, 85, 675)
        pygame.draw.rect(self.screen, PURPLE, RETURN_RECT, border_radius=8)
        self.text("집으로 E / Esc", 16, CREAM, RETURN_RECT.centerx, RETURN_RECT.centery, center=True)
