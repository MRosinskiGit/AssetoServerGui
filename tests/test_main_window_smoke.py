from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QMessageBox
from pytestqt.qtbot import QtBot

from ac_server_gui.core.config import AppConfig
from ac_server_gui.main_window import MainWindow


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    presets_dir = tmp_path / "presets"
    presets_dir.mkdir()
    (presets_dir / "TEST_PRESET").mkdir()
    (presets_dir / "TEST_PRESET" / "server_cfg.ini").write_text(
        "[SERVER]\nTCP_PORT=9600\nUDP_PORT=9600\nHTTP_PORT=8081\n", encoding="utf-8"
    )
    return AppConfig(
        server_exe=Path("acServer.exe"),
        server_dir=tmp_path,
        presets_dir=presets_dir,
        content_dir=tmp_path,
        logs_dir=tmp_path / "logs",
    )


def test_window_opens(qtbot: QtBot, config: AppConfig) -> None:
    window = MainWindow(config)
    qtbot.addWidget(window)
    window.show()
    assert window.isVisible()


def test_start_without_preset_shows_warning(
    qtbot: QtBot, config: AppConfig, mocker: MagicMock
) -> None:
    window = MainWindow(config)
    qtbot.addWidget(window)
    window._preset_picker.clear()

    mock_warning = mocker.patch.object(
        QMessageBox,
        "warning",
        return_value=QMessageBox.StandardButton.Ok,
    )
    window._on_start()
    mock_warning.assert_called_once()


def test_log_viewer_accepts_lines(qtbot: QtBot, config: AppConfig) -> None:
    window = MainWindow(config)
    qtbot.addWidget(window)
    window.show()

    window._log_viewer.append_line(
        "2026-04-24 21:09:27.418 +02:00 [INF] Starting server"
    )
    window._log_viewer.append_line(
        "2026-04-24 21:09:29.938 +02:00 [INF]"
        " Starting update loop with an update rate of 18hz"
    )
    doc_text = window._log_viewer.toPlainText()
    assert "Starting server" in doc_text
    assert "Starting update loop" in doc_text
