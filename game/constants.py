"""Constantes configurables de Batadrez.

Este es el único archivo donde deben ajustarse las reglas numéricas del juego.
El motor no importa pygame.
"""

from pathlib import Path

BOARD_SIZE = 8
SET_SIZE = 9
PIECE_COUNTS = {
    "king": 1,
    "queen": 1,
    "rook": 1,
    "bishop": 2,
    "knight": 2,
    "pawn": 2,
}
WHITE_HOME_ROWS = (6, 7)
BLACK_HOME_ROWS = (0, 1)
HOME_ROWS_BY_COLOR = {
    "white": WHITE_HOME_ROWS,
    "black": BLACK_HOME_ROWS,
}
PAWN_LAST_ROW_BY_COLOR = {
    "white": 0,
    "black": 7,
}
PAWN_FORWARD_BY_COLOR = {
    "white": -1,
    "black": 1,
}

PAWN_CAN_MOVE_TWO = False
CIVIL_CAN_BE_PAWN = True

CLOCK_START_SECONDS = 4 * 60


SCORE_BRACKET_LIMITS_SECONDS = (120, 300)
WIN_POINTS_BY_BRACKET = (10, 7, 4)
LOSS_POINTS_BY_BRACKET = (-10, -7, -4)
TIMEOUT_PENALTY = -3

LEVEL_DEFINITIONS = (
    ("Semilla", 0, 64),
    ("Árbol", 65, 144),
    ("Fruta", 145, 215),
    ("Manzana", 216, 900),
    ("Compota de Manzana", 901, None),
)
COMPOTA_LEVEL_NAME = "Compota de Manzana"
COMPOTA_THRESHOLD = 901
POINTS_NEVER_BELOW_ZERO = True
COMPOTA_PREVENTS_DESCENT = True


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROFILES_FILE = PROJECT_ROOT / "profiles.json"
MAX_PROFILE_NAME_LENGTH = 24
