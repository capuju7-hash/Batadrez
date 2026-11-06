"""Interfaz base para las pantallas."""

from __future__ import annotations

import pygame


class BaseScreen:
    def __init__(self, app) -> None:
        self.app = app

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, delta_seconds: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError
