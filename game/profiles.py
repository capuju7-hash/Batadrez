"""Perfiles locales, puntos y persistencia en JSON."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from game import constants as rules
from game.levels import Level, level_for_points, points_to_next_level


class ProfileError(ValueError):
    pass


class DuplicateProfileError(ProfileError):
    pass


class ProfileStorageError(OSError):
    pass


@dataclass
class Profile:
    profile_id: str
    name: str
    points: int = 0
    compota_locked: bool = False

    @property
    def level(self) -> Level:
        return level_for_points(self.points, self.compota_locked)

    @property
    def points_to_next(self) -> int | None:
        return points_to_next_level(self.points, self.compota_locked)

    def to_dict(self) -> dict:
        return {
            "id": self.profile_id,
            "name": self.name,
            "points": self.points,
            "compota_locked": self.compota_locked,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        try:
            profile_id = str(data["id"]).strip()
            name = str(data["name"]).strip()
            points = data["points"]
            compota_locked = bool(data.get("compota_locked", False))
        except (KeyError, TypeError, ValueError) as exc:
            raise ProfileError("Perfil con campos inválidos.") from exc

        if not profile_id or not name:
            raise ProfileError("El perfil necesita identificador y nombre.")
        if len(name) > rules.MAX_PROFILE_NAME_LENGTH:
            raise ProfileError("El nombre del perfil es demasiado largo.")
        if isinstance(points, bool) or not isinstance(points, int):
            raise ProfileError("Los puntos del perfil deben ser un entero.")

        if rules.POINTS_NEVER_BELOW_ZERO:
            points = max(points, 0)
        if points >= rules.COMPOTA_THRESHOLD:
            compota_locked = True
        return cls(
            profile_id=profile_id,
            name=name,
            points=points,
            compota_locked=compota_locked,
        )


@dataclass(frozen=True)
class ProfileUpdate:
    profile: Profile
    points_delta: int
    before_level: Level
    after_level: Level

    @property
    def leveled_up(self) -> bool:
        return self.after_level.index > self.before_level.index


class ProfileManager:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else rules.PROFILES_FILE
        self.profiles: list[Profile] = []
        self.load_error: str | None = None
        self.load()

    def load(self) -> None:
        self.profiles = []
        self.load_error = None
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                entries = raw.get("profiles", [])
            elif isinstance(raw, list):
                entries = raw
            else:
                raise ProfileError("La raíz del archivo no es válida.")
            if not isinstance(entries, list):
                raise ProfileError("La lista de perfiles no es válida.")

            loaded: list[Profile] = []
            seen_ids: set[str] = set()
            seen_names: set[str] = set()
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ProfileError("Hay un perfil con formato inválido.")
                profile = Profile.from_dict(entry)
                name_key = profile.name.casefold()
                if profile.profile_id in seen_ids or name_key in seen_names:
                    raise ProfileError("Hay identificadores o nombres duplicados.")
                seen_ids.add(profile.profile_id)
                seen_names.add(name_key)
                loaded.append(profile)
            self.profiles = loaded
        except (OSError, json.JSONDecodeError, ProfileError, TypeError) as exc:
            backup_message = self._backup_corrupt_file()
            self.profiles = []
            self.load_error = (
                "No se pudo leer el archivo de perfiles. "
                "Se creó una copia de seguridad y se empezó de cero."
            )
            if backup_message:
                self.load_error += f" {backup_message}"
            if not isinstance(exc, (json.JSONDecodeError, ProfileError)):
                self.load_error += f" Detalle: {exc}"

    def _backup_corrupt_file(self) -> str:
        if not self.path.exists():
            return ""
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = self.path.with_name(f"{self.path.stem}.corrupt-{stamp}{self.path.suffix}")
        try:
            self.path.replace(backup)
            return f"Copia: {backup.name}."
        except OSError:
            return ""

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "profiles": [profile.to_dict() for profile in self.profiles],
        }
        temporary = self.path.with_name(f"{self.path.name}.tmp")
        try:
            temporary.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(temporary, self.path)
        except OSError as exc:
            try:
                if temporary.exists():
                    temporary.unlink()
            except OSError:
                pass
            raise ProfileStorageError(
                "No se pudo guardar el archivo de perfiles."
            ) from exc

    def get(self, profile_id: str) -> Profile | None:
        for profile in self.profiles:
            if profile.profile_id == profile_id:
                return profile
        return None

    def require(self, profile_id: str) -> Profile:
        profile = self.get(profile_id)
        if profile is None:
            raise ProfileError("El perfil no existe.")
        return profile

    def create(self, name: str) -> Profile:
        clean_name = name.strip()
        if not clean_name:
            raise ProfileError("El nombre no puede estar vacío.")
        if len(clean_name) > rules.MAX_PROFILE_NAME_LENGTH:
            raise ProfileError(
                f"El nombre puede tener como máximo {rules.MAX_PROFILE_NAME_LENGTH} caracteres."
            )
        if any(
            profile.name.casefold() == clean_name.casefold()
            for profile in self.profiles
        ):
            raise DuplicateProfileError("Ya existe un perfil con ese nombre.")

        profile = Profile(
            profile_id=uuid.uuid4().hex,
            name=clean_name,
        )
        self.profiles.append(profile)
        try:
            self.save()
        except Exception:
            self.profiles.remove(profile)
            raise
        return profile

    def delete(self, profile_id: str) -> None:
        profile = self.require(profile_id)
        index = self.profiles.index(profile)
        self.profiles.remove(profile)
        try:
            self.save()
        except Exception:
            self.profiles.insert(index, profile)
            raise

    def apply_many(self, changes: list[tuple[str, int]]) -> list[ProfileUpdate]:
        """Aplica varios cambios y guarda una sola vez, con rollback si falla."""

        originals = {
            profile.profile_id: (profile.points, profile.compota_locked)
            for profile in self.profiles
        }
        updates: list[ProfileUpdate] = []
        try:
            for profile_id, delta in changes:
                profile = self.require(profile_id)
                before_level = profile.level
                before_points = profile.points
                new_points = profile.points + delta
                if rules.POINTS_NEVER_BELOW_ZERO:
                    new_points = max(new_points, 0)
                profile.points = new_points

                if (
                    rules.COMPOTA_PREVENTS_DESCENT
                    and profile.points >= rules.COMPOTA_THRESHOLD
                ):
                    profile.compota_locked = True

                updates.append(
                    ProfileUpdate(
                        profile=profile,
                        points_delta=profile.points - before_points,
                        before_level=before_level,
                        after_level=profile.level,
                    )
                )
            self.save()
            return updates
        except Exception:
            for profile in self.profiles:
                if profile.profile_id in originals:
                    profile.points, profile.compota_locked = originals[profile.profile_id]
            raise

    def apply_points(self, profile_id: str, delta: int) -> ProfileUpdate:
        return self.apply_many([(profile_id, delta)])[0]

    def ranking(self) -> list[Profile]:
        return sorted(
            self.profiles,
            key=lambda profile: (-profile.points, profile.name.casefold()),
        )

