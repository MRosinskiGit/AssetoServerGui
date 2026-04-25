from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ac_server_gui.core.server_process import ServerState

_STATE_COLORS: dict[ServerState, str] = {
    ServerState.STOPPED: "#888888",
    ServerState.STARTING: "#FFA500",
    ServerState.RUNNING: "#00CC44",
    ServerState.CRASHED: "#CC2200",
}


class StatusPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._dot = QLabel("●", self)
        self._dot.setFixedWidth(20)
        self._label = QLabel(ServerState.STOPPED.value, self)

        layout.addWidget(self._dot)
        layout.addWidget(self._label)

        self.update_state(ServerState.STOPPED)

    def update_state(self, state: ServerState) -> None:
        color = _STATE_COLORS[state]
        self._dot.setStyleSheet(f"color: {color}; font-size: 16px;")
        self._label.setText(state.value)
        self._label.setStyleSheet(f"color: {color}; font-weight: bold;")
