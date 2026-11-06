"""Pantalla de relevo para ocultar la preparación secreta."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from ui.base import BaseScreen
from ui.theme import (
    GOLD,
    MUTED,
    TEXT,
    Button,
    draw_apple,
    draw_text,
    draw_wrapped_text,
)


class RelayScreen(BaseScreen):
    def __init__(
        self,
        app,
        title: str,
        player_name: str,
        message: str,
        button_label: str,
        on_continue: Callable[[], None],
    ) -> None:
        super().__init__(app)
        self.title = title
        self.player_name = player_name
        self.message = message
        self.on_continue = on_continue
        self.continue_button = Button(
            pygame.Rect(490, 572, 300, 62), button_label
        )
        self.cancel_button = Button(
            pygame.Rect(550, 660, 180, 48), "Cancelar", variant="ghost"
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.app.mouse_position
            if self.continue_button.rect.collidepoint(mouse):
                self.on_continue()
            elif self.cancel_button.rect.collidepoint(mouse):
                self.app.show_menu()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((4, 3, 6))
        pygame.draw.rect(
            surface, (17, 12, 21), pygame.Rect(0, 0, surface.get_width(), 8)
        )
        draw_apple(surface, (640, 92), 35, color=(156, 43, 58))
        draw_text(surface, self.title, 34, MUTED, (640, 154), anchor="center", bold=True)
        draw_text(
            surface,
            self.player_name,
            60,
            TEXT,
            (640, 225),
            anchor="center",
            bold=True,
        )
        draw_text(
            surface,
            "CIVIL SECRETO",
            17,
            GOLD,
            (640, 278),
            anchor="center",
            bold=True,
        )
        draw_wrapped_text(
            surface,
            self.message,
            22,
            MUTED,
            pygame.Rect(310, 320, 660, 150),
            center=True,
            line_spacing=8,
        )
        draw_text(
            surface,
            "Nadie más debe mirar la pantalla en este momento.",
            16,
            (119, 105, 127),
            (640, 512),
            anchor="center",
        )
        self.continue_button.draw(surface, self.app.mouse_position)
        self.cancel_button.draw(surface, self.app.mouse_position)
