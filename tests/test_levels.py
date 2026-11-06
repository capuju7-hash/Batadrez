"""Fase 4: umbrales de niveles y bloqueo de Compota de Manzana."""

from __future__ import annotations

import pytest

from game.levels import level_for_points, points_to_next_level
from game.profiles import ProfileManager


@pytest.mark.parametrize(
    ("points", "expected"),
    [
        (0, "Semilla"),
        (64, "Semilla"),
        (65, "Árbol"),
        (144, "Árbol"),
        (145, "Fruta"),
        (215, "Fruta"),
        (216, "Manzana"),
        (900, "Manzana"),
        (901, "Compota de Manzana"),
        (2000, "Compota de Manzana"),
    ],
)
def test_level_thresholds(points, expected):
    assert level_for_points(points).name == expected


def test_points_to_next_level_at_each_boundary():
    assert points_to_next_level(64) == 1
    assert points_to_next_level(65) == 80
    assert points_to_next_level(144) == 1
    assert points_to_next_level(145) == 71
    assert points_to_next_level(215) == 1
    assert points_to_next_level(216) == 685
    assert points_to_next_level(900) == 1
    assert points_to_next_level(901) is None


def test_locked_compota_never_descends():
    assert level_for_points(100, compota_locked=True).name == "Compota de Manzana"
    assert points_to_next_level(100, compota_locked=True) is None


def test_profile_points_never_go_below_zero(tmp_path):
    manager = ProfileManager(tmp_path / "profiles.json")
    profile = manager.create("Ana")

    update = manager.apply_points(profile.profile_id, -50)

    assert profile.points == 0
    assert update.points_delta == 0
    assert update.after_level.name == "Semilla"


def test_reaching_compota_locks_level_even_after_losing_points(tmp_path):
    manager = ProfileManager(tmp_path / "profiles.json")
    profile = manager.create("Ana")

    manager.apply_points(profile.profile_id, 901)
    assert profile.points == 901
    assert profile.compota_locked is True
    assert profile.level.name == "Compota de Manzana"

    manager.apply_points(profile.profile_id, -500)
    assert profile.points == 401
    assert profile.level.name == "Compota de Manzana"

    manager.apply_points(profile.profile_id, -1000)
    assert profile.points == 0
    assert profile.level.name == "Compota de Manzana"


def test_level_up_is_reported(tmp_path):
    manager = ProfileManager(tmp_path / "profiles.json")
    profile = manager.create("Ana")
    manager.apply_points(profile.profile_id, 64)

    update = manager.apply_points(profile.profile_id, 1)

    assert update.leveled_up is True
    assert update.before_level.name == "Semilla"
    assert update.after_level.name == "Árbol"


def test_profiles_are_persisted_with_compota_lock(tmp_path):
    path = tmp_path / "profiles.json"
    manager = ProfileManager(path)
    profile = manager.create("Ana")
    manager.apply_points(profile.profile_id, 901)
    manager.apply_points(profile.profile_id, -800)

    reloaded = ProfileManager(path)
    loaded = reloaded.require(profile.profile_id)

    assert loaded.points == 101
    assert loaded.compota_locked is True
    assert loaded.level.name == "Compota de Manzana"


def test_ranking_sorts_by_points_then_name(tmp_path):
    manager = ProfileManager(tmp_path / "profiles.json")
    ana = manager.create("Ana")
    beto = manager.create("Beto")
    caro = manager.create("Caro")
    manager.apply_points(ana.profile_id, 10)
    manager.apply_points(beto.profile_id, 50)
    manager.apply_points(caro.profile_id, 50)

    ranking = manager.ranking()

    assert [profile.name for profile in ranking] == ["Beto", "Caro", "Ana"]


def test_damaged_profile_file_is_backed_up(tmp_path):
    path = tmp_path / "profiles.json"
    path.write_text("{esto no es json", encoding="utf-8")

    manager = ProfileManager(path)

    assert manager.profiles == []
    assert manager.load_error is not None
    assert list(tmp_path.glob("profiles.corrupt-*.json"))
    assert not path.exists()
