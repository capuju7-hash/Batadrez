"""Partida: turnos, relojes, finales y puntuación."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from game import constants as rules
from game.board import Board, InvalidMoveError, Position
from game.pieces import Color, Piece
from game.setup import InvalidSetupError, Setup


class GameOverError(RuntimeError):
    pass


class EndReason(Enum):
    CIVIL_CAPTURED = "civil_captured"
    TIMEOUT = "timeout"
    STALEMATE = "stalemate"
    REPETITION = "repetition"
    RESIGN = "resign"


@dataclass(frozen=True)
class CaptureEvent:
    capturing_color: Color
    captured_piece: Piece
    is_civil: bool


@dataclass(frozen=True)
class MoveOutcome:
    moving_piece: Piece
    start: Position
    destination: Position
    captured_piece: Piece | None
    capture_event: CaptureEvent | None
    result: "MatchResult | None"


@dataclass(frozen=True)
class MatchResult:
    reason: EndReason
    winner: Color | None
    loser: Color | None
    elapsed_seconds: float
    white_points_delta: int
    black_points_delta: int
    white_civil: Piece
    black_civil: Piece

    def points_delta_for(self, color: Color) -> int:
        return (
            self.white_points_delta
            if color is Color.WHITE
            else self.black_points_delta
        )


def score_bracket_index(elapsed_seconds: float) -> int:
    """Devuelve 0 (hasta 2:00), 1 (hasta 5:00) o 2 (5:01 en adelante)."""

    for index, limit in enumerate(rules.SCORE_BRACKET_LIMITS_SECONDS):
        if elapsed_seconds <= limit:
            return index
    return len(rules.SCORE_BRACKET_LIMITS_SECONDS)


def win_loss_deltas(elapsed_seconds: float) -> tuple[int, int]:
    bracket = score_bracket_index(elapsed_seconds)
    return (
        rules.WIN_POINTS_BY_BRACKET[bracket],
        rules.LOSS_POINTS_BY_BRACKET[bracket],
    )


class Match:
    def __init__(
        self,
        white_setup: Setup,
        black_setup: Setup,
        clock_seconds: int | float = rules.CLOCK_START_SECONDS,
    ) -> None:
        if white_setup.color is not Color.WHITE:
            raise InvalidSetupError("La preparación blanca tiene un color incorrecto.")
        if black_setup.color is not Color.BLACK:
            raise InvalidSetupError("La preparación negra tiene un color incorrecto.")
        white_setup.validate()
        black_setup.validate()

        self.initial_clock_seconds = float(clock_seconds)
        self.white_time = float(clock_seconds)
        self.black_time = float(clock_seconds)
        self.turn = Color.WHITE
        self.result: MatchResult | None = None
        self.last_capture: CaptureEvent | None = None
        self.capture_events: list[CaptureEvent] = []

        self.board = Board()
        for piece in white_setup.clone().pieces + black_setup.clone().pieces:
            piece.initial_row = piece.row
            piece.initial_col = piece.col
            self.board.add_piece(piece)

        self.white_civil_id = white_setup.civil_id
        self.black_civil_id = black_setup.civil_id
        self.white_civil_piece = self._find_piece(self.white_civil_id)
        self.black_civil_piece = self._find_piece(self.black_civil_id)

        self._position_counts: dict[tuple, int] = {}
        self._record_position()
        self.check_stalemate()

    def _find_piece(self, piece_id: str) -> Piece:
        for piece in self.board.all_pieces():
            if piece.piece_id == piece_id:
                return piece
        raise InvalidSetupError("No se encontró el civil en el tablero.")

    @property
    def is_over(self) -> bool:
        return self.result is not None

    def remaining_for(self, color: Color) -> float:
        return self.white_time if color is Color.WHITE else self.black_time

    def elapsed_seconds(self) -> float:
        elapsed = (
            self.initial_clock_seconds * 2
            - self.white_time
            - self.black_time
        )
        return max(0.0, elapsed)

    def tick(self, delta_seconds: float) -> MatchResult | None:
        if self.result is not None or delta_seconds <= 0:
            return self.result

        if self.turn is Color.WHITE:
            self.white_time = max(0.0, self.white_time - delta_seconds)
            timed_out = self.white_time <= 0.0
        else:
            self.black_time = max(0.0, self.black_time - delta_seconds)
            timed_out = self.black_time <= 0.0

        if timed_out:
            self._finish_timeout(self.turn)
        return self.result

    def play_move(self, start: Position, destination: Position) -> MoveOutcome:
        if self.result is not None:
            raise GameOverError("La partida ya terminó.")
        piece = self.board.piece_at(*start)
        if piece is None:
            raise InvalidMoveError("No hay una pieza en la casilla de origen.")
        if piece.color is not self.turn:
            raise InvalidMoveError("No es el turno de esa pieza.")

        captured = self.board.move(start, destination)
        capture_event: CaptureEvent | None = None
        if captured is not None:
            opponent_civil_id = (
                self.black_civil_id
                if self.turn is Color.WHITE
                else self.white_civil_id
            )
            is_civil = captured.piece_id == opponent_civil_id
            capture_event = CaptureEvent(
                capturing_color=self.turn,
                captured_piece=captured,
                is_civil=is_civil,
            )
            self.last_capture = capture_event
            self.capture_events.append(capture_event)
            if is_civil:
                self._finish_with_winner(
                    winner=self.turn,
                    loser=self.turn.opponent,
                    reason=EndReason.CIVIL_CAPTURED,
                )
                return MoveOutcome(
                    moving_piece=piece,
                    start=start,
                    destination=destination,
                    captured_piece=captured,
                    capture_event=capture_event,
                    result=self.result,
                )

        self.turn = self.turn.opponent
        self._record_position()
        if self._position_counts[self._position_key()] >= 3:
            self._finish_draw(EndReason.REPETITION)
        else:
            self.check_stalemate()

        return MoveOutcome(
            moving_piece=piece,
            start=start,
            destination=destination,
            captured_piece=captured,
            capture_event=capture_event,
            result=self.result,
        )

    def check_stalemate(self) -> MatchResult | None:
        if self.result is None and not self.board.has_any_move(self.turn):
            self._finish_draw(EndReason.STALEMATE)
        return self.result

    def resign(self, color: Color) -> MatchResult:
        if self.result is not None:
            return self.result
        self._finish_with_winner(
            winner=color.opponent,
            loser=color,
            reason=EndReason.RESIGN,
        )
        return self.result  # type: ignore[return-value]

    def _position_key(self) -> tuple:
        return (self.board.position_key(), self.turn.value)

    def _record_position(self) -> None:
        key = self._position_key()
        self._position_counts[key] = self._position_counts.get(key, 0) + 1

    def _finish_timeout(self, flagged_color: Color) -> None:
        white_delta = 0
        black_delta = 0
        if flagged_color is Color.WHITE:
            white_delta = rules.TIMEOUT_PENALTY
        else:
            black_delta = rules.TIMEOUT_PENALTY
        self.result = MatchResult(
            reason=EndReason.TIMEOUT,
            winner=None,
            loser=flagged_color,
            elapsed_seconds=self.elapsed_seconds(),
            white_points_delta=white_delta,
            black_points_delta=black_delta,
            white_civil=self.white_civil_piece.clone(),
            black_civil=self.black_civil_piece.clone(),
        )

    def _finish_with_winner(
        self, winner: Color, loser: Color, reason: EndReason
    ) -> None:
        win_points, loss_points = win_loss_deltas(self.elapsed_seconds())
        white_delta = 0
        black_delta = 0
        if winner is Color.WHITE:
            white_delta = win_points
            black_delta = loss_points
        else:
            black_delta = win_points
            white_delta = loss_points
        self.result = MatchResult(
            reason=reason,
            winner=winner,
            loser=loser,
            elapsed_seconds=self.elapsed_seconds(),
            white_points_delta=white_delta,
            black_points_delta=black_delta,
            white_civil=self.white_civil_piece.clone(),
            black_civil=self.black_civil_piece.clone(),
        )

    def _finish_draw(self, reason: EndReason) -> None:
        self.result = MatchResult(
            reason=reason,
            winner=None,
            loser=None,
            elapsed_seconds=self.elapsed_seconds(),
            white_points_delta=0,
            black_points_delta=0,
            white_civil=self.white_civil_piece.clone(),
            black_civil=self.black_civil_piece.clone(),
        )
