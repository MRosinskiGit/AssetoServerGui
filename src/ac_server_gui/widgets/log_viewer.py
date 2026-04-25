from __future__ import annotations

import datetime
from pathlib import Path

from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QWidget

from ac_server_gui.core.log_parser import EventType, LogEvent, LogLevel, classify_line

MAX_LINES = 5000

_LEVEL_COLORS: dict[LogLevel, str] = {
    LogLevel.INFO: "#DDDDDD",
    LogLevel.DEBUG: "#888888",
    LogLevel.WARNING: "#FFA500",
    LogLevel.ERROR: "#FF4444",
    LogLevel.UNKNOWN: "#AAAAAA",
}

_EVENT_COLORS: dict[EventType, str | None] = {
    EventType.READY: "#00CC44",
    EventType.PLAYER_JOIN: "#44AAFF",
    EventType.PLAYER_LEAVE: "#FF8844",
    EventType.ERROR: "#FF4444",
    EventType.INFO: None,  # fall back to level color
    EventType.UNKNOWN: None,
}


class LogViewer(QPlainTextEdit):
    def __init__(self, logs_dir: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(MAX_LINES)
        self._logs_dir = logs_dir
        self._log_file: Path | None = None
        self._auto_scroll = True

        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def start_log_file(self) -> None:
        self._logs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log_file = self._logs_dir / f"server_{ts}.log"

    def append_line(self, line: str) -> None:
        event = classify_line(line)
        self._append_event(event)
        if self._log_file is not None:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def _append_event(self, event: LogEvent) -> None:
        color_hex = _EVENT_COLORS.get(event.event_type)
        if color_hex is None:
            color_hex = _LEVEL_COLORS.get(event.level, "#AAAAAA")

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_hex))

        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self.document().isEmpty():
            cursor.insertText("\n")
        cursor.insertText(event.raw, fmt)

        if self._auto_scroll:
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def _on_scroll(self, value: int) -> None:
        at_bottom = value >= self.verticalScrollBar().maximum() - 4
        self._auto_scroll = at_bottom

    def clear_log(self) -> None:
        self.clear()
        self._log_file = None
        self._auto_scroll = True
