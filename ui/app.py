"""Aplicación pygame y navegación entre pantallas."""

from __future__ import annotations

import random

import pygame

from game.match import Match
from game.pieces import Color
from game.profiles import ProfileError, ProfileManager, ProfileStorageError
from game.setup import Setup
from ui.theme import (
    FPS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    draw_apple,
)


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Batadrez — el civil es secreto")
        self.window = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE
        )
        self.canvas = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.mouse_position = (0, 0)
        self.profile_manager = ProfileManager()
        self._text_input_active = False
        self.screen = None

        self.match_white_id: str | None = None
        self.match_black_id: str | None = None
        self.white_setup: Setup | None = None
        self.black_setup: Setup | None = None
        self.result_processed = False

        self._set_icon()
        self.show_menu()

    def _set_icon(self) -> None:
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        draw_apple(icon, (16, 18), 11)
        pygame.display.set_icon(icon)

    def set_screen(self, screen) -> None:
        if self._text_input_active:
            self.stop_text_input()
        self.screen = screen

    def start_text_input(self) -> None:
        self._text_input_active = True
        pygame.key.start_text_input()

    def stop_text_input(self) -> None:
        self._text_input_active = False
        pygame.key.stop_text_input()

    def quit(self) -> None:
        self.running = False

    def show_menu(self) -> None:
        from ui.menu import MenuScreen

        self.set_screen(MenuScreen(self))

    def show_profiles(self, message: str | None = None) -> None:
        from ui.profiles import ProfilesScreen

        self.set_screen(ProfilesScreen(self, message))

    def show_lobby(self) -> None:
        from ui.lobby import LobbyScreen

        self.set_screen(LobbyScreen(self))

    def show_ranking(self) -> None:
        from ui.ranking import RankingScreen

        self.set_screen(RankingScreen(self))

    def begin_match_setup(self, player_one_id: str, player_two_id: str) -> None:
        first = self.profile_manager.require(player_one_id)
        second = self.profile_manager.require(player_two_id)
        if first.profile_id == second.profile_id:
            self.show_lobby()
            return

        if random.choice((True, False)):
            white_id, black_id = first.profile_id, second.profile_id
        else:
            white_id, black_id = second.profile_id, first.profile_id
        self.match_white_id = white_id
        self.match_black_id = black_id
        self.white_setup = None
        self.black_setup = None
        self.result_processed = False
        self._show_relay_for_setup(Color.WHITE, first_setup=True)

    def _show_relay_for_setup(self, color: Color, first_setup: bool = False) -> None:
        from ui.relay import RelayScreen

        profile = self.profile_manager.require(
            self.match_white_id if color is Color.WHITE else self.match_black_id
        )
        if first_setup:
            title = "Preparación de blancas"
            message = (
                f"Pasa el equipo a {profile.name}. Va a colocar sus 9 piezas y a elegir "
                "su civil en secreto. El otro jugador no debe mirar."
            )
            button = "Comenzar preparación secreta"
        else:
            white = self.profile_manager.require(self.match_white_id)
            title = "Pasa el equipo"
            message = (
                f"Las blancas ya escondieron su civil. {white.name} no debe mirar ahora. "
                f"Entrega el equipo a {profile.name} para preparar a las negras."
            )
            button = "Preparar negras"
        self.set_screen(
            RelayScreen(
                self,
                title=title,
                player_name=profile.name,
                message=message,
                button_label=button,
                on_continue=lambda: self.show_setup(color),
            )
        )

    def show_setup(self, color: Color) -> None:
        from ui.setup import SetupScreen

        profile_id = (
            self.match_white_id if color is Color.WHITE else self.match_black_id
        )
        if profile_id is None:
            self.show_menu()
            return
        profile = self.profile_manager.require(profile_id)
        self.set_screen(SetupScreen(self, profile, color))

    def register_setup(self, setup: Setup) -> None:
        if setup.color is Color.WHITE:
            self.white_setup = setup
            self._show_relay_for_setup(Color.BLACK)
        else:
            self.black_setup = setup
            self.show_match()

    def show_match(self) -> None:
        from ui.match import MatchScreen

        if self.white_setup is None or self.black_setup is None:
            self.show_menu()
            return
        if self.match_white_id is None or self.match_black_id is None:
            self.show_menu()
            return
        match = Match(self.white_setup, self.black_setup)
        white_profile = self.profile_manager.require(self.match_white_id)
        black_profile = self.profile_manager.require(self.match_black_id)
        self.result_processed = False
        self.set_screen(
            MatchScreen(self, match, white_profile, black_profile)
        )

    def finish_match(self, match: Match) -> None:
        from ui.result import ResultScreen

        if self.result_processed:
            return
        self.result_processed = True
        result = match.result
        if result is None:
            self.show_menu()
            return
        if self.match_white_id is None or self.match_black_id is None:
            self.show_menu()
            return

        updates = []
        save_error = None
        try:
            updates = self.profile_manager.apply_many(
                [
                    (self.match_white_id, result.white_points_delta),
                    (self.match_black_id, result.black_points_delta),
                ]
            )
        except (ProfileError, ProfileStorageError) as exc:
            save_error = f"No se pudieron guardar los puntos: {exc}"

        white_profile = self.profile_manager.require(self.match_white_id)
        black_profile = self.profile_manager.require(self.match_black_id)
        self.set_screen(
            ResultScreen(
                self,
                match,
                white_profile,
                black_profile,
                updates,
                save_error=save_error,
            )
        )

    def rematch(self) -> None:
        if self.match_white_id is None or self.match_black_id is None:
            self.show_lobby()
            return
        current_white = self.match_white_id
        current_black = self.match_black_id
        if (
            self.profile_manager.get(current_white) is None
            or self.profile_manager.get(current_black) is None
        ):
            self.show_lobby()
            return
        self.begin_match_setup(current_white, current_black)

    def run(self) -> None:
        while self.running:
            delta_seconds = min(self.clock.tick(FPS) / 1000.0, 1.0)
            self.mouse_position = self._to_canvas(pygame.mouse.get_pos())
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.VIDEORESIZE:
                    width = max(800, event.w)
                    height = max(600, event.h)
                    self.window = pygame.display.set_mode(
                        (width, height), pygame.RESIZABLE
                    )
                else:
                    if event.type in (
                        pygame.MOUSEMOTION,
                        pygame.MOUSEBUTTONDOWN,
                        pygame.MOUSEBUTTONUP,
                    ):
                        self.mouse_position = self._to_canvas(event.pos)
                    if self.screen is not None:
                        self.screen.handle_event(event)

            if self.screen is not None:
                self.screen.update(delta_seconds)
                self.screen.draw(self.canvas)
            self._present()
            pygame.display.flip()

        pygame.quit()

    def _viewport(self) -> tuple[int, int, int, int]:
        window_width, window_height = self.window.get_size()
        scale = min(window_width / WINDOW_WIDTH, window_height / WINDOW_HEIGHT)
        draw_width = max(1, int(WINDOW_WIDTH * scale))
        draw_height = max(1, int(WINDOW_HEIGHT * scale))
        offset_x = (window_width - draw_width) // 2
        offset_y = (window_height - draw_height) // 2
        return draw_width, draw_height, offset_x, offset_y

    def _to_canvas(self, position: tuple[int, int]) -> tuple[int, int]:
        draw_width, draw_height, offset_x, offset_y = self._viewport()
        if draw_width <= 0 or draw_height <= 0:
            return (0, 0)
        x = (position[0] - offset_x) * WINDOW_WIDTH / draw_width
        y = (position[1] - offset_y) * WINDOW_HEIGHT / draw_height
        return (int(x), int(y))

    def _present(self) -> None:
        draw_width, draw_height, offset_x, offset_y = self._viewport()
        self.window.fill((0, 0, 0))
        if (draw_width, draw_height) == (WINDOW_WIDTH, WINDOW_HEIGHT):
            scaled = self.canvas
        else:
            scaled = pygame.transform.smoothscale(
                self.canvas, (draw_width, draw_height)
            )
        self.window.blit(scaled, (offset_x, offset_y))

