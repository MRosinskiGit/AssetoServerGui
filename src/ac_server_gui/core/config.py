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
    logs_dir: Path


def load_config(config_path: str | Path | None = None) -> AppConfig:
    if config_path is None:
        config_path = Path(__file__).parents[3] / "app_config.yml"
    config_path = Path(config_path)
    with open(config_path, encoding="utf-8") as f:
        data: dict[str, str] = yaml.safe_load(f)

    base = config_path.parent
    logs_raw = data.get("logs_dir", "logs")
    logs_path = Path(logs_raw) if os.path.isabs(logs_raw) else base / logs_raw

    return AppConfig(
        server_exe=Path(data["server_exe"]),
        server_dir=Path(data["server_dir"]),
        presets_dir=Path(data["presets_dir"]),
        logs_dir=logs_path,
    )
