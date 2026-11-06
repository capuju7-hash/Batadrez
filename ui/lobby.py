"""Selección de los dos perfiles que jugarán."""

from __future__ import annotations

import pygame

from ui.base import BaseScreen
from ui.theme import (
    BORDER,
    GOLD,
    MUTED,
    PANEL,
    PANEL_DARK,
    PANEL_LIGHT,
    TEXT,
    Button,
    draw_background,
    draw_panel,
    draw_text,
    level_color,
    truncate_text,
)


class LobbyScreen(BaseScreen):
    ROW_HEIGHT = 55
    VISIBLE_ROWS = 7

    def __init__(self, app) -> None:
        super().__init__(app)
        self.profiles = sorted(
            app.profile_manager.profiles, key=lambda profile: profile.name.casefold()
        )
        self.selected = {"p1": None, "p2": None}
        if self.profiles:
            self.selected["p1"] = self.profiles[0].profile_id
        if len(self.profiles) > 1:
            self.selected["p2"] = self.profiles[1].profile_id
        self.scroll = {"p1": 0, "p2": 0}
        self.message = ""
        self.panels = {
            "p1": pygame.Rect(80, 158, 540, 470),
            "p2": pygame.Rect(660, 158, 540, 470),
        }
        self.start_button = Button(
            pygame.Rect(480, 682, 320, 58), "Comenzar preparación"
        )
        self.manage_button = Button(
            pygame.Rect(80, 682, 250, 54), "Gestionar perfiles", variant="ghost"
        )
        self.back_button = Button(
            pygame.Rect(1060, 682, 140, 54), "Volver", variant="ghost"
        )

    def _rows(self, key: str) -> list[tuple[int, pygame.Rect]]:
        panel = self.panels[key]
        start = self.scroll[key]
        rows = []
        for visible in range(self.VISIBLE_ROWS):
            index = start + visible
            if index >= len(self.profiles):
                break
            rect = pygame.Rect(
                panel.left + 18,
                panel.top + 82 + visible * self.ROW_HEIGHT,
                panel.width - 36,
                47,
            )
            rows.append((index, rect))
        return rows

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEWHEEL:
            key = "p1" if self.app.mouse_position[0] < 640 else "p2"
            maximum = max(0, len(self.profiles) - self.VISIBLE_ROWS)
            self.scroll[key] = max(
                0, min(self.scroll[key] - event.y, maximum)
            )
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.app.mouse_position
            for key in ("p1", "p2"):
                for index, rect in self._rows(key):
                    if rect.collidepoint(mouse):
                        profile = self.profiles[index]
                        other_key = "p2" if key == "p1" else "p1"
                        if self.selected[other_key] == profile.profile_id:
                            self.message = "Ese perfil ya está elegido para el otro jugador."
                        else:
                            self.selected[key] = profile.profile_id
                            self.message = ""
                        return
            if self.start_button.rect.collidepoint(mouse):
                if self.selected["p1"] and self.selected["p2"]:
                    self.app.begin_match_setup(
                        self.selected["p1"], self.selected["p2"]
                    )
            elif self.manage_button.rect.collidepoint(mouse):
                self.app.show_profiles(
                    "Crea o elimina perfiles y luego vuelve a Nueva partida."
                )
            elif self.back_button.rect.collidepoint(mouse):
                self.app.show_menu()

    def draw(self, surface: pygame.Surface) -> None:
        draw_background(surface)
        draw_text(surface, "Nueva partida", 44, TEXT, (64, 28), bold=True)
        draw_text(
            surface,
            "Elige un perfil para cada jugador. Los colores se sortean al comenzar.",
            19,
            MUTED,
            (64, 83),
        )

        if len(self.profiles) < 2:
            draw_panel(surface, self.panels["p1"])
            draw_text(
                surface,
                "Necesitas al menos dos perfiles.",
                24,
                MUTED,
                self.panels["p1"].center,
                anchor="center",
            )
        else:
            for key, title in (("p1", "Jugador 1"), ("p2", "Jugador 2")):
                self._draw_panel(surface, key, title)

        if self.message:
            draw_text(surface, self.message, 18, GOLD, (640, 650), anchor="center")

        self.start_button.enabled = bool(
            self.selected["p1"]
            and self.selected["p2"]
            and self.selected["p1"] != self.selected["p2"]
        )
        self.start_button.draw(surface, self.app.mouse_position)
        self.manage_button.draw(surface, self.app.mouse_position)
        self.back_button.draw(surface, self.app.mouse_position)

    def _draw_panel(self, surface: pygame.Surface, key: str, title: str) -> None:
        panel = self.panels[key]
        draw_panel(surface, panel)
        player_color = (204, 165, 92) if key == "p1" else (150, 138, 202)
        pygame.draw.circle(surface, player_color, (panel.left + 32, panel.top + 38), 11)
        draw_text(
            surface,
            title,
            27,
            TEXT,
            (panel.left + 56, panel.top + 24),
            bold=True,
        )
        selected_id = self.selected[key]
        selected_profile = self.app.profile_manager.get(selected_id) if selected_id else None
        if selected_profile:
            draw_text(
                surface,
                f"Elegido: {selected_profile.name}",
                16,
                MUTED,
                (panel.right - 20, panel.top + 31),
                anchor="midright",
            )

        for index, rect in self._rows(key):
            profile = self.profiles[index]
            selected = profile.profile_id == selected_id
            other_key = "p2" if key == "p1" else "p1"
            used_elsewhere = self.selected[other_key] == profile.profile_id
            fill = PANEL_LIGHT if selected else PANEL_DARK
            pygame.draw.rect(surface, fill, rect, border_radius=10)
            border = GOLD if selected else (65, 52, 73)
            pygame.draw.rect(surface, border, rect, width=2, border_radius=10)
            if used_elsewhere:
                pygame.draw.rect(surface, (26, 20, 31), rect, border_radius=10)
                pygame.draw.rect(surface, border, rect, width=2, border_radius=10)

            name_color = MUTED if used_elsewhere else TEXT
            draw_text(
                surface,
                truncate_text(profile.name, 21, 210, bold=True),
                21,
                name_color,
                (rect.left + 16, rect.centery),
                anchor="midleft",
                bold=True,
            )
            badge = pygame.Rect(rect.left + 250, rect.centery - 12, 145, 24)
            pygame.draw.rect(surface, level_color(profile.level.index), badge, border_radius=12)
            draw_text(
                surface,
                profile.level.name,
                13,
                (20, 17, 22),
                badge.center,
                anchor="center",
                bold=True,
            )
            draw_text(
                surface,
                f"{profile.points} pts",
                16,
                MUTED if used_elsewhere else TEXT,
                (rect.right - 15, rect.centery),
                anchor="midright",
            )

        if len(self.profiles) > self.VISIBLE_ROWS:
            track = pygame.Rect(panel.right - 10, panel.top + 88, 4, panel.height - 110)
            pygame.draw.rect(surface, PANEL_DARK, track, border_radius=2)
            maximum = max(1, len(self.profiles) - self.VISIBLE_ROWS)
            thumb_height = max(36, int(track.height * self.VISIBLE_ROWS / len(self.profiles)))
            travel = track.height - thumb_height
            thumb_y = track.top + int(travel * self.scroll[key] / maximum)
            pygame.draw.rect(
                surface,
                BORDER,
                pygame.Rect(track.left, thumb_y, track.width, thumb_height),
                border_radius=2,
            )
