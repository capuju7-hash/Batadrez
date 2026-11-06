"""Preparación secreta de cada jugador."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from game import constants as rules
from game.pieces import Color, Piece, PieceType


class InvalidSetupError(ValueError):
    pass


@dataclass
class Setup:
    color: Color
    pieces: list[Piece]
    civil_id: str

    @property
    def civil_piece(self) -> Piece:
        for piece in self.pieces:
            if piece.piece_id == self.civil_id:
                return piece
        raise InvalidSetupError("El civil elegido no pertenece al set.")

    def validate(self) -> None:
        if len(self.pieces) != rules.SET_SIZE:
            raise InvalidSetupError(
                f"Se deben colocar exactamente {rules.SET_SIZE} piezas."
            )

        ids = [piece.piece_id for piece in self.pieces]
        if len(ids) != len(set(ids)):
            raise InvalidSetupError("Hay piezas duplicadas en la preparación.")

        if any(piece.color is not self.color for piece in self.pieces):
            raise InvalidSetupError("Todas las piezas deben ser del mismo color.")

        expected_counts = Counter(
            {PieceType(name): count for name, count in rules.PIECE_COUNTS.items()}
        )
        actual_counts = Counter(piece.kind for piece in self.pieces)
        if actual_counts != expected_counts:
            raise InvalidSetupError("El set de piezas no tiene la composición correcta.")

        home_rows = rules.HOME_ROWS_BY_COLOR[self.color.value]
        occupied: set[tuple[int, int]] = set()
        for piece in self.pieces:
            position = piece.position
            if position is None:
                raise InvalidSetupError("Todas las piezas deben estar colocadas.")
            row, col = position
            if row not in home_rows:
                raise InvalidSetupError(
                    "Las piezas deben ubicarse en las dos filas iniciales."
                )
            if not 0 <= col < rules.BOARD_SIZE:
                raise InvalidSetupError("Hay una pieza fuera del tablero.")
            if position in occupied:
                raise InvalidSetupError("No puede haber dos piezas en la misma casilla.")
            occupied.add(position)

        civil = [piece for piece in self.pieces if piece.piece_id == self.civil_id]
        if len(civil) != 1:
            raise InvalidSetupError("Debe elegirse exactamente un civil válido.")
        if civil[0].kind is PieceType.PAWN and not rules.CIVIL_CAN_BE_PAWN:
            raise InvalidSetupError("La configuración actual no permite un peón civil.")

    def clone(self) -> "Setup":
        return Setup(
            color=self.color,
            pieces=[piece.clone() for piece in self.pieces],
            civil_id=self.civil_id,
        )
