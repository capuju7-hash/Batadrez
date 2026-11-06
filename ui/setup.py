"""Preparación secreta: elegir el civil y acomodar las piezas."""

from __future__ import annotations

import pygame

from game import constants as rules
from game.pieces import Color, PieceType, create_piece_set
from game.setup import InvalidSetupError, Setup
from ui.base import BaseScreen
from ui.theme import (
    BOARD_X,
    BOARD_Y,
    BORDER,
    GOLD,
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
    draw_text,
    draw_wrapped_text,
    get_font,
)

BOARD_ORIGIN = (BOARD_X, 156)


class SetupScreen(BaseScreen):
    def __init__(self, app, profile, color: Color) -> None:
        super().__init__(app)
        self.profile = profile
        self.color = color
        self.pieces = create_piece_set(color)
        self.civil_id: str | None = None
        self.selected_kind: PieceType | None = None
        self.selected_piece_id: str | None = None
        self.civil_mode = False
        self.message = "Elige una pieza del set y colócala en una de tus dos filas."
        self.message_color = MUTED

        self.panel = pygame.Rect(650, 148, 590, 610)
        self.palette_rects: dict[PieceType, pygame.Rect] = {}
        kinds = [
            PieceType.KING,
            PieceType.QUEEN,
            PieceType.ROOK,
            PieceType.BISHOP,
            PieceType.KNIGHT,
            PieceType.PAWN,
        ]
        for index, kind in enumerate(kinds):
            col = index % 3
            row = index // 3
            self.palette_rects[kind] = pygame.Rect(
                670 + col * 186, 202 + row * 82, 174, 70
            )

        self.civil_button = Button(
            pygame.Rect(670, 590, 185, 48), "Elegir civil", variant="ghost"
        )
        self.remove_button = Button(
            pygame.Rect(867, 590, 165, 48), "Quitar pieza", variant="ghost"
        )
        self.clear_button = Button(
            pygame.Rect(1044, 590, 175, 48), "Vaciar", variant="danger"
        )
        self.cancel_button = Button(
            pygame.Rect(670, 660, 150, 48), "Cancelar", variant="ghost"
        )
        self.confirm_button = Button(
            pygame.Rect(842, 660, 377, 54), "Confirmar preparación"
        )

    @property
    def home_rows(self) -> tuple[int, int]:
        return rules.HOME_ROWS_BY_COLOR[self.color.value]

    @property
    def placed_count(self) -> int:
        return sum(1 for piece in self.pieces if piece.position is not None)

    def _find_piece_at(self, row: int, col: int):
        for piece in self.pieces:
            if piece.position == (row, col):
                return piece
        return None

    def _unplaced_of(self, kind: PieceType):
        return [
            piece
            for piece in self.pieces
            if piece.kind is kind and piece.position is None
        ]

    def _kind_count(self, kind: PieceType) -> int:
        return sum(1 for piece in self.pieces if piece.kind is kind)

    def _remaining_count(self, kind: PieceType) -> int:
        return len(self._unplaced_of(kind))

    def _select_piece(self, piece) -> None:
        self.selected_piece_id = piece.piece_id
        self.selected_kind = None
        self.message = "Pieza seleccionada. Haz clic en una casilla libre de tus filas para moverla."
        self.message_color = MUTED

    def _remove_piece(self, piece) -> None:
        piece.clear_position()
        piece.civil = False
        if piece.piece_id == self.civil_id:
            self.civil_id = None
        if piece.piece_id == self.selected_piece_id:
            self.selected_piece_id = None
        self.message = "Pieza retirada."
        self.message_color = MUTED

    def _mark_civil(self, piece) -> None:
        if piece.kind is PieceType.PAWN and not rules.CIVIL_CAN_BE_PAWN:
            self.message = "La configuración actual no permite que un peón sea el civil."
            self.message_color = GOLD
            return
        for other in self.pieces:
            other.civil = False
        piece.civil = True
        self.civil_id = piece.piece_id
        self.civil_mode = False
        self.selected_kind = None
        self.message = f"Civil elegido: {piece.kind.spanish}. Recuerda que es secreto."
        self.message_color = GOLD

    def _handle_board_click(self, cell: tuple[int, int], right_click: bool = False) -> None:
        row, col = cell
        piece = self._find_piece_at(row, col)
        if right_click:
            if piece is not None:
                self._remove_piece(piece)
            return

        if self.civil_mode:
            if piece is None:
                self.message = "Haz clic sobre una de tus piezas colocadas."
                self.message_color = GOLD
            else:
                self._mark_civil(piece)
            return

        if piece is not None:
            self._select_piece(piece)
            return

        if row not in self.home_rows:
            self.message = "Solo puedes usar tus dos filas iniciales."
            self.message_color = GOLD
            return

        if self.selected_piece_id is not None:
            selected = next(
                (
                    item
                    for item in self.pieces
                    if item.piece_id == self.selected_piece_id
                ),
                None,
            )
            if selected is None:
                self.selected_piece_id = None
                return
            selected.place(row, col)
            self.selected_piece_id = None
            self.message = "Pieza movida."
            self.message_color = MUTED
            return

        if self.selected_kind is not None:
            if self._remaining_count(self.selected_kind) == 0:
                self.selected_kind = None
                return
            piece = self._unplaced_of(self.selected_kind)[0]
            piece.place(row, col)
            if self._remaining_count(self.selected_kind) == 0:
                self.selected_kind = None
            self.message = f"{piece.kind.spanish} colocado."
            self.message_color = MUTED
            return

        self.message = "Elige una pieza del set y luego una casilla."
        self.message_color = MUTED

    def _clear_setup(self) -> None:
        for piece in self.pieces:
            piece.clear_position()
            piece.civil = False
        self.civil_id = None
        self.selected_kind = None
        self.selected_piece_id = None
        self.civil_mode = False
        self.message = "Preparación vaciada."
        self.message_color = MUTED

    def _try_confirm(self) -> None:
        if self.placed_count != rules.SET_SIZE:
            self.message = f"Debes colocar las {rules.SET_SIZE} piezas antes de confirmar."
            self.message_color = GOLD
            return
        if self.civil_id is None:
            self.message = "Debes elegir una pieza como civil."
            self.message_color = GOLD
            return
        setup = Setup(self.color, self.pieces, self.civil_id)
        try:
            setup.validate()
        except InvalidSetupError as exc:
            self.message = str(exc)
            self.message_color = GOLD
            return
        self.app.register_setup(setup)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            mouse = self.app.mouse_position
            if event.button == 1:
                if self.civil_button.rect.collidepoint(mouse):
                    self.civil_mode = not self.civil_mode
                    self.selected_kind = None
                    self.selected_piece_id = None
                    self.message = (
                        "Haz clic en una pieza colocada para marcarla como civil."
                        if self.civil_mode
                        else "Selecciona una pieza del set."
                    )
                    self.message_color = GOLD if self.civil_mode else MUTED
                    return
                if self.remove_button.rect.collidepoint(mouse):
                    selected = next(
                        (
                            piece
                            for piece in self.pieces
                            if piece.piece_id == self.selected_piece_id
                        ),
                        None,
                    )
                    if selected is not None:
                        self._remove_piece(selected)
                    else:
                        self.message = "Primero selecciona una pieza colocada."
                        self.message_color = GOLD
                    return
                if self.clear_button.rect.collidepoint(mouse):
                    self._clear_setup()
                    return
                if self.cancel_button.rect.collidepoint(mouse):
                    self.app.show_menu()
                    return
                if self.confirm_button.rect.collidepoint(mouse):
                    self._try_confirm()
                    return

                for kind, rect in self.palette_rects.items():
                    if rect.collidepoint(mouse):
                        if self._remaining_count(kind) == 0:
                            self.message = f"No quedan piezas de tipo {kind.spanish}."
                            self.message_color = GOLD
                        else:
                            self.selected_kind = kind
                            self.selected_piece_id = None
                            self.civil_mode = False
                            self.message = (
                                f"{kind.spanish} seleccionado. Elige una casilla libre."
                            )
                            self.message_color = MUTED
                        return

            cell = cell_from_mouse(mouse, BOARD_ORIGIN)
            if cell is not None:
                self._handle_board_click(cell, right_click=event.button == 3)

    def draw(self, surface: pygame.Surface) -> None:
        draw_background(surface)
        draw_text(surface, "Preparación secreta", 42, TEXT, (64, 26), bold=True)
        color_dot = (244, 238, 222) if self.color is Color.WHITE else (49, 41, 58)
        pygame.draw.circle(surface, color_dot, (71, 88), 10)
        pygame.draw.circle(surface, (146, 122, 100), (71, 88), 10, 2)
        draw_text(
            surface,
            f"{self.profile.name} · {self.color.spanish}",
            20,
            MUTED,
            (90, 77),
        )
        draw_text(
            surface,
            "Coloca tus 9 piezas en tus dos filas y marca una como civil.",
            17,
            MUTED,
            (64, 111),
        )

        draw_board(surface, BOARD_ORIGIN, highlight_rows=self.home_rows)
        self._draw_hover(surface)
        for piece in self.pieces:
            position = piece.position
            if position is None:
                continue
            row, col = position
            rect = board_cell_rect(row, col, BOARD_ORIGIN)
            draw_piece_token(
                surface,
                piece,
                rect.center,
                radius=27,
                highlight=piece.piece_id == self.selected_piece_id,
                show_civil=piece.civil,
            )

        self._draw_side_panel(surface)
        self.civil_button.label = "Cancelar civil" if self.civil_mode else "Elegir civil"
        self.civil_button.draw(surface, self.app.mouse_position, selected=self.civil_mode)
        self.remove_button.enabled = self.selected_piece_id is not None
        self.remove_button.draw(surface, self.app.mouse_position)
        self.clear_button.draw(surface, self.app.mouse_position)
        self.cancel_button.draw(surface, self.app.mouse_position)
        self.confirm_button.enabled = (
            self.placed_count == rules.SET_SIZE and self.civil_id is not None
        )
        self.confirm_button.draw(surface, self.app.mouse_position)

    def _draw_hover(self, surface: pygame.Surface) -> None:
        cell = cell_from_mouse(self.app.mouse_position, BOARD_ORIGIN)
        if cell is None or cell[0] not in self.home_rows:
            return
        rect = board_cell_rect(cell[0], cell[1], BOARD_ORIGIN)
        pygame.draw.rect(surface, GOLD, rect, width=3)

    def _draw_side_panel(self, surface: pygame.Surface) -> None:
        draw_panel(surface, self.panel)
        draw_text(surface, "Tu set", 26, TEXT, (670, 162), bold=True)
        draw_text(
            surface,
            f"{self.placed_count}/9 colocadas",
            17,
            MUTED,
            (1215, 170),
            anchor="topright",
        )

        for kind, rect in self.palette_rects.items():
            remaining = self._remaining_count(kind)
            total = self._kind_count(kind)
            selected = self.selected_kind is kind
            fill = PANEL_LIGHT if selected else PANEL_DARK
            pygame.draw.rect(surface, fill, rect, border_radius=12)
            pygame.draw.rect(
                surface,
                GOLD if selected else BORDER,
                rect,
                width=2,
                border_radius=12,
            )
            sample = next(piece for piece in self.pieces if piece.kind is kind)
            draw_piece_token(surface, sample, (rect.left + 35, rect.centery), radius=22)
            name_color = TEXT if remaining else MUTED
            draw_text(
                surface,
                kind.spanish,
                18,
                name_color,
                (rect.left + 66, rect.centery - 11),
                bold=True,
            )
            draw_text(
                surface,
                f"{remaining} de {total}",
                15,
                MUTED,
                (rect.left + 66, rect.centery + 12),
            )
            if remaining == 0:
                pygame.draw.rect(surface, (28, 22, 33), rect, border_radius=12)
                pygame.draw.rect(surface, BORDER, rect, width=2, border_radius=12)
                draw_text(
                    surface,
                    "Sin stock",
                    14,
                    MUTED,
                    rect.center,
                    anchor="center",
                    bold=True,
                )

        civil_text = "Sin elegir"
        if self.civil_id:
            civil_piece = next(
                piece for piece in self.pieces if piece.piece_id == self.civil_id
            )
            civil_text = civil_piece.kind.spanish
        draw_text(surface, "Civil secreto:", 19, MUTED, (670, 386), bold=True)
        draw_text(surface, civil_text, 22, GOLD, (810, 384), bold=True)
        draw_text(
            surface,
            "Durante la partida nunca se indicará cuál es.",
            15,
            MUTED,
            (670, 414),
        )

        instruction = (
            "Haz clic en una de tus piezas para marcarla como civil."
            if self.civil_mode
            else "Elige una pieza del set y luego una casilla libre. Clic derecho quita una pieza."
        )
        draw_wrapped_text(
            surface,
            instruction,
            16,
            MUTED,
            pygame.Rect(670, 448, 548, 70),
            line_spacing=4,
        )
        draw_wrapped_text(
            surface,
            self.message,
            17,
            self.message_color,
            pygame.Rect(670, 520, 548, 58),
            line_spacing=4,
            bold=True,
        )

