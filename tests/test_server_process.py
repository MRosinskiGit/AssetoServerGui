from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication

from ac_server_gui.core.server_process import ServerProcess, ServerState


@pytest.fixture
def app(qapp: QCoreApplication) -> QCoreApplication:
    return qapp


def test_start_calls_qprocess(app: QCoreApplication, mocker: MagicMock) -> None:
    proc = ServerProcess()
    mock_qproc = mocker.patch.object(proc._process, "start")
    mocker.patch.object(proc._process, "setWorkingDirectory")

    exe = Path("C:/server/acServer.exe")
    proc.start(exe, "SERVER_01", Path("C:/server"))

    proc._process.setWorkingDirectory.assert_called_once_with(  # type: ignore[attr-defined]
        str(Path("C:/server"))
    )
    mock_qproc.assert_called_once_with(
        str(Path("C:/server/acServer.exe")), ["-p", "SERVER_01"]
    )
    assert proc.state == ServerState.STARTING


def test_start_ignored_when_already_running(
    app: QCoreApplication, mocker: MagicMock
) -> None:
    proc = ServerProcess()
    mocker.patch.object(proc._process, "start")
    mocker.patch.object(proc._process, "setWorkingDirectory")

    proc._state = ServerState.RUNNING
    proc.start(Path("x.exe"), "P", Path("."))
    proc._process.start.assert_not_called()  # type: ignore[attr-defined]


def test_stop_terminate_then_kill(app: QCoreApplication, mocker: MagicMock) -> None:
    proc = ServerProcess()
    proc._state = ServerState.RUNNING
    mocker.patch.object(proc._process, "terminate")
    mocker.patch.object(proc._process, "waitForFinished", return_value=False)
    mocker.patch.object(proc._process, "kill")

    proc.stop(timeout_s=1)

    proc._process.terminate.assert_called_once()  # type: ignore[attr-defined]
    proc._process.waitForFinished.assert_called_once_with(1000)  # type: ignore[attr-defined]
    proc._process.kill.assert_called_once()  # type: ignore[attr-defined]


def test_stop_no_kill_when_terminates(app: QCoreApplication, mocker: MagicMock) -> None:
    proc = ServerProcess()
    proc._state = ServerState.RUNNING
    mocker.patch.object(proc._process, "terminate")
    mocker.patch.object(proc._process, "waitForFinished", return_value=True)
    mocker.patch.object(proc._process, "kill")

    proc.stop()

    proc._process.kill.assert_not_called()  # type: ignore[attr-defined]


def test_stop_ignored_when_stopped(app: QCoreApplication, mocker: MagicMock) -> None:
    proc = ServerProcess()
    mocker.patch.object(proc._process, "terminate")
    proc.stop()
    proc._process.terminate.assert_not_called()  # type: ignore[attr-defined]


def test_state_changed_signal(app: QCoreApplication) -> None:
    proc = ServerProcess()
    states: list[ServerState] = []
    proc.state_changed.connect(lambda s: states.append(s))
    proc._set_state(ServerState.RUNNING)
    assert states == [ServerState.RUNNING]


def test_state_changed_not_emitted_for_same_state(app: QCoreApplication) -> None:
    proc = ServerProcess()
    states: list[ServerState] = []
    proc.state_changed.connect(lambda s: states.append(s))
    proc._set_state(ServerState.STOPPED)  # already STOPPED
    assert states == []


def test_output_line_emitted_per_line(app: QCoreApplication) -> None:
    proc = ServerProcess()
    lines: list[str] = []
    proc.output_line.connect(lines.append)
    proc._emit_lines(b"line one\nline two\npartial")
    assert lines == ["line one", "line two"]
    assert proc._buf == b"partial"


def test_output_line_strips_crlf(app: QCoreApplication) -> None:
    proc = ServerProcess()
    lines: list[str] = []
    proc.output_line.connect(lines.append)
    proc._emit_lines(b"line one\r\nline two\r\n")
    assert lines == ["line one", "line two"]


def test_ready_line_transitions_to_running(app: QCoreApplication) -> None:
    proc = ServerProcess()
    proc._state = ServerState.STARTING
    states: list[ServerState] = []
    proc.state_changed.connect(lambda s: states.append(s))
    ready = (
        b"2026-04-24 21:09:29.938 +02:00 [INF]"
        b" Starting update loop with an update rate of 18hz\n"
    )
    proc._emit_lines(ready)
    assert ServerState.RUNNING in states
