from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.preset_config import PresetConfig


class GeneralTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        inner = QWidget()
        scroll.setWidget(inner)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(12, 12, 12, 12)

        # Server identity
        id_box = QGroupBox("Server Identity")
        id_form = QFormLayout(id_box)
        self._name = QLineEdit()
        self._password = QLineEdit()
        self._password.setPlaceholderText("(empty = public)")
        self._admin_pwd = QLineEdit()
        self._admin_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        id_form.addRow("Server name:", self._name)
        id_form.addRow("Password:", self._password)
        id_form.addRow("Admin password:", self._admin_pwd)
        layout.addWidget(id_box)

        # Capacity
        cap_box = QGroupBox("Capacity & Mode")
        cap_form = QFormLayout(cap_box)
        self._max_clients = QLineEdit()
        self._max_clients.setPlaceholderText("1–254")
        self._pickup_mode = QCheckBox("Pickup mode (any car, no booking)")
        self._loop_mode = QCheckBox("Loop mode (auto-restart sessions)")
        self._locked_entry = QCheckBox("Locked entry list (only listed drivers)")
        self._register_lobby = QCheckBox("Register to public lobby")
        cap_form.addRow("Max clients:", self._max_clients)
        cap_form.addRow("", self._pickup_mode)
        cap_form.addRow("", self._loop_mode)
        cap_form.addRow("", self._locked_entry)
        cap_form.addRow("", self._register_lobby)
        layout.addWidget(cap_box)

        layout.addStretch()

    def populate(self, cfg: PresetConfig) -> None:
        self._name.setText(cfg.name)
        self._password.setText(cfg.password)
        self._admin_pwd.setText(cfg.admin_password)
        self._max_clients.setText(str(cfg.max_clients))
        self._pickup_mode.setChecked(cfg.pickup_mode)
        self._loop_mode.setChecked(cfg.loop_mode)
        self._locked_entry.setChecked(cfg.locked_entry_list)
        self._register_lobby.setChecked(cfg.register_to_lobby)

    def collect(self, cfg: PresetConfig) -> None:
        cfg.name = self._name.text()
        cfg.password = self._password.text()
        cfg.admin_password = self._admin_pwd.text()
        try:
            cfg.max_clients = int(self._max_clients.text())
        except ValueError:
            pass
        cfg.pickup_mode = self._pickup_mode.isChecked()
        cfg.loop_mode = self._loop_mode.isChecked()
        cfg.locked_entry_list = self._locked_entry.isChecked()
        cfg.register_to_lobby = self._register_lobby.isChecked()
