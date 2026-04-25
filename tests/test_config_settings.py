from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ac_server_gui.core.config import load_config, save_config


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    p = tmp_path / "app_config.yml"
    p.write_text(
        "server_exe: C:/server/acServer.exe\n"
        "server_dir: C:/server\n"
        "presets_dir: C:/server/presets\n"
        "content_dir: C:/server/../content\n"
        "logs_dir: logs\n"
        "openweathermap_api_key: ''\n",
        encoding="utf-8",
    )
    return p


def test_load_config_default_key_is_empty(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert cfg.openweathermap_api_key == ""


def test_load_config_reads_existing_key(tmp_path: Path) -> None:
    p = tmp_path / "app_config.yml"
    p.write_text(
        "server_exe: C:/s/acServer.exe\n"
        "server_dir: C:/s\n"
        "presets_dir: C:/s/presets\n"
        "content_dir: C:/s/content\n"
        "logs_dir: logs\n"
        "openweathermap_api_key: 'mykey123'\n",
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg.openweathermap_api_key == "mykey123"


def test_save_config_writes_key(config_file: Path) -> None:
    cfg = load_config(config_file)
    cfg.openweathermap_api_key = "abc456"
    save_config(cfg, config_file)

    reloaded = load_config(config_file)
    assert reloaded.openweathermap_api_key == "abc456"


def test_save_config_preserves_other_fields(config_file: Path) -> None:
    cfg = load_config(config_file)
    cfg.openweathermap_api_key = "newkey"
    save_config(cfg, config_file)

    data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    assert data["server_exe"] == "C:/server/acServer.exe"
    assert data["presets_dir"] == "C:/server/presets"


def test_save_config_roundtrip(config_file: Path) -> None:
    cfg = load_config(config_file)
    cfg.openweathermap_api_key = "roundtrip_key"
    save_config(cfg, config_file)
    cfg2 = load_config(config_file)
    assert cfg2.openweathermap_api_key == "roundtrip_key"


def test_missing_key_field_defaults_to_empty(tmp_path: Path) -> None:
    p = tmp_path / "app_config.yml"
    p.write_text(
        "server_exe: C:/s/acServer.exe\n"
        "server_dir: C:/s\n"
        "presets_dir: C:/s/presets\n"
        "content_dir: C:/s/content\n"
        "logs_dir: logs\n",
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg.openweathermap_api_key == ""
