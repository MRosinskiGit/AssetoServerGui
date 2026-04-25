from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class AppConfig:
    server_exe: Path
    server_dir: Path
    presets_dir: Path
    content_dir: Path
    logs_dir: Path
    openweathermap_api_key: str = ""


def _config_path(config_path: str | Path | None) -> Path:
    if config_path is None:
        return Path(__file__).parents[3] / "app_config.yml"
    return Path(config_path)


def load_config(config_path: str | Path | None = None) -> AppConfig:
    path = _config_path(config_path)
    with open(path, encoding="utf-8") as f:
        data: dict[str, str] = yaml.safe_load(f)

    base = path.parent
    logs_raw = data.get("logs_dir", "logs")
    logs_path = Path(logs_raw) if os.path.isabs(logs_raw) else base / logs_raw

    return AppConfig(
        server_exe=Path(data["server_exe"]),
        server_dir=Path(data["server_dir"]),
        presets_dir=Path(data["presets_dir"]),
        content_dir=Path(data.get("content_dir", str(Path(data["server_dir"]).parent / "content"))),
        logs_dir=logs_path,
        openweathermap_api_key=str(data.get("openweathermap_api_key", "")),
    )


def save_config(config: AppConfig, config_path: str | Path | None = None) -> None:
    """Write the mutable fields of AppConfig back to app_config.yml."""
    path = _config_path(config_path)
    with open(path, encoding="utf-8") as f:
        data: dict[str, object] = yaml.safe_load(f) or {}
    data["openweathermap_api_key"] = config.openweathermap_api_key
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
