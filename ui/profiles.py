"""Pantalla de perfiles: alta, baja y estado de cada jugador."""

from __future__ import annotations

import pygame

from game.constants import MAX_PROFILE_NAME_LENGTH
from game.profiles import ProfileError, ProfileStorageError
from ui.base import BaseScreen
from ui.theme import (
    ACCENT,
    BORDER,
    GOLD,
    MUTED,
    PANEL,
    PANEL_DARK,
    PANEL_LIGHT,
    TEXT,
    Button,
    draw_background,
    draw_panel,
    draw_progress_bar,
    draw_text,
    draw_wrapped_text,
    format_points,
    get_font,
    level_color,
    truncate_text,
)


class ProfilesScreen(BaseScreen):
    ROW_HEIGHT = 70
    VISIBLE_ROWS = 7

    def __init__(self, app, message: str | None = None) -> None:
        super().__init__(app)
        self.message = message
        self.selected_id: str | None = None
        self.scroll = 0
        self.create_open = False
        self.delete_open = False
        self.name_text = ""
        self.dialog_error = ""
        self.caret_time = 0.0
        self.buttons = {
            "create": Button(pygame.Rect(90, 668, 230, 54), "Crear perfil"),
            "delete": Button(
                pygame.Rect(336, 668, 270, 54),
                "Eliminar seleccionado",
                variant="danger",
            ),
            "ranking": Button(
                pygame.Rect(622, 668, 200, 54), "Ver ranking", variant="ghost"
            ),
            "back": Button(
                pygame.Rect(1040, 668, 150, 54), "Volver", variant="ghost"
            ),
        }
        self.list_rect = pygame.Rect(104, 148, 1072, 505)
        self.modal_panel = pygame.Rect(320, 218, 640, 350)
        self.field_rect = pygame.Rect(370, 336, 540, 58)
        self.create_button = Button(pygame.Rect(370, 458, 250, 52), "Crear")
        self.cancel_button = Button(
            pygame.Rect(660, 458, 250, 52), "Cancelar", variant="ghost"
        )
        self.delete_panel = pygame.Rect(360, 260, 560, 270)
        self.confirm_delete = Button(
            pygame.Rect(408, 448, 220, 52), "Sí, eliminar", variant="danger"
        )
        self.cancel_delete = Button(
            pygame.Rect(652, 448, 220, 52), "Cancelar", variant="ghost"
        )

    @property
    def profiles(self):
        return self.app.profile_manager.profiles

    def _open_create(self) -> None:
        self.create_open = True
        self.name_text = ""
        self.dialog_error = ""
        self.app.start_text_input()

    def _close_create(self) -> None:
        self.create_open = False
        self.dialog_error = ""
        self.app.stop_text_input()

    def _create_profile(self) -> None:
        try:
            profile = self.app.profile_manager.create(self.name_text)
        except (ProfileError, ProfileStorageError) as exc:
            self.dialog_error = str(exc)
            return
        self.selected_id = profile.profile_id
        self.message = f"Perfil «{profile.name}» creado."
        self._close_create()

    def _delete_profile(self) -> None:
        if not self.selected_id:
            return
        try:
            self.app.profile_manager.delete(self.selected_id)
        except (ProfileError, ProfileStorageError) as exc:
            self.message = str(exc)
            self.delete_open = False
            return
        self.selected_id = None
        self.delete_open = False
        self.message = "Perfil eliminado."
        self.scroll = min(self.scroll, max(0, len(self.profiles) - self.VISIBLE_ROWS))

    def _row_rects(self) -> list[tuple[int, pygame.Rect]]:
        rows = []
        start = self.scroll
        for visible_index in range(self.VISIBLE_ROWS):
            index = start + visible_index
            if index >= len(self.profiles):
                break
            rect = pygame.Rect(
                self.list_rect.left + 14,
                self.list_rect.top + 14 + visible_index * self.ROW_HEIGHT,
                self.list_rect.width - 28,
                60,
            )
            rows.append((index, rect))
        return rows

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.create_open:
            self._handle_create_event(event)
            return
        if self.delete_open:
            self._handle_delete_event(event)
            return

        if event.type == pygame.MOUSEWHEEL:
            maximum = max(0, len(self.profiles) - self.VISIBLE_ROWS)
            self.scroll = max(0, min(self.scroll - event.y, maximum))
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.app.mouse_position
            for index, rect in self._row_rects():
                if rect.collidepoint(mouse):
                    self.selected_id = self.profiles[index].profile_id
                    self.message = None
                    return
            if self.buttons["create"].rect.collidepoint(mouse):
                self._open_create()
            elif self.buttons["delete"].rect.collidepoint(mouse):
                if self.selected_id:
                    self.delete_open = True
                else:
                    self.message = "Selecciona un perfil para eliminarlo."
            elif self.buttons["ranking"].rect.collidepoint(mouse):
                self.app.show_ranking()
            elif self.buttons["back"].rect.collidepoint(mouse):
                self.app.show_menu()

    def _handle_create_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.TEXTINPUT and len(self.name_text) < MAX_PROFILE_NAME_LENGTH:
            self.name_text = (self.name_text + event.text)[:MAX_PROFILE_NAME_LENGTH]
            self.dialog_error = ""
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.name_text = self.name_text[:-1]
            elif event.key == pygame.K_RETURN:
                self._create_profile()
            elif event.key == pygame.K_ESCAPE:
                self._close_create()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.app.mouse_position
            if self.create_button.rect.collidepoint(mouse):
                self._create_profile()
            elif self.cancel_button.rect.collidepoint(mouse):
                self._close_create()

    def _handle_delete_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = self.app.mouse_position
            if self.confirm_delete.rect.collidepoint(mouse):
                self._delete_profile()
            elif self.cancel_delete.rect.collidepoint(mouse):
                self.delete_open = False

    def update(self, delta_seconds: float) -> None:
        self.caret_time += delta_seconds

    def draw(self, surface: pygame.Surface) -> None:
        draw_background(surface)
        draw_text(surface, "Perfiles", 44, TEXT, (64, 28), bold=True)
        draw_text(
            surface,
            "Los puntos se guardan en esta computadora y definen el nivel de cada jugador.",
            19,
            MUTED,
            (64, 83),
        )
        notice = self.message or self.app.profile_manager.load_error
        if notice:
            draw_wrapped_text(
                surface,
                notice,
                16,
                GOLD,
                pygame.Rect(64, 108, 1150, 34),
                line_spacing=2,
            )

        draw_panel(surface, self.list_rect)
        if not self.profiles:
            draw_text(
                surface,
                "Todavía no hay perfiles. Crea el primero para empezar.",
                24,
                MUTED,
                self.list_rect.center,
                anchor="center",
            )
        else:
            for index, rect in self._row_rects():
                self._draw_row(surface, self.profiles[index], rect, index)
            if len(self.profiles) > self.VISIBLE_ROWS:
                self._draw_scrollbar(surface)

        self.buttons["delete"].enabled = self.selected_id is not None
        for button in self.buttons.values():
            button.draw(surface, self.app.mouse_position)

        if self.create_open:
            self._draw_create_modal(surface)
        if self.delete_open:
            self._draw_delete_modal(surface)

    def _draw_row(self, surface: pygame.Surface, profile, rect: pygame.Rect, index: int) -> None:
        selected = profile.profile_id == self.selected_id
        fill = PANEL_LIGHT if selected else PANEL_DARK
        pygame.draw.rect(surface, fill, rect, border_radius=12)
        border = GOLD if selected else (63, 51, 72)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=12)

        name = truncate_text(profile.name, 24, 300, bold=True)
        draw_text(surface, name, 24, TEXT, (rect.left + 22, rect.centery), anchor="midleft", bold=True)

        level = profile.level
        badge = pygame.Rect(rect.left + 370, rect.centery - 15, 205, 30)
        pygame.draw.rect(surface, level_color(level.index), badge, border_radius=15)
        draw_text(
            surface,
            level.name,
            16,
            (20, 17, 22),
            badge.center,
            anchor="center",
            bold=True,
        )

        draw_text(
            surface,
            f"{profile.points} pts",
            21,
            TEXT,
            (rect.left + 605, rect.centery),
            anchor="midleft",
            bold=True,
        )

        if level.next_min_points is None:
            fraction = 1.0
            next_text = "Nivel máximo"
        else:
            span = max(level.next_min_points - level.min_points, 1)
            fraction = (profile.points - level.min_points) / span
            next_text = f"Faltan {profile.points_to_next} pts"
        bar = pygame.Rect(rect.left + 735, rect.centery - 6, 210, 12)
        draw_progress_bar(surface, bar, fraction, fill=level_color(level.index))
        draw_text(
            surface,
            next_text,
            15,
            MUTED,
            (bar.left, rect.centery + 17),
        )
        draw_text(
            surface,
            f"#{index + 1}",
            15,
            (122, 106, 130),
            (rect.right - 24, rect.centery),
            anchor="midright",
            bold=True,
        )

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        track = pygame.Rect(self.list_rect.right - 13, self.list_rect.top + 18, 5, 470)
        pygame.draw.rect(surface, PANEL_DARK, track, border_radius=3)
        maximum = max(1, len(self.profiles) - self.VISIBLE_ROWS)
        thumb_height = max(42, int(track.height * self.VISIBLE_ROWS / max(len(self.profiles), 1)))
        travel = track.height - thumb_height
        thumb_y = track.top + int(travel * self.scroll / maximum)
        pygame.draw.rect(
            surface,
            BORDER,
            pygame.Rect(track.left, thumb_y, track.width, thumb_height),
            border_radius=3,
        )

    def _draw_overlay(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((8, 6, 11, 190))
        surface.blit(overlay, (0, 0))

    def _draw_create_modal(self, surface: pygame.Surface) -> None:
        self._draw_overlay(surface)
        draw_panel(surface, self.modal_panel, color=PANEL, radius=20, border=BORDER)
        draw_text(
            surface,
            "Nuevo perfil",
            32,
            TEXT,
            (self.modal_panel.centerx, self.modal_panel.top + 35),
            anchor="center",
            bold=True,
        )
        draw_text(
            surface,
            "Escribe el nombre del jugador.",
            18,
            MUTED,
            (self.modal_panel.centerx, self.modal_panel.top + 79),
            anchor="center",
        )
        focused = self.field_rect.collidepoint(self.app.mouse_position)
        pygame.draw.rect(surface, PANEL_DARK, self.field_rect, border_radius=10)
        pygame.draw.rect(
            surface,
            GOLD if focused else BORDER,
            self.field_rect,
            width=2,
            border_radius=10,
        )
        font = get_font(25)
        text_surface = font.render(self.name_text, True, TEXT)
        surface.blit(text_surface, (self.field_rect.left + 16, self.field_rect.centery - text_surface.get_height() // 2))
        if int(self.caret_time * 2) % 2 == 0:
            caret_x = self.field_rect.left + 16 + text_surface.get_width() + 2
            pygame.draw.line(
                surface,
                TEXT,
                (caret_x, self.field_rect.centery - 17),
                (caret_x, self.field_rect.centery + 17),
                2,
            )

        if self.dialog_error:
            draw_text(
                surface,
                self.dialog_error,
                16,
                GOLD,
                (self.modal_panel.centerx, self.field_rect.bottom + 20),
                anchor="center",
            )
        self.create_button.enabled = bool(self.name_text.strip())
        self.create_button.draw(surface, self.app.mouse_position)
        self.cancel_button.draw(surface, self.app.mouse_position)

    def _draw_delete_modal(self, surface: pygame.Surface) -> None:
        self._draw_overlay(surface)
        draw_panel(surface, self.delete_panel, color=PANEL, radius=20, border=BORDER)
        profile = self.app.profile_manager.get(self.selected_id or "")
        name = profile.name if profile else "este perfil"
        draw_text(
            surface,
            "Eliminar perfil",
            31,
            TEXT,
            (self.delete_panel.centerx, self.delete_panel.top + 42),
            anchor="center",
            bold=True,
        )
        draw_wrapped_text(
            surface,
            f"¿Seguro que quieres eliminar «{name}»? Sus puntos se perderán.",
            20,
            MUTED,
            pygame.Rect(
                self.delete_panel.left + 50,
                self.delete_panel.top + 90,
                self.delete_panel.width - 100,
                80,
            ),
            center=True,
        )
        self.confirm_delete.draw(surface, self.app.mouse_position)
        self.cancel_delete.draw(surface, self.app.mouse_position)



