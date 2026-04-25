from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.config import AppConfig
from ac_server_gui.core.network_info import get_lan_ip, read_ports_from_cfg
from ac_server_gui.core.server_process import ServerProcess, ServerState
from ac_server_gui.widgets.log_viewer import LogViewer
from ac_server_gui.widgets.preset_picker import PresetPicker
from ac_server_gui.widgets.status_panel import StatusPanel


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config
        self._server = ServerProcess(self)

        self.setWindowTitle("AC Server GUI")
        self.resize(1200, 700)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.setCentralWidget(splitter)

        # --- Left panel ---
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left.setMinimumWidth(280)
        left.setMaximumWidth(400)

        left_layout.addWidget(QLabel("Preset:"))
        self._preset_picker = PresetPicker(self._config.presets_dir, left)
        left_layout.addWidget(self._preset_picker)

        btn_row = QHBoxLayout()
        self._btn_start = QPushButton("Start")
        self._btn_stop = QPushButton("Stop")
        self._btn_stop.setEnabled(False)
        btn_row.addWidget(self._btn_start)
        btn_row.addWidget(self._btn_stop)
        left_layout.addLayout(btn_row)

        left_layout.addSpacing(8)
        self._status_panel = StatusPanel(left)
        left_layout.addWidget(self._status_panel)

        left_layout.addSpacing(12)
        left_layout.addWidget(QLabel("LAN Info:"))
        self._lan_label = QLabel("—")
        self._lan_label.setWordWrap(True)
        self._lan_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        left_layout.addWidget(self._lan_label)

        left_layout.addStretch()
        splitter.addWidget(left)

        # --- Right panel (log viewer) ---
        self._log_viewer = LogViewer(self._config.logs_dir, self)
        splitter.addWidget(self._log_viewer)
        splitter.setStretchFactor(1, 3)

    def _connect_signals(self) -> None:
        self._btn_start.clicked.connect(self._on_start)
        self._btn_stop.clicked.connect(self._on_stop)
        self._server.output_line.connect(self._on_output_line)
        self._server.state_changed.connect(self._on_state_changed)

    def _on_start(self) -> None:
        preset = self._preset_picker.selected_preset()
        if not preset:
            QMessageBox.warning(self, "No preset", "Please select a preset first.")
            return

        preset_path = self._config.presets_dir / preset
        try:
            ip = get_lan_ip()
            ports = read_ports_from_cfg(preset_path)
            self._lan_label.setText(
                f"IP: {ip}\nTCP: {ports.tcp}  UDP: {ports.udp}  HTTP: {ports.http}"
            )
        except Exception:
            self._lan_label.setText("(could not read ports)")

        self._log_viewer.clear_log()
        self._log_viewer.start_log_file()
        self._server.start(self._config.server_exe, preset, self._config.server_dir)
        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)

    def _on_stop(self) -> None:
        self._server.stop()

    def _on_output_line(self, line: str) -> None:
        self._log_viewer.append_line(line)

    def _on_state_changed(self, state: ServerState) -> None:
        self._status_panel.update_state(state)
        stopped = state in (ServerState.STOPPED, ServerState.CRASHED)
        self._btn_start.setEnabled(stopped)
        self._btn_stop.setEnabled(not stopped)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._server.state not in (ServerState.STOPPED, ServerState.CRASHED):
            reply = QMessageBox.question(
                self,
                "Server is running",
                "The server is still running. What would you like to do?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            # Yes = Stop and close, No = Leave running, Cancel = abort close
            if reply == QMessageBox.StandardButton.Yes:
                self._server.stop()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        event.accept()
