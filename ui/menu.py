"""Pantalla del menú principal."""

from __future__ import annotations

import pygame

from ui.base import BaseScreen
from ui.theme import (
    ACCENT,
    GOLD,
    MUTED,
    PANEL,
    TEXT,
    Button,
    draw_apple,
    draw_background,
    draw_panel,
    draw_text,
    draw_wrapped_text,
)


class MenuScreen(BaseScreen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.buttons = {
            "play": Button(pygame.Rect(470, 350, 340, 60), "Jugar"),
            "profiles": Button(pygame.Rect(470, 428, 340, 60), "Perfiles"),
            "ranking": Button(pygame.Rect(470, 506, 340, 60), "Ranking"),
            "quit": Button(pygame.Rect(470, 584, 340, 60), "Salir", variant="ghost"),
        }

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.app.mouse_position
            if self.buttons["play"].rect.collidepoint(mouse):
                if len(self.app.profile_manager.profiles) < 2:
                    self.app.show_profiles(
                        "Crea al menos dos perfiles para poder jugar una partida."
                    )
                else:
                    self.app.show_lobby()
            elif self.buttons["profiles"].rect.collidepoint(mouse):
                self.app.show_profiles()
            elif self.buttons["ranking"].rect.collidepoint(mouse):
                self.app.show_ranking()
            elif self.buttons["quit"].rect.collidepoint(mouse):
                self.app.quit()

    def draw(self, surface: pygame.Surface) -> None:
        draw_background(surface)
        draw_apple(surface, (640, 107), 42)
        draw_text(surface, "BATADREZ", 78, TEXT, (640, 174), anchor="center", bold=True)
        draw_text(
            surface,
            "Ajedrez con un secreto. Captura el civil rival y gana.",
            23,
            GOLD,
            (640, 221),
            anchor="center",
        )

        for button in self.buttons.values():
            button.draw(surface, self.app.mouse_position)

        if self.app.profile_manager.load_error:
            banner = pygame.Rect(290, 660, 700, 66)
            draw_panel(surface, banner, color=(75, 48, 38), radius=12, border=GOLD)
            draw_wrapped_text(
                surface,
                "Aviso: hubo un problema con profiles.json. Se guardó una copia y se empezó de cero. Revisa la pantalla de perfiles.",
                16,
                TEXT,
                pygame.Rect(308, 672, 664, 44),
                center=True,
            )
        else:
            draw_panel(surface, pygame.Rect(470, 660, 340, 66), color=PANEL, radius=12, shadow=False)
            draw_wrapped_text(
                surface,
                "2 jugadores · mismo equipo · 4:00 por jugador · el civil es secreto",
                15,
                MUTED,
                pygame.Rect(488, 673, 304, 40),
                center=True,
            )
        draw_text(
            surface,
            "Hecho para partidas cara a cara",
            14,
            (116, 102, 123),
            (640, 772),
            anchor="center",
        )
        pygame.draw.circle(surface, ACCENT, (110, 735), 4)
        pygame.draw.circle(surface, GOLD, (1160, 748), 3)

