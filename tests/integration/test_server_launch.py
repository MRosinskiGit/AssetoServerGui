"""Integration test: actually launches acServer.exe."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from ac_server_gui.core.config import load_config
from ac_server_gui.core.preset_manager import copy_preset
from ac_server_gui.core.server_process import ServerProcess, ServerState

SERVER_01 = Path(
    "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/server/presets/SERVER_01"
)
PRESETS_DIR = Path(
    "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/server/presets"
)
TEST_PRESET_NAME = "SERVER_TEST_GUI"
TEST_PRESET_PATH = PRESETS_DIR / TEST_PRESET_NAME


@pytest.fixture
def test_preset() -> Path:  # type: ignore[return]
    copy_preset(SERVER_01, TEST_PRESET_PATH)
    yield TEST_PRESET_PATH  # type: ignore[misc]
    if TEST_PRESET_PATH.exists():
        shutil.rmtree(TEST_PRESET_PATH)


@pytest.mark.integration
def test_server_actually_launches(qtbot: QtBot, test_preset: Path) -> None:
    config = load_config()
    proc = ServerProcess()

    lines: list[str] = []
    states: list[ServerState] = []
    proc.output_line.connect(lines.append)
    proc.state_changed.connect(lambda s: states.append(s))

    proc.start(config.server_exe, TEST_PRESET_NAME, config.server_dir)
    assert proc.state == ServerState.STARTING

    def reached_running() -> None:
        assert ServerState.RUNNING in states, (
            f"Not yet RUNNING. States so far: {states}\n"
            f"Last 10 output lines:\n" + "\n".join(lines[-10:])
        )

    qtbot.waitUntil(reached_running, timeout=30_000)

    assert ServerState.RUNNING in states, (
        "Server never reached RUNNING state.\n"
        "First 50 output lines:\n" + "\n".join(lines[:50])
    )

    # Stop server
    proc.stop(timeout_s=10)

    def stopped() -> None:
        assert proc.state in (ServerState.STOPPED, ServerState.CRASHED)

    qtbot.waitUntil(stopped, timeout=12_000)

    assert proc.state in (ServerState.STOPPED, ServerState.CRASHED), (
        f"Unexpected state after stop: {proc.state}"
    )
