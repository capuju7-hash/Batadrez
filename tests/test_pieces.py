"""Fase 1: movimientos y capturas de todas las piezas."""

from __future__ import annotations

from game import constants as rules
from game.board import Board
from game.pieces import Color, PieceType

from tests.helpers import empty_piece


def moves_for(board: Board, piece) -> set[tuple[int, int]]:
    return set(board.legal_moves(piece))


def test_white_pawn_advances_and_captures_diagonally():
    board = Board()
    pawn = empty_piece(Color.WHITE, PieceType.PAWN, 6, 3)
    enemy = empty_piece(Color.BLACK, PieceType.PAWN, 5, 4)
    own = empty_piece(Color.WHITE, PieceType.PAWN, 5, 2)
    for piece in (pawn, enemy, own):
        board.add_piece(piece)

    assert moves_for(board, pawn) == {(5, 3), (5, 4)}


def test_black_pawn_moves_in_the_opposite_direction():
    board = Board()
    pawn = empty_piece(Color.BLACK, PieceType.PAWN, 1, 3)
    enemy = empty_piece(Color.WHITE, PieceType.KNIGHT, 2, 2)
    board.add_piece(pawn)
    board.add_piece(enemy)

    assert moves_for(board, pawn) == {(2, 3), (2, 2)}


def test_pawn_is_blocked_by_piece_in_front():
    board = Board()
    pawn = empty_piece(Color.WHITE, PieceType.PAWN, 4, 3)
    blocker = empty_piece(Color.BLACK, PieceType.PAWN, 3, 3)
    board.add_piece(pawn)
    board.add_piece(blocker)

    assert moves_for(board, pawn) == set()


def test_pawn_is_immobile_on_last_row():
    board = Board()
    white = empty_piece(Color.WHITE, PieceType.PAWN, 0, 2)
    black = empty_piece(Color.BLACK, PieceType.PAWN, 7, 5)
    board.add_piece(white)
    board.add_piece(black)

    assert board.legal_moves(white) == []
    assert board.legal_moves(black) == []


def test_pawn_does_not_move_two_by_default():
    board = Board()
    pawn = empty_piece(Color.WHITE, PieceType.PAWN, 6, 3)
    board.add_piece(pawn)

    assert moves_for(board, pawn) == {(5, 3)}


def test_pawn_two_square_move_is_configurable(monkeypatch):
    monkeypatch.setattr(rules, "PAWN_CAN_MOVE_TWO", True)
    board = Board()
    pawn = empty_piece(Color.WHITE, PieceType.PAWN, 6, 3)
    board.add_piece(pawn)

    assert moves_for(board, pawn) == {(5, 3), (4, 3)}


def test_pawn_two_square_move_requires_clear_path(monkeypatch):
    monkeypatch.setattr(rules, "PAWN_CAN_MOVE_TWO", True)
    board = Board()
    pawn = empty_piece(Color.WHITE, PieceType.PAWN, 6, 3)
    blocker = empty_piece(Color.BLACK, PieceType.KNIGHT, 4, 3)
    board.add_piece(pawn)
    board.add_piece(blocker)

    assert moves_for(board, pawn) == {(5, 3)}


def test_knight_jumps_and_captures():
    board = Board()
    knight = empty_piece(Color.WHITE, PieceType.KNIGHT, 4, 4)
    enemy = empty_piece(Color.BLACK, PieceType.PAWN, 2, 3)
    own = empty_piece(Color.WHITE, PieceType.PAWN, 6, 3)
    for piece in (knight, enemy, own):
        board.add_piece(piece)

    moves = moves_for(board, knight)
    assert (2, 3) in moves
    assert (6, 3) not in moves
    assert len(moves) == 7


def test_king_moves_one_square_and_captures():
    board = Board()
    king = empty_piece(Color.WHITE, PieceType.KING, 4, 4)
    enemy = empty_piece(Color.BLACK, PieceType.ROOK, 3, 3)
    own = empty_piece(Color.WHITE, PieceType.PAWN, 5, 5)
    for piece in (king, enemy, own):
        board.add_piece(piece)

    moves = moves_for(board, king)
    assert (3, 3) in moves
    assert (5, 5) not in moves
    assert (4, 5) in moves
    assert (2, 2) not in moves


def test_rook_slides_and_stops_at_blockers():
    board = Board()
    rook = empty_piece(Color.WHITE, PieceType.ROOK, 4, 4)
    enemy = empty_piece(Color.BLACK, PieceType.PAWN, 2, 4)
    own = empty_piece(Color.WHITE, PieceType.PAWN, 4, 6)
    for piece in (rook, enemy, own):
        board.add_piece(piece)

    moves = moves_for(board, rook)
    assert (3, 4) in moves
    assert (2, 4) in moves
    assert (1, 4) not in moves
    assert (4, 5) in moves
    assert (4, 6) not in moves
    assert (4, 7) not in moves


def test_bishop_slides_diagonally_and_captures():
    board = Board()
    bishop = empty_piece(Color.WHITE, PieceType.BISHOP, 4, 4)
    enemy = empty_piece(Color.BLACK, PieceType.KNIGHT, 1, 1)
    for piece in (bishop, enemy):
        board.add_piece(piece)

    moves = moves_for(board, bishop)
    assert (3, 3) in moves
    assert (2, 2) in moves
    assert (1, 1) in moves
    assert (0, 0) not in moves
    assert (5, 5) in moves
    assert (4, 5) not in moves


def test_queen_combines_rook_and_bishop_moves():
    board = Board()
    queen = empty_piece(Color.WHITE, PieceType.QUEEN, 4, 4)
    board.add_piece(queen)

    moves = moves_for(board, queen)
    assert {(4, 0), (4, 7), (0, 4), (7, 4)} <= moves
    assert (0, 0) in moves
    assert (7, 7) in moves
    assert (5, 4) in moves
    assert (2, 1) not in moves  # no salto de caballo


def test_king_can_be_captured_like_any_piece():
    board = Board()
    rook = empty_piece(Color.WHITE, PieceType.ROOK, 6, 3)
    king = empty_piece(Color.BLACK, PieceType.KING, 3, 3)
    board.add_piece(rook)
    board.add_piece(king)

    captured = board.move((6, 3), (3, 3))

    assert captured is king
    assert captured.captured is True
    assert board.piece_at(3, 3) is rook


def test_moving_piece_updates_position_and_moved_flag():
    board = Board()
    rook = empty_piece(Color.WHITE, PieceType.ROOK, 6, 0)
    board.add_piece(rook)

    board.move((6, 0), (4, 0))

    assert rook.position == (4, 0)
    assert rook.has_moved is True

