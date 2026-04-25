from __future__ import annotations

from enum import Enum
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal

from ac_server_gui.core.log_parser import EventType, classify_line


class ServerState(Enum):
    STOPPED = "Stopped"
    STARTING = "Starting"
    RUNNING = "Running"
    CRASHED = "Crashed"


class ServerProcess(QObject):
    started = Signal()
    output_line = Signal(str)
    state_changed = Signal(object)  # ServerState
    finished = Signal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._process = QProcess(self)
        self._state = ServerState.STOPPED
        self._buf = b""

        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.started.connect(self._on_process_started)
        self._process.finished.connect(self._on_process_finished)

    @property
    def state(self) -> ServerState:
        return self._state

    def _set_state(self, new_state: ServerState) -> None:
        if new_state != self._state:
            self._state = new_state
            self.state_changed.emit(new_state)

    def start(self, exe_path: Path, preset_name: str, server_dir: Path) -> None:
        if self._state not in (ServerState.STOPPED, ServerState.CRASHED):
            return
        self._buf = b""
        self._process.setWorkingDirectory(str(server_dir))
        self._process.start(str(exe_path), ["-p", preset_name])
        self._set_state(ServerState.STARTING)

    def stop(self, timeout_s: int = 5) -> None:
        if self._state in (ServerState.STOPPED, ServerState.CRASHED):
            return
        self._process.terminate()
        if not self._process.waitForFinished(timeout_s * 1000):
            self._process.kill()

    def _emit_line(self, text: str) -> None:
        self.output_line.emit(text)
        if self._state == ServerState.STARTING:
            event = classify_line(text)
            if event.event_type == EventType.READY:
                self._set_state(ServerState.RUNNING)

    def _emit_lines(self, data: bytes) -> None:
        self._buf += data
        while b"\n" in self._buf:
            line, self._buf = self._buf.split(b"\n", 1)
            text = line.rstrip(b"\r").decode("utf-8", errors="replace")
            self._emit_line(text)

    def _on_stdout(self) -> None:
        raw = self._process.readAllStandardOutput().data()
        self._emit_lines(bytes(raw))

    def _on_stderr(self) -> None:
        raw = self._process.readAllStandardError().data()
        self._emit_lines(bytes(raw))

    def _on_process_started(self) -> None:
        self.started.emit()

    def _on_process_finished(self, exit_code: int, _exit_status: object) -> None:
        # Flush any remaining buffered bytes
        if self._buf:
            text = self._buf.rstrip(b"\r").decode("utf-8", errors="replace")
            self._buf = b""
            if text:
                self._emit_line(text)
        if exit_code == 0:
            self._set_state(ServerState.STOPPED)
        else:
            self._set_state(ServerState.CRASHED)
        self.finished.emit(exit_code)
