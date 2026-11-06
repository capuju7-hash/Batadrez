"""Fase 3: relojes, puntuación, tiempo agotado, ahogado y repetición."""

from __future__ import annotations

import pytest

from game.board import Board
from game.match import (
    EndReason,
    Match,
    score_bracket_index,
    win_loss_deltas,
)
from game.pieces import Color, PieceType

from tests.helpers import empty_piece, make_match_setups


def test_score_brackets_are_inclusive_at_the_limits():
    assert score_bracket_index(0) == 0
    assert score_bracket_index(120) == 0
    assert win_loss_deltas(120) == (10, -10)

    assert score_bracket_index(120.0001) == 1
    assert score_bracket_index(300) == 1
    assert win_loss_deltas(300) == (7, -7)

    assert score_bracket_index(300.0001) == 2
    assert score_bracket_index(480) == 2
    assert win_loss_deltas(480) == (4, -4)


def test_clock_runs_only_for_the_current_player():
    white, black = make_match_setups()
    match = Match(white, black)

    match.tick(10)
    assert match.white_time == 230
    assert match.black_time == 240
    assert match.elapsed_seconds() == 10

    match.play_move((6, 0), (5, 0))
    match.tick(5)
    assert match.white_time == 230
    assert match.black_time == 235
    assert match.elapsed_seconds() == 15


def test_timeout_is_a_draw_with_penalty_for_flagged_player():
    white, black = make_match_setups()
    match = Match(white, black)

    result = match.tick(240)

    assert result is not None
    assert result.reason is EndReason.TIMEOUT
    assert result.winner is None
    assert result.loser is Color.WHITE
    assert result.white_points_delta == -3
    assert result.black_points_delta == 0
    assert match.white_time == 0


def test_black_can_time_out_after_its_turn_starts():
    white, black = make_match_setups()
    match = Match(white, black)

    match.tick(100)
    match.play_move((6, 0), (5, 0))
    result = match.tick(240)

    assert result is not None
    assert result.loser is Color.BLACK
    assert result.black_points_delta == -3
    assert result.white_points_delta == 0


def test_resignation_scores_the_current_minute():
    white, black = make_match_setups()
    match = Match(white, black)
    match.tick(121)

    result = match.resign(Color.BLACK)

    assert result.reason is EndReason.RESIGN
    assert result.winner is Color.WHITE
    assert result.loser is Color.BLACK
    assert result.white_points_delta == 7
    assert result.black_points_delta == -7


def test_resignation_in_fast_bracket_gives_ten_points():
    white, black = make_match_setups()
    match = Match(white, black)

    result = match.resign(Color.WHITE)

    assert result.winner is Color.BLACK
    assert result.white_points_delta == -10
    assert result.black_points_delta == 10


def test_stalemate_is_a_zero_point_draw():
    white, black = make_match_setups()
    match = Match(white, black)

    match.board.squares = [[None for _ in range(8)] for _ in range(8)]
    king = empty_piece(Color.BLACK, PieceType.KING, 7, 7)
    pawn_a = empty_piece(Color.BLACK, PieceType.PAWN, 7, 6, "a")
    pawn_b = empty_piece(Color.BLACK, PieceType.PAWN, 6, 6, "b")
    pawn_c = empty_piece(Color.BLACK, PieceType.PAWN, 6, 7, "c")
    for piece in (king, pawn_a, pawn_b, pawn_c):
        match.board.add_piece(piece)
    match.turn = Color.BLACK

    result = match.check_stalemate()

    assert result is not None
    assert result.reason is EndReason.STALEMATE
    assert result.winner is None
    assert result.white_points_delta == 0
    assert result.black_points_delta == 0


def test_threefold_repetition_ends_in_draw():
    white, black = make_match_setups()
    match = Match(white, black)

    def cycle() -> None:
        match.play_move((6, 5), (4, 4))
        match.play_move((0, 5), (2, 4))
        match.play_move((4, 4), (6, 5))
        match.play_move((2, 4), (0, 5))

    cycle()
    cycle()

    assert match.result is not None
    assert match.result.reason is EndReason.REPETITION
    assert match.result.white_points_delta == 0
    assert match.result.black_points_delta == 0


def test_cannot_tick_after_game_over():
    white, black = make_match_setups()
    match = Match(white, black)
    match.resign(Color.WHITE)

    assert match.tick(100) is match.result
    assert match.white_time == 240

