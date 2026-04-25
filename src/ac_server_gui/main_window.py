from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.config import AppConfig, save_config
from ac_server_gui.core.content_scanner import ContentScanner
from ac_server_gui.core.network_info import get_lan_ip, read_ports_from_cfg
from ac_server_gui.core.preset_manager import copy_preset
from ac_server_gui.core.server_process import ServerProcess, ServerState
from ac_server_gui.widgets.config_editor import ConfigEditor
from ac_server_gui.widgets.log_viewer import LogViewer
from ac_server_gui.widgets.preset_picker import PresetPicker
from ac_server_gui.widgets.status_panel import StatusPanel


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config
        self._server = ServerProcess(self)
        self._scanner = ContentScanner(config.content_dir)

        self.setWindowTitle("AC Server GUI")
        self.resize(1400, 800)

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------ UI build
    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.setCentralWidget(splitter)

        # ---- Left panel ----
        left = QWidget()
        left.setMinimumWidth(260)
        left.setMaximumWidth(380)
        left_layout = QVBoxLayout(left)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        left_layout.addWidget(QLabel("Preset:"))
        self._preset_picker = PresetPicker(self._config.presets_dir, left)
        left_layout.addWidget(self._preset_picker)

        # Preset management buttons
        preset_btns = QHBoxLayout()
        self._btn_new_preset = QPushButton("New")
        self._btn_copy_preset = QPushButton("Copy")
        self._btn_new_preset.setToolTip("Create new preset (copy of SERVER_01)")
        self._btn_copy_preset.setToolTip("Copy selected preset")
        preset_btns.addWidget(self._btn_new_preset)
        preset_btns.addWidget(self._btn_copy_preset)
        left_layout.addLayout(preset_btns)

        left_layout.addSpacing(8)

        # Start / Stop
        run_btns = QHBoxLayout()
        self._btn_start = QPushButton("▶  Start")
        self._btn_stop = QPushButton("■  Stop")
        self._btn_stop.setEnabled(False)
        run_btns.addWidget(self._btn_start)
        run_btns.addWidget(self._btn_stop)
        left_layout.addLayout(run_btns)

        left_layout.addSpacing(4)
        self._status_panel = StatusPanel(left)
        left_layout.addWidget(self._status_panel)

        left_layout.addSpacing(12)
        left_layout.addWidget(QLabel("LAN connection info:"))
        self._lan_label = QLabel("—")
        self._lan_label.setWordWrap(True)
        self._lan_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._lan_label.setStyleSheet("font-family: monospace; color: #AAA;")
        left_layout.addWidget(self._lan_label)

        left_layout.addStretch()

        self._btn_settings = QPushButton("⚙  Settings")
        left_layout.addWidget(self._btn_settings)

        splitter.addWidget(left)

        # ---- Right panel (tab widget) ----
        right_tabs = QTabWidget()

        self._log_viewer = LogViewer(self._config.logs_dir, self)
        right_tabs.addTab(self._log_viewer, "Monitor")

        self._config_editor = ConfigEditor(self._scanner, self)
        right_tabs.addTab(self._config_editor, "Configuration")

        splitter.addWidget(right_tabs)
        splitter.setStretchFactor(1, 3)

        # Push global API key into config editor, then load preset
        self._config_editor.set_global_api_key(self._config.openweathermap_api_key)
        self._on_preset_changed()

    # ------------------------------------------------------------------ signals
    def _connect_signals(self) -> None:
        self._btn_start.clicked.connect(self._on_start)
        self._btn_stop.clicked.connect(self._on_stop)
        self._btn_new_preset.clicked.connect(self._on_new_preset)
        self._btn_copy_preset.clicked.connect(self._on_copy_preset)
        self._btn_settings.clicked.connect(self._on_settings)
        self._preset_picker.currentTextChanged.connect(self._on_preset_changed)
        self._server.output_line.connect(self._log_viewer.append_line)
        self._server.state_changed.connect(self._on_state_changed)

    # ------------------------------------------------------------------ preset management
    def _on_preset_changed(self) -> None:
        preset = self._preset_picker.selected_preset()
        if preset:
            self._config_editor.set_preset(self._config.presets_dir / preset)
        else:
            self._config_editor.set_preset(None)

    def _on_new_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "New Preset", "Preset name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        dst = self._config.presets_dir / name
        if dst.exists():
            QMessageBox.warning(self, "Exists", f"Preset '{name}' already exists.")
            return
        template = self._config.presets_dir / "SERVER_01"
        if not template.exists():
            template = next(iter(self._config.presets_dir.iterdir()), None)  # type: ignore[assignment]
        if template is None:
            QMessageBox.critical(self, "Error", "No template preset found.")
            return
        copy_preset(template, dst)
        self._preset_picker.refresh()
        idx = self._preset_picker.findText(name)
        if idx >= 0:
            self._preset_picker.setCurrentIndex(idx)

    def _on_copy_preset(self) -> None:
        src_name = self._preset_picker.selected_preset()
        if not src_name:
            QMessageBox.warning(self, "No preset", "Select a preset to copy.")
            return
        name, ok = QInputDialog.getText(
            self, "Copy Preset", "New preset name:", text=f"{src_name}_copy"
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        dst = self._config.presets_dir / name
        if dst.exists():
            QMessageBox.warning(self, "Exists", f"Preset '{name}' already exists.")
            return
        copy_preset(self._config.presets_dir / src_name, dst)
        self._preset_picker.refresh()
        idx = self._preset_picker.findText(name)
        if idx >= 0:
            self._preset_picker.setCurrentIndex(idx)

    def _on_settings(self) -> None:
        dlg = _SettingsDialog(self._config, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._config.openweathermap_api_key = dlg.api_key()
            try:
                save_config(self._config)
            except Exception as exc:
                QMessageBox.warning(self, "Save failed", str(exc))
            self._config_editor.set_global_api_key(self._config.openweathermap_api_key)

    # ------------------------------------------------------------------ server control
    def _on_start(self) -> None:
        preset = self._preset_picker.selected_preset()
        if not preset:
            QMessageBox.warning(self, "No preset", "Please select a preset first.")
            return

        if self._config_editor.is_dirty():
            reply = QMessageBox.question(
                self,
                "Unsaved changes",
                "Config has unsaved changes. Save before starting?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Save:
                self._config_editor._on_save()  # noqa: SLF001

        preset_path = self._config.presets_dir / preset
        try:
            ip = get_lan_ip()
            ports = read_ports_from_cfg(preset_path)
            self._lan_label.setText(
                f"IP:   {ip}\nTCP:  {ports.tcp}\nUDP:  {ports.udp}\nHTTP: {ports.http}"
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

    def _on_state_changed(self, state: ServerState) -> None:
        self._status_panel.update_state(state)
        stopped = state in (ServerState.STOPPED, ServerState.CRASHED)
        self._btn_start.setEnabled(stopped)
        self._btn_stop.setEnabled(not stopped)
        self._config_editor.lock(not stopped)

    # ------------------------------------------------------------------ close
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
            if reply == QMessageBox.StandardButton.Yes:
                self._server.stop()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        event.accept()


class _SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._api_key_edit = QLineEdit(config.openweathermap_api_key)
        self._api_key_edit.setPlaceholderText("Paste your free key from openweathermap.org")
        self._api_key_edit.setToolTip(
            "Used as the default API key for LiveWeatherPlugin.\n"
            "Saved to app_config.yml and pre-filled in every preset's AssettoServer tab."
        )
        form.addRow("OpenWeatherMap API key:", self._api_key_edit)
        layout.addLayout(form)

        hint = QLabel(
            '<a href="https://home.openweathermap.org/api_keys">openweathermap.org/api_keys</a>'
            " — free tier is sufficient."
        )
        hint.setOpenExternalLinks(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def api_key(self) -> str:
        return self._api_key_edit.text().strip()
