"""Colores, tipografía y dibujo de elementos comunes."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from game.constants import BOARD_SIZE
from game.pieces import Color, Piece, PieceType

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
FPS = 60

BOARD_X = 64
BOARD_Y = 146
SQUARE_SIZE = 68
BOARD_PIXELS = BOARD_SIZE * SQUARE_SIZE

# Paleta general
BG_TOP = (31, 23, 37)
BG_BOTTOM = (12, 10, 16)
PANEL = (44, 34, 52)
PANEL_LIGHT = (57, 45, 66)
PANEL_DARK = (28, 21, 34)
TEXT = (247, 241, 231)
MUTED = (178, 164, 184)
MUTED_DARK = (120, 105, 128)
ACCENT = (215, 62, 79)
ACCENT_HOVER = (235, 82, 96)
GOLD = (236, 190, 91)
GOLD_DARK = (166, 122, 45)
GREEN = (96, 181, 123)
GREEN_DARK = (46, 113, 70)
RED_DARK = (125, 37, 50)
BORDER = (88, 71, 99)
BOARD_LIGHT = (237, 218, 191)
BOARD_DARK = (135, 96, 77)
WHITE_PIECE = (250, 244, 228)
BLACK_PIECE = (45, 38, 53)
WHITE_LETTER = (62, 45, 32)
BLACK_LETTER = (240, 233, 246)

LEVEL_COLORS = [
    (130, 165, 107),
    (103, 155, 117),
    (189, 151, 71),
    (207, 77, 77),
    (230, 157, 57),
]

BACKGROUND: pygame.Surface | None = None
_FONT_CACHE: dict[tuple[int, bool], pygame.font.Font] = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont("segoeui,arial", size, bold=bold)
    return _FONT_CACHE[key]


def _build_background() -> pygame.Surface:
    surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    for y in range(WINDOW_HEIGHT):
        ratio = y / max(WINDOW_HEIGHT - 1, 1)
        color = tuple(
            int(BG_TOP[index] + (BG_BOTTOM[index] - BG_TOP[index]) * ratio)
            for index in range(3)
        )
        pygame.draw.line(surface, color, (0, y), (WINDOW_WIDTH, y))

    glow = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(glow, (175, 48, 70, 24), (1060, 90), 310)
    pygame.draw.circle(glow, (222, 171, 63, 16), (160, 760), 360)
    pygame.draw.circle(glow, (88, 132, 92, 14), (1200, 690), 260)
    surface.blit(glow, (0, 0))
    return surface


def draw_background(surface: pygame.Surface) -> None:
    global BACKGROUND
    if BACKGROUND is None:
        BACKGROUND = _build_background()
    surface.blit(BACKGROUND, (0, 0))


def draw_text(
    surface: pygame.Surface,
    text: str,
    size: int,
    color: tuple[int, int, int],
    position: tuple[int, int],
    anchor: str = "topleft",
    bold: bool = False,
) -> pygame.Rect:
    rendered = get_font(size, bold).render(text, True, color)
    rect = rendered.get_rect()
    anchors = {
        "topleft": "topleft",
        "topright": "topright",
        "midleft": "midleft",
        "midright": "midright",
        "center": "center",
        "bottomleft": "bottomleft",
        "bottomright": "bottomright",
        "midtop": "midtop",
        "midbottom": "midbottom",
    }
    setattr(rect, anchors.get(anchor, "topleft"), position)
    surface.blit(rendered, rect)
    return rect


def draw_wrapped_text(
    surface: pygame.Surface,
    text: str,
    size: int,
    color: tuple[int, int, int],
    rect: pygame.Rect,
    line_spacing: int = 5,
    bold: bool = False,
    center: bool = False,
) -> int:
    font = get_font(size, bold)
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= rect.width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    y = rect.top
    for line in lines:
        rendered = font.render(line, True, color)
        if center:
            surface.blit(rendered, rendered.get_rect(center=(rect.centerx, y + rendered.get_height() // 2)))
        else:
            surface.blit(rendered, (rect.left, y))
        y += rendered.get_height() + line_spacing
    return y


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int] = PANEL,
    radius: int = 18,
    border: tuple[int, int, int] | None = None,
    shadow: bool = True,
) -> None:
    if shadow:
        shadow_rect = rect.move(0, 5)
        pygame.draw.rect(surface, (9, 7, 12), shadow_rect, border_radius=radius)
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border is not None:
        pygame.draw.rect(surface, border, rect, width=2, border_radius=radius)


def draw_progress_bar(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fraction: float,
    fill: tuple[int, int, int] = GOLD,
    background: tuple[int, int, int] = PANEL_DARK,
) -> None:
    fraction = max(0.0, min(1.0, fraction))
    pygame.draw.rect(surface, background, rect, border_radius=rect.height // 2)
    if fraction > 0:
        width = max(rect.height, int(rect.width * fraction))
        fill_rect = pygame.Rect(rect.left, rect.top, min(width, rect.width), rect.height)
        pygame.draw.rect(surface, fill, fill_rect, border_radius=rect.height // 2)


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    variant: str = "primary"
    font_size: int = 26
    enabled: bool = True

    def hovered(self, mouse_position: tuple[int, int]) -> bool:
        return self.rect.collidepoint(mouse_position)

    def draw(
        self,
        surface: pygame.Surface,
        mouse_position: tuple[int, int],
        selected: bool = False,
    ) -> None:
        hover = self.enabled and self.hovered(mouse_position)
        if not self.enabled:
            fill = (72, 63, 78)
            text_color = (132, 121, 139)
            border = None
        elif self.variant == "primary":
            fill = ACCENT_HOVER if hover else ACCENT
            text_color = TEXT
            border = GOLD if selected else None
        elif self.variant == "danger":
            fill = (169, 48, 62) if hover else RED_DARK
            text_color = TEXT
            border = GOLD if selected else None
        elif self.variant == "ghost":
            fill = PANEL_LIGHT if hover else PANEL
            text_color = TEXT
            border = GOLD if selected else BORDER
        else:
            fill = (78, 62, 88) if hover else PANEL_LIGHT
            text_color = TEXT
            border = GOLD if selected else None

        if hover:
            pygame.draw.rect(
                surface, (8, 6, 11), self.rect.move(0, 4), border_radius=12
            )
        pygame.draw.rect(surface, fill, self.rect, border_radius=12)
        if border is not None:
            pygame.draw.rect(surface, border, self.rect, width=2, border_radius=12)
        elif hover:
            pygame.draw.rect(
                surface, (255, 255, 255, 35), self.rect, width=1, border_radius=12
            )
        draw_text(
            surface,
            self.label,
            self.font_size,
            text_color,
            self.rect.center,
            anchor="center",
            bold=True,
        )


def draw_apple(
    surface: pygame.Surface,
    center: tuple[int, int],
    radius: int,
    color: tuple[int, int, int] = ACCENT,
) -> None:
    x, y = center
    pygame.draw.circle(surface, color, (x, y + radius // 8), radius)
    pygame.draw.circle(
        surface,
        (int(color[0] * 0.72), int(color[1] * 0.72), int(color[2] * 0.72)),
        (x - radius // 3, y + radius // 4),
        max(3, radius // 7),
    )
    pygame.draw.ellipse(
        surface,
        (97, 151, 93),
        pygame.Rect(x + radius // 5, y - radius - radius // 5, radius // 2, radius // 3),
    )
    pygame.draw.line(
        surface,
        (109, 76, 48),
        (x, y - radius + 2),
        (x + radius // 6, y - radius - radius // 4),
        max(2, radius // 10),
    )


def draw_piece_token(
    surface: pygame.Surface,
    piece: Piece,
    center: tuple[int, int],
    radius: int = 26,
    highlight: bool = False,
    show_civil: bool = False,
) -> None:
    shadow = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
    pygame.draw.circle(
        shadow,
        (0, 0, 0, 80),
        (radius + 4, radius + 6),
        radius,
    )
    surface.blit(shadow, (center[0] - radius - 4, center[1] - radius - 4))

    if piece.color is Color.WHITE:
        fill = WHITE_PIECE
        border = (104, 78, 55)
        letter_color = WHITE_LETTER
    else:
        fill = BLACK_PIECE
        border = (170, 151, 183)
        letter_color = BLACK_LETTER

    if highlight:
        pygame.draw.circle(surface, GOLD, center, radius + 4)
    pygame.draw.circle(surface, border, center, radius)
    pygame.draw.circle(surface, fill, center, radius - 3)
    letter = {
        PieceType.KING: "R",
        PieceType.QUEEN: "D",
        PieceType.ROOK: "T",
        PieceType.BISHOP: "A",
        PieceType.KNIGHT: "C",
        PieceType.PAWN: "P",
    }[piece.kind]
    draw_text(
        surface,
        letter,
        max(15, int(radius * 1.1)),
        letter_color,
        center,
        anchor="center",
        bold=True,
    )
    if show_civil:
        pygame.draw.circle(surface, GOLD, (center[0] + radius - 5, center[1] - radius + 4), 6)
        pygame.draw.circle(surface, (91, 64, 22), (center[0] + radius - 5, center[1] - radius + 4), 6, 2)


def board_cell_rect(row: int, col: int, origin: tuple[int, int] = (BOARD_X, BOARD_Y)) -> pygame.Rect:
    x, y = origin
    return pygame.Rect(x + col * SQUARE_SIZE, y + row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)


def cell_from_mouse(
    position: tuple[int, int], origin: tuple[int, int] = (BOARD_X, BOARD_Y)
) -> tuple[int, int] | None:
    x, y = origin
    local_x = position[0] - x
    local_y = position[1] - y
    if local_x < 0 or local_y < 0:
        return None
    col = local_x // SQUARE_SIZE
    row = local_y // SQUARE_SIZE
    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
        return int(row), int(col)
    return None


def draw_board(
    surface: pygame.Surface,
    origin: tuple[int, int] = (BOARD_X, BOARD_Y),
    highlight_rows: tuple[int, ...] = (),
) -> None:
    x, y = origin
    outer = pygame.Rect(x - 12, y - 12, BOARD_PIXELS + 24, BOARD_PIXELS + 24)
    pygame.draw.rect(surface, (22, 15, 25), outer.move(0, 5), border_radius=12)
    pygame.draw.rect(surface, (67, 49, 57), outer, border_radius=12)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            rect = board_cell_rect(row, col, origin)
            color = BOARD_LIGHT if (row + col) % 2 == 0 else BOARD_DARK
            if row in highlight_rows:
                color = tuple(min(255, channel + 18) for channel in color)
            pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(
        surface, (29, 20, 29), pygame.Rect(x, y, BOARD_PIXELS, BOARD_PIXELS), width=2
    )

    for col in range(BOARD_SIZE):
        label = chr(ord("a") + col)
        draw_text(
            surface,
            label,
            15,
            MUTED,
            (x + col * SQUARE_SIZE + SQUARE_SIZE // 2, y + BOARD_PIXELS + 16),
            anchor="center",
            bold=True,
        )
    for row in range(BOARD_SIZE):
        label = str(BOARD_SIZE - row)
        draw_text(
            surface,
            label,
            15,
            MUTED,
            (x - 22, y + row * SQUARE_SIZE + SQUARE_SIZE // 2),
            anchor="center",
            bold=True,
        )


def square_name(row: int, col: int) -> str:
    return f"{chr(ord('a') + col)}{BOARD_SIZE - row}"


def format_clock(seconds: float) -> str:
    whole = max(0, int(math.ceil(seconds)))
    minutes, secs = divmod(whole, 60)
    return f"{minutes}:{secs:02d}"


def format_elapsed(seconds: float) -> str:
    whole = max(0, int(seconds))
    minutes, secs = divmod(whole, 60)
    return f"{minutes}:{secs:02d}"


def format_points(delta: int) -> str:
    return f"{delta:+d}" if delta else "0"


def truncate_text(text: str, size: int, max_width: int, bold: bool = False) -> str:
    font = get_font(size, bold)
    if font.size(text)[0] <= max_width:
        return text
    suffix = "…"
    while text and font.size(text + suffix)[0] > max_width:
        text = text[:-1]
    return text + suffix


def level_color(level_index: int) -> tuple[int, int, int]:
    return LEVEL_COLORS[min(level_index, len(LEVEL_COLORS) - 1)]

