"""Cálculo de niveles a partir de los puntos acumulados."""

from __future__ import annotations

from dataclasses import dataclass

from game import constants as rules


@dataclass(frozen=True)
class Level:
    index: int
    name: str
    min_points: int
    max_points: int | None

    @property
    def next_min_points(self) -> int | None:
        if self.index + 1 >= len(LEVELS):
            return None
        return LEVELS[self.index + 1].min_points


def _build_levels() -> tuple[Level, ...]:
    return tuple(
        Level(index=index, name=name, min_points=minimum, max_points=maximum)
        for index, (name, minimum, maximum) in enumerate(rules.LEVEL_DEFINITIONS)
    )


LEVELS = _build_levels()
COMPOTA_LEVEL = next(
    level for level in LEVELS if level.name == rules.COMPOTA_LEVEL_NAME
)


def level_for_points(points: int, compota_locked: bool = False) -> Level:
    if compota_locked or points >= rules.COMPOTA_THRESHOLD:
        return COMPOTA_LEVEL
    safe_points = max(points, 0)
    for level in LEVELS:
        if level.max_points is None or safe_points <= level.max_points:
            if safe_points >= level.min_points:
                return level
    return LEVELS[0]


def points_to_next_level(points: int, compota_locked: bool = False) -> int | None:
    level = level_for_points(points, compota_locked)
    if level.next_min_points is None:
        return None
    return max(level.next_min_points - max(points, 0), 0)
