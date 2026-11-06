"""Utilidades compartidas por las pruebas."""

from __future__ import annotations

from game import constants as rules
from game.pieces import Color, Piece, PieceType, create_piece_set
from game.setup import Setup


def default_positions(color: Color) -> list[tuple[int, int]]:
    first_row, second_row = rules.HOME_ROWS_BY_COLOR[color.value]
    return [(first_row, col) for col in range(rules.BOARD_SIZE)] + [(second_row, 0)]


def make_setup(
    color: Color,
    positions: list[tuple[int, int]] | None = None,
    civil_kind: PieceType | None = None,
    civil_index: int = 0,
    validate: bool = True,
) -> Setup:
    pieces = create_piece_set(color)
    chosen_positions = positions or default_positions(color)
    for piece, position in zip(pieces, chosen_positions):
        piece.place(*position)

    if civil_kind is None:
        civil_piece = pieces[civil_index]
    else:
        matching = [piece for piece in pieces if piece.kind is civil_kind]
        civil_piece = matching[civil_index]
    civil_piece.civil = True
    setup = Setup(color=color, pieces=pieces, civil_id=civil_piece.piece_id)
    if validate:
        setup.validate()
    return setup


def make_match_setups() -> tuple[Setup, Setup]:
    return make_setup(Color.WHITE), make_setup(Color.BLACK)


def make_capture_setups(
    black_civil_index: int = 0,
) -> tuple[Setup, Setup]:
    """Blancas tienen una torre en (6, 0) y negras una pieza en (1, 0)."""

    white_positions = [(7, 0), (7, 1), (6, 0), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7), (7, 2)]
    black_positions = [(1, 0)] + [(0, col) for col in range(1, 8)] + [(0, 0)]
    white = make_setup(Color.WHITE, white_positions, civil_index=0)
    black = make_setup(Color.BLACK, black_positions, civil_index=black_civil_index)
    return white, black


def empty_piece(
    color: Color, kind: PieceType, row: int, col: int, suffix: str = "x"
) -> Piece:
    return Piece(
        piece_id=f"{color.value}-{kind.value}-{suffix}",
        color=color,
        kind=kind,
        row=row,
        col=col,
    )

