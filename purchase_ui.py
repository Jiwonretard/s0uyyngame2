"""Modal purchase confirmation shared by home furniture and wardrobe shops."""
from dataclasses import dataclass
from typing import Callable
import pygame

CARD = pygame.Rect(360, 230, 560, 260)
BUY_BUTTON = pygame.Rect(397, 416, 225, 48)
CANCEL_BUTTON = pygame.Rect(658, 416, 225, 48)


@dataclass
class PurchasePrompt:
    label: str
    price: int
    action: Callable[[], None]
    buy_selected: bool = False


class PurchaseUI:
    def request_purchase(self, label, price, action):
        if self.pending_purchase is None:
            self.pending_purchase = PurchasePrompt(label, price, action)

    def finish_purchase_confirmation(self, buy):
        prompt = self.pending_purchase
        # Clear first so repeated input cannot execute the same purchase twice.
        self.pending_purchase = None
        if prompt is not None and buy:
            if self.state.money < prompt.price:
                self.notify(f"벨리가 부족해요. {prompt.price:,}벨리가 필요해요.", True)
                return
            prompt.action()

    def handle_purchase_key(self, event):
        if getattr(event, 'repeat', False):
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_n):
            self.finish_purchase_confirmation(False)
        elif event.key == pygame.K_y or getattr(event, 'scancode', None) == pygame.KSCAN_Y:
            self.finish_purchase_confirmation(True)
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
            self.pending_purchase.buy_selected = not self.pending_purchase.buy_selected
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.finish_purchase_confirmation(self.pending_purchase.buy_selected)

    def handle_purchase_click(self, position):
        if BUY_BUTTON.collidepoint(position):
            self.finish_purchase_confirmation(True)
        elif CANCEL_BUTTON.collidepoint(position):
            self.finish_purchase_confirmation(False)

    def draw_purchase_confirmation(self):
        prompt = self.pending_purchase
        self.draw_screen_shade((31, 26, 39, 180))
        pygame.draw.rect(self.screen, (55, 39, 69), CARD.inflate(8, 8), border_radius=14)
        pygame.draw.rect(self.screen, (255, 242, 210), CARD, border_radius=10)
        self.text('정말 구매할까요?', 25, (55, 39, 69), CARD.centerx, 267, center=True)
        label = self.fitted_text(prompt.label, 22, CARD.width - 48)
        self.text(label, 22, (94, 70, 153), CARD.centerx, 310, center=True)
        self.text(f'가격 {prompt.price:,}벨리', 20, (55, 39, 69), CARD.centerx, 345, center=True)
        remaining = self.state.money - prompt.price
        balance = (f'보유 {self.state.money:,}벨리 · 구매 후 {remaining:,}벨리'
                   if remaining >= 0 else f'보유 {self.state.money:,}벨리 · {-remaining:,}벨리 부족')
        self.text(self.fitted_text(balance, 16, CARD.width - 40), 16,
                  (122, 101, 113) if remaining >= 0 else (169, 65, 62), CARD.centerx, 380, center=True)
        for rect, label, selected in (
            (BUY_BUTTON, '구매하기 Y', prompt.buy_selected),
            (CANCEL_BUTTON, '취소 Esc', not prompt.buy_selected),
        ):
            pygame.draw.rect(self.screen, (94, 70, 153), rect, border_radius=8)
            if selected:
                pygame.draw.rect(self.screen, (236, 167, 48), rect.inflate(6, 6), 3, border_radius=10)
            self.text(label, 18, (255, 242, 210), rect.centerx, rect.centery, center=True)
