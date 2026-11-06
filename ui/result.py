"""Pantalla de resultado con revelación de civiles y puntos."""

from __future__ import annotations

import pygame

from game.match import EndReason
from game.pieces import Color, piece_label
from ui.base import BaseScreen
from ui.theme import (
    ACCENT,
    BORDER,
    GOLD,
    GREEN,
    MUTED,
    PANEL,
    PANEL_DARK,
    TEXT,
    Button,
    draw_background,
    draw_panel,
    draw_piece_token,
    draw_progress_bar,
    draw_text,
    draw_wrapped_text,
    format_elapsed,
    format_points,
    level_color,
    truncate_text,
)


class ResultScreen(BaseScreen):
    def __init__(
        self,
        app,
        match,
        white_profile,
        black_profile,
        updates,
        save_error: str | None = None,
    ) -> None:
        super().__init__(app)
        self.match = match
        self.profiles = {Color.WHITE: white_profile, Color.BLACK: black_profile}
        self.updates = {update.profile.profile_id: update for update in updates}
        self.save_error = save_error
        self.rematch_button = Button(pygame.Rect(355, 692, 240, 56), "Revancha")
        self.ranking_button = Button(
            pygame.Rect(615, 692, 220, 56), "Ver ranking", variant="ghost"
        )
        self.menu_button = Button(
            pygame.Rect(855, 692, 160, 56), "Menú", variant="ghost"
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.app.mouse_position
            if self.rematch_button.rect.collidepoint(mouse):
                self.app.rematch()
            elif self.ranking_button.rect.collidepoint(mouse):
                self.app.show_ranking()
            elif self.menu_button.rect.collidepoint(mouse):
                self.app.show_menu()

    def _headline(self) -> tuple[str, str]:
        result = self.match.result
        if result is None:
            return "Partida terminada", ""
        capture_note = ""
        if (
            result.reason is not EndReason.CIVIL_CAPTURED
            and self.match.last_capture is not None
            and not self.match.last_capture.is_civil
        ):
            capture_note = " La última captura no era el civil."
        if result.reason is EndReason.CIVIL_CAPTURED:
            winner = self.profiles[result.winner].name
            loser = self.profiles[result.loser].name
            return f"¡{winner} gana!", f"¡Era el civil! Capturó el civil de {loser}."
        if result.reason is EndReason.RESIGN:
            winner = self.profiles[result.winner].name
            loser = self.profiles[result.loser].name
            return f"¡{winner} gana!", f"{loser} abandonó la partida.{capture_note}"
        if result.reason is EndReason.TIMEOUT:
            loser = self.profiles[result.loser].name
            return "Empate por tiempo", f"Se agotó el reloj de {loser}. Recibe -3 puntos.{capture_note}"
        if result.reason is EndReason.STALEMATE:
            player = self.profiles[self.match.turn].name
            return "Empate por ahogado", f"{player} no tenía movimientos legales.{capture_note}"
        if result.reason is EndReason.REPETITION:
            return "Empate por repetición", f"La misma posición apareció tres veces.{capture_note}"
        return "Partida terminada", ""

    def draw(self, surface: pygame.Surface) -> None:
        draw_background(surface)
        title, subtitle = self._headline()
        draw_text(surface, title, 48, TEXT, (640, 42), anchor="center", bold=True)
        draw_text(surface, subtitle, 21, GOLD, (640, 104), anchor="center")
        draw_text(
            surface,
            f"Duración de la partida: {format_elapsed(self.match.result.elapsed_seconds)}",
            16,
            MUTED,
            (640, 136),
            anchor="center",
        )

        notices = []
        for color in (Color.WHITE, Color.BLACK):
            profile = self.profiles[color]
            update = self.updates.get(profile.profile_id)
            if update and update.leveled_up:
                notices.append(f"{profile.name} subió a {update.after_level.name}.")
        if notices:
            draw_wrapped_text(
                surface,
                "  ·  ".join(notices),
                18,
                GOLD,
                pygame.Rect(190, 150, 900, 36),
                center=True,
                bold=True,
            )
        elif self.save_error:
            draw_wrapped_text(
                surface,
                self.save_error,
                16,
                ACCENT,
                pygame.Rect(190, 150, 900, 36),
                center=True,
            )

        self._draw_player_panel(surface, Color.WHITE, pygame.Rect(110, 190, 500, 370))
        self._draw_player_panel(surface, Color.BLACK, pygame.Rect(670, 190, 500, 370))

        self.rematch_button.draw(surface, self.app.mouse_position)
        self.ranking_button.draw(surface, self.app.mouse_position)
        self.menu_button.draw(surface, self.app.mouse_position)

    def _draw_player_panel(self, surface: pygame.Surface, color: Color, rect: pygame.Rect) -> None:
        profile = self.profiles[color]
        update = self.updates.get(profile.profile_id)
        result = self.match.result
        draw_panel(surface, rect)
        dot_color = (247, 241, 225) if color is Color.WHITE else (50, 42, 60)
        pygame.draw.circle(surface, dot_color, (rect.left + 34, rect.top + 34), 13)
        pygame.draw.circle(surface, (128, 107, 89), (rect.left + 34, rect.top + 34), 13, 2)
        draw_text(
            surface,
            color.spanish,
            17,
            MUTED,
            (rect.left + 58, rect.top + 24),
            bold=True,
        )
        draw_text(
            surface,
            truncate_text(profile.name, 30, 390, bold=True),
            30,
            TEXT,
            (rect.left + 30, rect.top + 52),
            bold=True,
        )

        level = profile.level
        badge = pygame.Rect(rect.left + 30, rect.top + 101, 190, 28)
        pygame.draw.rect(surface, level_color(level.index), badge, border_radius=14)
        draw_text(
            surface,
            level.name,
            15,
            (20, 17, 22),
            badge.center,
            anchor="center",
            bold=True,
        )

        delta = update.points_delta if update else result.points_delta_for(color)
        delta_color = GREEN if delta > 0 else (ACCENT if delta < 0 else MUTED)
        draw_text(
            surface,
            f"{profile.points} pts",
            38,
            TEXT,
            (rect.left + 30, rect.top + 144),
            bold=True,
        )
        draw_text(
            surface,
            f"{format_points(delta)} en esta partida",
            19,
            delta_color,
            (rect.right - 30, rect.top + 162),
            anchor="topright",
            bold=True,
        )

        if level.next_min_points is None:
            fraction = 1.0
            next_text = "Nivel máximo alcanzado"
        else:
            span = max(level.next_min_points - level.min_points, 1)
            fraction = (profile.points - level.min_points) / span
            next_text = f"Faltan {profile.points_to_next} pts para el siguiente nivel"
        bar = pygame.Rect(rect.left + 30, rect.top + 205, rect.width - 60, 14)
        draw_progress_bar(surface, bar, fraction, fill=level_color(level.index))
        draw_text(surface, next_text, 15, MUTED, (rect.left + 30, rect.top + 228))

        civil_panel = pygame.Rect(rect.left + 30, rect.top + 262, rect.width - 60, 78)
        pygame.draw.rect(surface, PANEL_DARK, civil_panel, border_radius=12)
        pygame.draw.rect(surface, BORDER, civil_panel, width=2, border_radius=12)
        civil = result.white_civil if color is Color.WHITE else result.black_civil
        draw_piece_token(
            surface,
            civil,
            (civil_panel.left + 44, civil_panel.centery),
            radius=25,
            highlight=True,
        )
        draw_text(
            surface,
            "CIVIL REVELADO",
            13,
            GOLD,
            (civil_panel.left + 84, civil_panel.top + 14),
            bold=True,
        )
        name = piece_label(civil)
        if civil.captured:
            name += " · capturado"
        draw_text(
            surface,
            name,
            20,
            TEXT,
            (civil_panel.left + 84, civil_panel.top + 36),
            bold=True,
        )

        if update and update.leveled_up:
            message = f"¡Subió de nivel: {update.after_level.name}!"
            draw_text(
                surface,
                message,
                17,
                GOLD,
                (rect.centerx, rect.bottom - 28),
                anchor="center",
                bold=True,
            )
        elif update and update.after_level.index < update.before_level.index:
            draw_text(
                surface,
                f"Bajó a {update.after_level.name}.",
                16,
                MUTED,
                (rect.centerx, rect.bottom - 28),
                anchor="center",
            )
        elif profile.compota_locked:
            draw_text(
                surface,
                "Compota de Manzana se mantiene.",
                16,
                GOLD,
                (rect.centerx, rect.bottom - 28),
                anchor="center",
                bold=True,
            )




