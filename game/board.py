"""Tablero y generación de movimientos. No conoce pygame ni turnos."""

from __future__ import annotations

from game import constants as rules
from game.pieces import Color, Piece, PieceType

Position = tuple[int, int]


class InvalidMoveError(ValueError):
    pass


class Board:
    def __init__(self) -> None:
        self.squares: list[list[Piece | None]] = [
            [None for _ in range(rules.BOARD_SIZE)]
            for _ in range(rules.BOARD_SIZE)
        ]

    def is_inside(self, row: int, col: int) -> bool:
        return 0 <= row < rules.BOARD_SIZE and 0 <= col < rules.BOARD_SIZE

    def piece_at(self, row: int, col: int) -> Piece | None:
        if not self.is_inside(row, col):
            return None
        return self.squares[row][col]

    def add_piece(self, piece: Piece, row: int | None = None, col: int | None = None) -> None:
        if row is not None or col is not None:
            if row is None or col is None:
                raise ValueError("Debe indicarse fila y columna juntas.")
            piece.place(row, col)
        position = piece.position
        if position is None:
            raise ValueError("La pieza no tiene una posición.")
        piece_row, piece_col = position
        if not self.is_inside(piece_row, piece_col):
            raise ValueError("La pieza está fuera del tablero.")
        if self.squares[piece_row][piece_col] is not None:
            raise InvalidMoveError("La casilla ya está ocupada.")
        if piece.initial_row is None or piece.initial_col is None:
            piece.initial_row = piece_row
            piece.initial_col = piece_col
        piece.captured = False
        self.squares[piece_row][piece_col] = piece

    def legal_moves(self, piece: Piece) -> list[Position]:
        position = piece.position
        if position is None:
            return []
        row, col = position
        if self.piece_at(row, col) is not piece:
            return []

        if piece.kind is PieceType.PAWN:
            return self._pawn_moves(piece)
        if piece.kind is PieceType.KNIGHT:
            return self._knight_moves(piece)
        if piece.kind is PieceType.KING:
            return self._king_moves(piece)
        if piece.kind is PieceType.ROOK:
            return self._sliding_moves(piece, ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if piece.kind is PieceType.BISHOP:
            return self._sliding_moves(piece, ((1, 1), (1, -1), (-1, 1), (-1, -1)))
        if piece.kind is PieceType.QUEEN:
            return self._sliding_moves(
                piece,
                (
                    (1, 0),
                    (-1, 0),
                    (0, 1),
                    (0, -1),
                    (1, 1),
                    (1, -1),
                    (-1, 1),
                    (-1, -1),
                ),
            )
        return []

    def _can_land(self, piece: Piece, row: int, col: int) -> bool:
        if not self.is_inside(row, col):
            return False
        target = self.squares[row][col]
        return target is None or target.color is not piece.color

    def _pawn_moves(self, piece: Piece) -> list[Position]:
        row, col = piece.position  # type: ignore[misc]
        forward = rules.PAWN_FORWARD_BY_COLOR[piece.color.value]
        last_row = rules.PAWN_LAST_ROW_BY_COLOR[piece.color.value]
        if row == last_row:
            return []

        moves: list[Position] = []
        next_row = row + forward
        if self.is_inside(next_row, col) and self.squares[next_row][col] is None:
            moves.append((next_row, col))
            two_row = row + 2 * forward
            if (
                rules.PAWN_CAN_MOVE_TWO
                and not piece.has_moved
                and self.is_inside(two_row, col)
                and self.squares[two_row][col] is None
            ):
                moves.append((two_row, col))

        for offset in (-1, 1):
            capture_col = col + offset
            if not self.is_inside(next_row, capture_col):
                continue
            target = self.squares[next_row][capture_col]
            if target is not None and target.color is not piece.color:
                moves.append((next_row, capture_col))
        return moves

    def _knight_moves(self, piece: Piece) -> list[Position]:
        row, col = piece.position  # type: ignore[misc]
        offsets = (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        )
        return [
            (row + dr, col + dc)
            for dr, dc in offsets
            if self._can_land(piece, row + dr, col + dc)
        ]

    def _king_moves(self, piece: Piece) -> list[Position]:
        row, col = piece.position  # type: ignore[misc]
        return [
            (row + dr, col + dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr or dc) and self._can_land(piece, row + dr, col + dc)
        ]

    def _sliding_moves(
        self, piece: Piece, directions: tuple[Position, ...]
    ) -> list[Position]:
        row, col = piece.position  # type: ignore[misc]
        moves: list[Position] = []
        for dr, dc in directions:
            next_row, next_col = row + dr, col + dc
            while self.is_inside(next_row, next_col):
                target = self.squares[next_row][next_col]
                if target is None:
                    moves.append((next_row, next_col))
                else:
                    if target.color is not piece.color:
                        moves.append((next_row, next_col))
                    break
                next_row += dr
                next_col += dc
        return moves

    def move(self, start: Position, destination: Position) -> Piece | None:
        start_row, start_col = start
        piece = self.piece_at(start_row, start_col)
        if piece is None:
            raise InvalidMoveError("No hay ninguna pieza en la casilla de origen.")
        if destination not in self.legal_moves(piece):
            raise InvalidMoveError("Ese movimiento no es legal para la pieza.")

        dest_row, dest_col = destination
        captured = self.squares[dest_row][dest_col]
        self.squares[start_row][start_col] = None
        if captured is not None:
            captured.captured = True
        self.squares[dest_row][dest_col] = piece
        piece.row = dest_row
        piece.col = dest_col
        piece.has_moved = True
        return captured

    def all_pieces(self, color: Color | None = None) -> list[Piece]:
        pieces: list[Piece] = []
        for row in self.squares:
            for piece in row:
                if piece is not None and (color is None or piece.color is color):
                    pieces.append(piece)
        return pieces

    def has_any_move(self, color: Color) -> bool:
        return any(self.legal_moves(piece) for piece in self.all_pieces(color))

    def position_key(self) -> tuple:
        entries = []
        for piece in self.all_pieces():
            moved_flag = (
                piece.has_moved
                if piece.kind is PieceType.PAWN and rules.PAWN_CAN_MOVE_TWO
                else False
            )
            entries.append(
                (
                    piece.color.value,
                    piece.kind.value,
                    piece.row,
                    piece.col,
                    moved_flag,
                )
            )
        return tuple(sorted(entries))

    def clone(self) -> "Board":
        new_board = Board()
        for piece in self.all_pieces():
            new_board.add_piece(piece.clone())
        return new_board
