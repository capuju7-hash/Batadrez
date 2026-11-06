"""Ranking de perfiles por puntos acumulados."""

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
    draw_progress_bar,
    draw_text,
    level_color,
    truncate_text,
)


class RankingScreen(BaseScreen):
    ROW_HEIGHT = 68
    VISIBLE_ROWS = 7

    def __init__(self, app) -> None:
        super().__init__(app)
        self.ranking = app.profile_manager.ranking()
        self.scroll = 0
        self.list_rect = pygame.Rect(100, 145, 1080, 500)
        self.profiles_button = Button(
            pygame.Rect(100, 680, 220, 54), "Perfiles", variant="ghost"
        )
        self.back_button = Button(
            pygame.Rect(1060, 680, 120, 54), "Volver", variant="ghost"
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEWHEEL:
            maximum = max(0, len(self.ranking) - self.VISIBLE_ROWS)
            self.scroll = max(0, min(self.scroll - event.y, maximum))
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.app.mouse_position
            if self.profiles_button.rect.collidepoint(mouse):
                self.app.show_profiles()
            elif self.back_button.rect.collidepoint(mouse):
                self.app.show_menu()

    def draw(self, surface: pygame.Surface) -> None:
        draw_background(surface)
        draw_text(surface, "Ranking", 44, TEXT, (64, 28), bold=True)
        draw_text(
            surface,
            "Ordenado por puntos acumulados. La meta es llegar a Compota de Manzana.",
            19,
            MUTED,
            (64, 83),
        )
        draw_panel(surface, self.list_rect)
        if not self.ranking:
            draw_text(
                surface,
                "Todavía no hay perfiles en el ranking.",
                24,
                MUTED,
                self.list_rect.center,
                anchor="center",
            )
        else:
            for visible in range(self.VISIBLE_ROWS):
                index = self.scroll + visible
                if index >= len(self.ranking):
                    break
                profile = self.ranking[index]
                rect = pygame.Rect(
                    self.list_rect.left + 16,
                    self.list_rect.top + 14 + visible * self.ROW_HEIGHT,
                    self.list_rect.width - 32,
                    58,
                )
                self._draw_row(surface, profile, index, rect)
            if len(self.ranking) > self.VISIBLE_ROWS:
                self._draw_scrollbar(surface)

        self.profiles_button.draw(surface, self.app.mouse_position)
        self.back_button.draw(surface, self.app.mouse_position)

    def _draw_row(self, surface: pygame.Surface, profile, index: int, rect: pygame.Rect) -> None:
        fill = PANEL_LIGHT if index < 3 else PANEL_DARK
        pygame.draw.rect(surface, fill, rect, border_radius=12)
        pygame.draw.rect(surface, BORDER, rect, width=1, border_radius=12)
        medal_colors = [(222, 173, 63), (184, 189, 198), (183, 119, 79)]
        medal = medal_colors[index] if index < 3 else (83, 69, 92)
        pygame.draw.circle(surface, medal, (rect.left + 32, rect.centery), 19)
        draw_text(
            surface,
            str(index + 1),
            20,
            (23, 19, 26),
            (rect.left + 32, rect.centery),
            anchor="center",
            bold=True,
        )

        draw_text(
            surface,
            truncate_text(profile.name, 24, 290, bold=True),
            24,
            TEXT,
            (rect.left + 66, rect.centery),
            anchor="midleft",
            bold=True,
        )
        level = profile.level
        badge = pygame.Rect(rect.left + 400, rect.centery - 15, 205, 30)
        pygame.draw.rect(surface, level_color(level.index), badge, border_radius=15)
        draw_text(
            surface,
            level.name,
            15,
            (20, 17, 22),
            badge.center,
            anchor="center",
            bold=True,
        )

        draw_text(
            surface,
            f"{profile.points} pts",
            23,
            GOLD if level.next_min_points is None else TEXT,
            (rect.left + 650, rect.centery),
            anchor="midleft",
            bold=True,
        )
        if level.next_min_points is None:
            fraction = 1.0
            next_text = "Meta cumplida"
        else:
            span = max(level.next_min_points - level.min_points, 1)
            fraction = (profile.points - level.min_points) / span
            next_text = f"Faltan {profile.points_to_next} pts"
        bar = pygame.Rect(rect.left + 800, rect.centery - 7, 190, 13)
        draw_progress_bar(surface, bar, fraction, fill=level_color(level.index))
        draw_text(surface, next_text, 14, MUTED, (bar.left, rect.centery + 17))

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        track = pygame.Rect(self.list_rect.right - 13, self.list_rect.top + 18, 5, 455)
        pygame.draw.rect(surface, PANEL_DARK, track, border_radius=3)
        maximum = max(1, len(self.ranking) - self.VISIBLE_ROWS)
        thumb_height = max(40, int(track.height * self.VISIBLE_ROWS / len(self.ranking)))
        travel = track.height - thumb_height
        thumb_y = track.top + int(travel * self.scroll / maximum)
        pygame.draw.rect(
            surface,
            BORDER,
            pygame.Rect(track.left, thumb_y, track.width, thumb_height),
            border_radius=3,
        )
