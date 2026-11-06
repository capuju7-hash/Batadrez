"""Pantalla de partida con tablero, relojes y anuncios."""

from __future__ import annotations

import pygame

from game.board import InvalidMoveError
from game.pieces import Color, PieceType
from ui.base import BaseScreen
from ui.theme import (
    ACCENT,
    BORDER,
    GOLD,
    GREEN,
    MUTED,
    PANEL,
    PANEL_DARK,
    PANEL_LIGHT,
    SQUARE_SIZE,
    TEXT,
    Button,
    board_cell_rect,
    cell_from_mouse,
    draw_background,
    draw_board,
    draw_panel,
    draw_piece_token,
    draw_progress_bar,
    draw_text,
    draw_wrapped_text,
    format_clock,
    format_elapsed,
    level_color,
    square_name,
    truncate_text,
)

BOARD_ORIGIN = (64, 136)


class MatchScreen(BaseScreen):
    def __init__(self, app, match, white_profile, black_profile) -> None:
        super().__init__(app)
        self.match = match
        self.white_profile = white_profile
        self.black_profile = black_profile
        self.selected: tuple[int, int] | None = None
        self.legal_moves: set[tuple[int, int]] = set()
        self.last_move: tuple[tuple[int, int], tuple[int, int]] | None = None
        self.toast = ""
        self.toast_timer = 0.0
        self.log: list[str] = []
        self.finished = False
        self.abandon_open = False
        self.rules_open = False
        self.top_card = pygame.Rect(64, 52, 544, 64)
        self.bottom_card = pygame.Rect(64, 710, 544, 58)
        self.side_panel = pygame.Rect(650, 136, 590, 622)
        self.abandon_button = Button(
            pygame.Rect(676, 686, 190, 52), "Abandonar", variant="danger"
        )
        self.rules_button = Button(
            pygame.Rect(882, 686, 150, 52), "Reglas", variant="ghost"
        )
        self.confirm_abandon = Button(
            pygame.Rect(390, 462, 230, 54), "Sí, abandonar", variant="danger"
        )
        self.cancel_abandon = Button(
            pygame.Rect(660, 462, 230, 54), "Seguir jugando", variant="ghost"
        )
        self.close_rules = Button(
            pygame.Rect(530, 648, 220, 52), "Cerrar", variant="ghost"
        )

    def profile_for(self, color: Color):
        return self.white_profile if color is Color.WHITE else self.black_profile

    def _open_result(self) -> None:
        if self.finished:
            return
        self.finished = True
        self.selected = None
        self.legal_moves = set()
        self.app.finish_match(self.match)

    def _select_piece(self, row: int, col: int) -> None:
        piece = self.match.board.piece_at(row, col)
        if piece is None:
            self.selected = None
            self.legal_moves = set()
            return
        if piece.color is not self.match.turn:
            self.toast = f"Es el turno de {self.match.turn.spanish.lower()}."
            self.toast_timer = 2.5
            return
        self.selected = (row, col)
        self.legal_moves = set(self.match.board.legal_moves(piece))

    def _handle_board_click(self, cell: tuple[int, int]) -> None:
        row, col = cell
        if self.selected is not None and (row, col) in self.legal_moves:
            start = self.selected
            try:
                outcome = self.match.play_move(start, (row, col))
            except InvalidMoveError as exc:
                self.toast = str(exc)
                self.toast_timer = 2.5
                return
            self.last_move = (start, (row, col))
            self.selected = None
            self.legal_moves = set()
            if outcome.capture_event is not None and not outcome.capture_event.is_civil:
                captured = outcome.capture_event.captured_piece
                message = (
                    f"{outcome.capture_event.capturing_color.spanish} capturaron "
                    f"un {captured.kind.spanish}. No era el civil."
                )
                self.toast = message
                self.toast_timer = 5.0
                self.log.append(message)
                self.log = self.log[-6:]
            if outcome.result is not None:
                self._open_result()
            return

        piece = self.match.board.piece_at(row, col)
        if piece is not None and piece.color is self.match.turn:
            self._select_piece(row, col)
            return
        if self.selected is not None:
            self.toast = "Ese movimiento no es legal. Elige un destino resaltado."
            self.toast_timer = 2.2
            self.selected = None
            self.legal_moves = set()

    def handle_event(self, event: pygame.event.Event) -> None:
        mouse = self.app.mouse_position
        if self.abandon_open:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.confirm_abandon.rect.collidepoint(mouse):
                    self.abandon_open = False
                    self.match.resign(self.match.turn)
                    self._open_result()
                elif self.cancel_abandon.rect.collidepoint(mouse):
                    self.abandon_open = False
            return
        if self.rules_open:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.close_rules.rect.collidepoint(mouse):
                    self.rules_open = False
            return
        if self.finished:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                self.selected = None
                self.legal_moves = set()
                return
            if event.button != 1:
                return
            if self.abandon_button.rect.collidepoint(mouse):
                self.abandon_open = True
                return
            if self.rules_button.rect.collidepoint(mouse):
                self.rules_open = True
                return
            cell = cell_from_mouse(mouse, BOARD_ORIGIN)
            if cell is not None:
                self._handle_board_click(cell)

    def update(self, delta_seconds: float) -> None:
        if self.toast_timer > 0:
            self.toast_timer = max(0.0, self.toast_timer - delta_seconds)
            if self.toast_timer == 0:
                self.toast = ""
        if self.finished:
            return
        result = self.match.tick(delta_seconds)
        if result is not None:
            self._open_result()

    def draw(self, surface: pygame.Surface) -> None:
        draw_background(surface)
        self._draw_player_card(surface, Color.BLACK, self.top_card)
        self._draw_player_card(surface, Color.WHITE, self.bottom_card)
        draw_board(surface, BOARD_ORIGIN)
        self._draw_highlights(surface)
        for piece in self.match.board.all_pieces():
            if piece.position is None:
                continue
            rect = board_cell_rect(piece.row, piece.col, BOARD_ORIGIN)
            draw_piece_token(surface, piece, rect.center, radius=27)
        self._draw_legal_markers(surface)
        self._draw_side_panel(surface)

        self.abandon_button.draw(surface, self.app.mouse_position)
        self.rules_button.draw(surface, self.app.mouse_position)

        if self.abandon_open:
            self._draw_abandon_modal(surface)
        if self.rules_open:
            self._draw_rules_modal(surface)

    def _draw_player_card(self, surface: pygame.Surface, color: Color, rect: pygame.Rect) -> None:
        profile = self.profile_for(color)
        current = self.match.turn is color and not self.finished
        draw_panel(
            surface,
            rect,
            color=PANEL_LIGHT if current else PANEL,
            radius=14,
            border=GOLD if current else None,
            shadow=False,
        )
        dot_color = (246, 240, 224) if color is Color.WHITE else (52, 43, 61)
        pygame.draw.circle(surface, dot_color, (rect.left + 24, rect.centery), 11)
        pygame.draw.circle(surface, (128, 107, 89), (rect.left + 24, rect.centery), 11, 2)
        if current:
            pygame.draw.circle(surface, GOLD, (rect.left + 24, rect.centery), 15, 2)

        name = truncate_text(profile.name, 21, 240, bold=True)
        draw_text(
            surface,
            name,
            21,
            TEXT,
            (rect.left + 44, rect.top + 10),
            bold=True,
        )
        level = profile.level
        badge = pygame.Rect(rect.left + 44, rect.top + 37, 132, 20)
        pygame.draw.rect(surface, level_color(level.index), badge, border_radius=10)
        draw_text(
            surface,
            level.name,
            12,
            (20, 17, 22),
            badge.center,
            anchor="center",
            bold=True,
        )
        next_text = (
            "Nivel máximo"
            if profile.points_to_next is None
            else f"faltan {profile.points_to_next} pts"
        )
        draw_text(
            surface,
            f"{profile.points} pts · {next_text}",
            15,
            MUTED,
            (rect.left + 186, rect.top + 38),
        )

        remaining = self.match.remaining_for(color)
        clock_color = ACCENT if remaining <= 30 else (GOLD if current else TEXT)
        draw_text(
            surface,
            format_clock(remaining),
            34,
            clock_color,
            (rect.right - 18, rect.centery),
            anchor="midright",
            bold=True,
        )

    def _draw_highlights(self, surface: pygame.Surface) -> None:
        if self.last_move is not None:
            for cell in self.last_move:
                rect = board_cell_rect(cell[0], cell[1], BOARD_ORIGIN)
                pygame.draw.rect(surface, (164, 118, 187), rect, width=3)
        cell = cell_from_mouse(self.app.mouse_position, BOARD_ORIGIN)
        if cell is not None:
            rect = board_cell_rect(cell[0], cell[1], BOARD_ORIGIN)
            pygame.draw.rect(surface, (246, 231, 198), rect, width=2)
        if self.selected is not None:
            rect = board_cell_rect(self.selected[0], self.selected[1], BOARD_ORIGIN)
            pygame.draw.rect(surface, GOLD, rect, width=4)

    def _draw_legal_markers(self, surface: pygame.Surface) -> None:
        for row, col in self.legal_moves:
            rect = board_cell_rect(row, col, BOARD_ORIGIN)
            target = self.match.board.piece_at(row, col)
            if target is None:
                pygame.draw.circle(surface, (62, 92, 60), rect.center, 9)
                pygame.draw.circle(surface, (228, 210, 160), rect.center, 9, 2)
            else:
                pygame.draw.circle(surface, ACCENT, rect.center, 30, 4)

    def _draw_side_panel(self, surface: pygame.Surface) -> None:
        draw_panel(surface, self.side_panel)
        turn_profile = self.profile_for(self.match.turn)
        draw_text(surface, "TURNO", 15, MUTED, (676, 156), bold=True)
        draw_text(
            surface,
            truncate_text(turn_profile.name, 30, 420, bold=True),
            30,
            TEXT,
            (676, 180),
            bold=True,
        )
        draw_text(
            surface,
            f"{self.match.turn.spanish} · minuto {format_elapsed(self.match.elapsed_seconds())}",
            18,
            GOLD,
            (676, 220),
        )
        draw_text(
            surface,
            "4:00 por jugador",
            15,
            MUTED,
            (1210, 158),
            anchor="topright",
        )

        message_rect = pygame.Rect(676, 252, 538, 78)
        if self.toast:
            pygame.draw.rect(surface, (73, 50, 79), message_rect, border_radius=12)
            pygame.draw.rect(surface, GOLD, message_rect, width=2, border_radius=12)
            draw_wrapped_text(
                surface,
                self.toast,
                17,
                TEXT,
                message_rect.inflate(-24, -20),
                line_spacing=4,
                bold=True,
            )
        else:
            draw_wrapped_text(
                surface,
                "Haz clic en una pieza y luego en una casilla resaltada. Clic derecho cancela la selección.",
                16,
                MUTED,
                message_rect.inflate(-6, 0),
                line_spacing=4,
            )

        draw_text(surface, "Capturas y anuncios", 18, TEXT, (676, 352), bold=True)
        log_rect = pygame.Rect(676, 382, 538, 282)
        pygame.draw.rect(surface, PANEL_DARK, log_rect, border_radius=12)
        if not self.log:
            draw_text(
                surface,
                "Todavía no hubo capturas.",
                16,
                MUTED,
                (log_rect.centerx, log_rect.top + 26),
                anchor="center",
            )
        else:
            y = log_rect.top + 14
            for entry in self.log[-6:]:
                draw_text(surface, "•", 18, GOLD, (log_rect.left + 14, y), bold=True)
                draw_wrapped_text(
                    surface,
                    entry,
                    15,
                    TEXT,
                    pygame.Rect(log_rect.left + 34, y, log_rect.width - 50, 38),
                    line_spacing=2,
                )
                y += 42

        draw_text(
            surface,
            "El civil sigue en secreto hasta el final.",
            14,
            MUTED,
            (676, 668),
        )

    def _draw_modal_overlay(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((7, 5, 10, 205))
        surface.blit(overlay, (0, 0))

    def _draw_abandon_modal(self, surface: pygame.Surface) -> None:
        self._draw_modal_overlay(surface)
        panel = pygame.Rect(320, 250, 640, 320)
        draw_panel(surface, panel, color=PANEL, radius=20, border=BORDER)
        profile = self.profile_for(self.match.turn)
        draw_text(
            surface,
            "Abandonar la partida",
            31,
            TEXT,
            (panel.centerx, panel.top + 40),
            anchor="center",
            bold=True,
        )
        draw_wrapped_text(
            surface,
            f"¿{profile.name} abandona? La derrota cuenta con los puntos del minuto actual "
            f"({format_elapsed(self.match.elapsed_seconds())}).",
            19,
            MUTED,
            pygame.Rect(panel.left + 60, panel.top + 92, panel.width - 120, 90),
            center=True,
            line_spacing=5,
        )
        self.confirm_abandon.draw(surface, self.app.mouse_position)
        self.cancel_abandon.draw(surface, self.app.mouse_position)

    def _draw_rules_modal(self, surface: pygame.Surface) -> None:
        self._draw_modal_overlay(surface)
        panel = pygame.Rect(230, 100, 820, 625)
        draw_panel(surface, panel, color=PANEL, radius=20, border=BORDER)
        draw_text(
            surface,
            "Cómo se juega",
            34,
            TEXT,
            (panel.centerx, panel.top + 42),
            anchor="center",
            bold=True,
        )
        rules = (
            "Cada bando tiene 9 piezas y un civil secreto. Gana quien capture el civil rival.\n\n"
            "No hay jaque, jaque mate, enroque, captura al paso ni coronación. "
            "El rey es una pieza más y puede ser capturado.\n\n"
            "El peón avanza una casilla y captura en diagonal hacia delante. "
            "En la última fila queda inmóvil.\n\n"
            "Cada jugador tiene 4:00. El reloj corre solo en su turno. "
            "Si se agota, es empate con -3 puntos para quien se quedó sin tiempo.\n\n"
            "Empate por ahogado o por repetir tres veces la misma posición: 0 puntos. "
            "Abandonar: derrota con los puntos del minuto actual.\n\n"
            "Al capturar una pieza se anuncia si era el civil. Si lo era, la partida termina. "
            "Los civiles se revelan únicamente en el resultado."
        )
        draw_wrapped_text(
            surface,
            rules,
            18,
            TEXT,
            pygame.Rect(panel.left + 54, panel.top + 92, panel.width - 108, 440),
            line_spacing=5,
        )
        draw_text(
            surface,
            "El reloj sigue corriendo mientras este panel está abierto.",
            15,
            GOLD,
            (panel.centerx, panel.top + 548),
            anchor="center",
        )
        self.close_rules.draw(surface, self.app.mouse_position)

