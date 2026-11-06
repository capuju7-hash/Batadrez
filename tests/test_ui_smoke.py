"""Fase 5: prueba de humo de las pantallas pygame en modo sin ventana."""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game import constants as rules
from game.pieces import Color
from tests.helpers import make_setup
from ui.app import App


def test_all_screens_draw_and_flow_completes(tmp_path, monkeypatch):
    monkeypatch.setattr(rules, "PROFILES_FILE", tmp_path / "profiles.json")
    app = App()
    try:
        ana = app.profile_manager.create("Ana")
        beto = app.profile_manager.create("Beto")
        app.profile_manager.apply_points(ana.profile_id, 64)
        app.profile_manager.apply_points(beto.profile_id, 900)

        app.screen.draw(app.canvas)
        app.show_profiles()
        app.screen.draw(app.canvas)
        app.screen._open_create()
        app.screen.name_text = "Carla"
        app.screen.draw(app.canvas)
        app.screen._close_create()
        app.screen.selected_id = ana.profile_id
        app.screen.delete_open = True
        app.screen.draw(app.canvas)
        app.screen.delete_open = False
        app.show_lobby()
        app.screen.draw(app.canvas)

        app.begin_match_setup(ana.profile_id, beto.profile_id)
        app.screen.draw(app.canvas)
        app.screen.on_continue()
        app.screen.draw(app.canvas)

        app.register_setup(make_setup(Color.WHITE))
        app.screen.draw(app.canvas)
        app.screen.on_continue()
        app.screen.draw(app.canvas)
        app.register_setup(make_setup(Color.BLACK))
        app.screen.draw(app.canvas)

        match_screen = app.screen
        assert len(match_screen.match.board.all_pieces()) == 18
        match_screen.match.resign(match_screen.match.turn)
        match_screen._open_result()
        app.screen.draw(app.canvas)

        app.show_ranking()
        app.screen.draw(app.canvas)
        app.show_menu()
        app.screen.draw(app.canvas)
    finally:
        pygame.quit()

