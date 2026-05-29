"""JSON-backed user settings for the mini player."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


def default_settings_path() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) / "DesktopTransMusic" if appdata else Path.home() / ".desktop_trans_music"
    return base / "config.json"


SETTINGS_PATH = default_settings_path()


@dataclass(frozen=True)
class PlayerSettings:
    repeat_mode: int = 0
    volume: int = 70
    muted: bool = False


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _sanitize(data: dict[str, Any]) -> PlayerSettings:
    repeat_mode = _coerce_int(data.get("repeat_mode"), PlayerSettings.repeat_mode)
    if repeat_mode not in (0, 1, 2):
        repeat_mode = PlayerSettings.repeat_mode

    volume = max(0, min(100, _coerce_int(data.get("volume"), PlayerSettings.volume)))
    muted = data.get("muted") is True
    return PlayerSettings(repeat_mode=repeat_mode, volume=volume, muted=muted)


def load_settings(path: Path | None = None) -> PlayerSettings:
    settings_path = path or SETTINGS_PATH
    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return PlayerSettings()
    if not isinstance(raw, dict):
        return PlayerSettings()
    return _sanitize(raw)


def save_settings(settings: PlayerSettings, path: Path | None = None) -> None:
    settings_path = path or SETTINGS_PATH
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = settings_path.with_suffix(settings_path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp_path.replace(settings_path)
