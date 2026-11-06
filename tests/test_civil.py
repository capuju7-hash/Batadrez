"""Fase 2: preparación, civil secreto y final por captura del civil."""

from __future__ import annotations

import pytest

from game import constants as rules
from game.match import EndReason, GameOverError, Match
from game.pieces import Color, PieceType
from game.setup import InvalidSetupError, Setup

from tests.helpers import make_capture_setups, make_setup


def test_valid_setup_has_nine_pieces_and_a_civil():
    setup = make_setup(Color.WHITE)

    assert len(setup.pieces) == 9
    assert setup.civil_piece.piece_id == setup.civil_id
    setup.validate()


def test_setup_rejects_piece_outside_home_rows():
    positions = [(5, 0)] + [(7, col) for col in range(1, 8)] + [(6, 0)]
    pieces = make_setup(Color.WHITE, positions, validate=False).pieces
    setup = Setup(Color.WHITE, pieces, pieces[0].piece_id)

    with pytest.raises(InvalidSetupError):
        setup.validate()


def test_setup_rejects_duplicate_squares():
    positions = [(7, 0)] * 2 + [(7, col) for col in range(2, 8)] + [(6, 0)]
    pieces = make_setup(Color.WHITE, positions, validate=False).pieces
    setup = Setup(Color.WHITE, pieces, pieces[0].piece_id)

    with pytest.raises(InvalidSetupError):
        setup.validate()


def test_setup_rejects_pawn_civil_when_disabled(monkeypatch):
    monkeypatch.setattr(rules, "CIVIL_CAN_BE_PAWN", False)
    pieces = make_setup(Color.WHITE, validate=False).pieces
    pawn = next(piece for piece in pieces if piece.kind is PieceType.PAWN)
    setup = Setup(Color.WHITE, pieces, pawn.piece_id)

    with pytest.raises(InvalidSetupError):
        setup.validate()


def test_capturing_the_civil_ends_the_match():
    white, black = make_capture_setups(black_civil_index=0)
    match = Match(white, black)

    outcome = match.play_move((6, 0), (1, 0))

    assert outcome.capture_event is not None
    assert outcome.capture_event.is_civil is True
    assert outcome.result is not None
    assert outcome.result.reason is EndReason.CIVIL_CAPTURED
    assert outcome.result.winner is Color.WHITE
    assert outcome.result.loser is Color.BLACK
    assert outcome.result.white_points_delta == 10
    assert outcome.result.black_points_delta == -10
    assert match.is_over is True


def test_capturing_a_non_civil_announces_and_continues():
    white, black = make_capture_setups(black_civil_index=1)
    match = Match(white, black)

    outcome = match.play_move((6, 0), (1, 0))

    assert outcome.capture_event is not None
    assert outcome.capture_event.is_civil is False
    assert outcome.result is None
    assert match.turn is Color.BLACK
    assert match.last_capture is not None
    assert match.last_capture.is_civil is False


def test_result_reveals_both_civils():
    white, black = make_capture_setups(black_civil_index=0)
    match = Match(white, black)

    outcome = match.play_move((6, 0), (1, 0))
    result = outcome.result

    assert result is not None
    assert result.white_civil.piece_id == white.civil_id
    assert result.black_civil.piece_id == black.civil_id


def test_cannot_move_after_match_finished():
    white, black = make_capture_setups(black_civil_index=0)
    match = Match(white, black)
    match.play_move((6, 0), (1, 0))

    with pytest.raises(GameOverError):
        match.play_move((7, 0), (6, 1))

