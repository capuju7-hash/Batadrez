"""Piezas y colores del juego."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from game.constants import BOARD_SIZE, PIECE_COUNTS


class Color(Enum):
    WHITE = "white"
    BLACK = "black"

    @property
    def opponent(self) -> "Color":
        return Color.BLACK if self is Color.WHITE else Color.WHITE

    @property
    def spanish(self) -> str:
        return "Blancas" if self is Color.WHITE else "Negras"


class PieceType(Enum):
    KING = "king"
    QUEEN = "queen"
    ROOK = "rook"
    BISHOP = "bishop"
    KNIGHT = "knight"
    PAWN = "pawn"

    @property
    def spanish(self) -> str:
        names = {
            PieceType.KING: "Rey",
            PieceType.QUEEN: "Dama",
            PieceType.ROOK: "Torre",
            PieceType.BISHOP: "Alfil",
            PieceType.KNIGHT: "Caballo",
            PieceType.PAWN: "Peón",
        }
        return names[self]


@dataclass
class Piece:

    piece_id: str
    color: Color
    kind: PieceType
    row: int = -1
    col: int = -1
    civil: bool = False
    has_moved: bool = False
    captured: bool = False
    initial_row: int | None = None
    initial_col: int | None = None

    @property
    def position(self) -> tuple[int, int] | None:
        if self.row < 0 or self.col < 0:
            return None
        return (self.row, self.col)

    def place(self, row: int, col: int) -> None:
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            raise ValueError("La posición está fuera del tablero.")
        self.row = row
        self.col = col
        if self.initial_row is None or self.initial_col is None:
            self.initial_row = row
            self.initial_col = col

    def clear_position(self) -> None:
        self.row = -1
        self.col = -1

    def clone(self) -> "Piece":
        return Piece(
            piece_id=self.piece_id,
            color=self.color,
            kind=self.kind,
            row=self.row,
            col=self.col,
            civil=self.civil,
            has_moved=self.has_moved,
            captured=self.captured,
            initial_row=self.initial_row,
            initial_col=self.initial_col,
        )


def create_piece_set(color: Color) -> list[Piece]:

    pieces: list[Piece] = []
    for kind_name, count in PIECE_COUNTS.items():
        kind = PieceType(kind_name)
        for index in range(1, count + 1):
            pieces.append(
                Piece(
                    piece_id=f"{color.value}-{kind.value}-{index}",
                    color=color,
                    kind=kind,
                )
            )
    return pieces


PIECE_LETTERS_ES = {
    PieceType.KING: "R",
    PieceType.QUEEN: "D",
    PieceType.ROOK: "T",
    PieceType.BISHOP: "A",
    PieceType.KNIGHT: "C",
    PieceType.PAWN: "P",
}


def piece_label(piece: Piece) -> str:

    base = piece.kind.spanish
    if piece.initial_row is None or piece.initial_col is None:
        return base
    file_name = chr(ord("a") + piece.initial_col)
    rank = BOARD_SIZE - piece.initial_row
    return f"{base} ({file_name}{rank})"
