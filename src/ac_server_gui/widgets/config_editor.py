from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.content_scanner import ContentScanner
from ac_server_gui.core.preset_config import PresetConfig
from ac_server_gui.widgets.tabs.assists_tab import AssistsTab
from ac_server_gui.widgets.tabs.dynamic_track_tab import DynamicTrackTab
from ac_server_gui.widgets.tabs.entry_list_tab import EntryListTab
from ac_server_gui.widgets.tabs.extra_tab import ExtraTab
from ac_server_gui.widgets.tabs.general_tab import GeneralTab
from ac_server_gui.widgets.tabs.network_tab import NetworkTab
from ac_server_gui.widgets.tabs.rules_tab import RulesTab
from ac_server_gui.widgets.tabs.sessions_tab import SessionsTab
from ac_server_gui.widgets.tabs.track_cars_tab import TrackCarsTab
from ac_server_gui.widgets.tabs.weather_tab import WeatherTab


class ConfigEditor(QWidget):
    saved = Signal(str)  # emits preset name after save

    def __init__(self, scanner: ContentScanner, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scanner = scanner
        self._cfg: PresetConfig | None = None
        self._dirty = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()
        self._general = GeneralTab()
        self._track_cars = TrackCarsTab(scanner)
        self._sessions = SessionsTab()
        self._assists = AssistsTab()
        self._rules = RulesTab()
        self._weather = WeatherTab(scanner)
        self._dyn_track = DynamicTrackTab()
        self._network = NetworkTab()
        self._entry_list = EntryListTab(scanner)
        self._extra = ExtraTab()

        self._tabs.addTab(self._general, "General")
        self._tabs.addTab(self._track_cars, "Track & Cars")
        self._tabs.addTab(self._sessions, "Sessions")
        self._tabs.addTab(self._assists, "Assists")
        self._tabs.addTab(self._rules, "Rules")
        self._tabs.addTab(self._weather, "Weather")
        self._tabs.addTab(self._dyn_track, "Track Grip")
        self._tabs.addTab(self._network, "Network")
        self._tabs.addTab(self._entry_list, "Entry List")
        self._tabs.addTab(self._extra, "AssettoServer")
        layout.addWidget(self._tabs, 1)

        # Bottom bar
        bar = QHBoxLayout()
        self._dirty_label = QLabel("")
        self._dirty_label.setStyleSheet("color: #FFA500;")
        bar.addWidget(self._dirty_label)
        bar.addStretch()
        self._btn_revert = QPushButton("Revert")
        self._btn_save = QPushButton("Save Config")
        self._btn_save.setDefault(True)
        bar.addWidget(self._btn_revert)
        bar.addWidget(self._btn_save)
        layout.addLayout(bar)

        self._btn_save.clicked.connect(self._on_save)
        self._btn_revert.clicked.connect(self._on_revert)

        self._all_tab_widgets = [
            self._general, self._track_cars, self._sessions, self._assists,
            self._rules, self._weather, self._dyn_track, self._network,
            self._entry_list, self._extra,
        ]

        self._connect_dirty_signals()
        # Cross-tab wiring: car selection drives entry-list model dropdowns
        self._track_cars.cars_changed.connect(self._entry_list.set_car_models)
        self.set_preset(None)

    # ------------------------------------------------------------------ public API
    def set_preset(self, preset_path: Path | None) -> None:
        if preset_path is None:
            self._cfg = None
            self._tabs.setEnabled(False)
            self._btn_save.setEnabled(False)
            self._btn_revert.setEnabled(False)
            self._dirty_label.setText("No preset selected")
            return
        self._cfg = PresetConfig(preset_path)
        self._tabs.setEnabled(True)
        self._load_all()
        self._mark_clean()

    def lock(self, locked: bool) -> None:
        """Disable editing while server is running."""
        self._tabs.setEnabled(not locked)
        self._btn_save.setEnabled(not locked)
        self._btn_revert.setEnabled(not locked)
        if locked:
            self._dirty_label.setText("⚠ Config editing disabled while server is running")
        else:
            self._update_dirty_label()

    def is_dirty(self) -> bool:
        return self._dirty

    def set_global_api_key(self, key: str) -> None:
        self._extra.set_global_api_key(key)

    # ------------------------------------------------------------------ internal
    def _load_all(self) -> None:
        if self._cfg is None:
            return
        for tab in self._all_tab_widgets:
            tab.populate(self._cfg)  # type: ignore[attr-defined]

    def _collect_all(self) -> None:
        if self._cfg is None:
            return
        for tab in self._all_tab_widgets:
            tab.collect(self._cfg)  # type: ignore[attr-defined]

    def _on_save(self) -> None:
        if self._cfg is None:
            return
        self._collect_all()
        try:
            self._cfg.save()
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self._mark_clean()
        self.saved.emit(self._cfg.path.name)

    def _on_revert(self) -> None:
        if self._cfg is None:
            return
        self._load_all()
        self._mark_clean()

    def _mark_dirty(self) -> None:
        if not self._dirty:
            self._dirty = True
            self._update_dirty_label()

    def _mark_clean(self) -> None:
        self._dirty = False
        self._update_dirty_label()

    def _update_dirty_label(self) -> None:
        if self._cfg is None:
            return
        if self._dirty:
            self._dirty_label.setText("● Unsaved changes")
        else:
            self._dirty_label.setText(f"✔ Saved  ({self._cfg.path.name})")

    def _connect_dirty_signals(self) -> None:
        from PySide6.QtWidgets import (
            QCheckBox,
            QComboBox,
            QLineEdit,
            QPlainTextEdit,
            QSpinBox,
        )

        for tab_widget in self._all_tab_widgets:
            for le in tab_widget.findChildren(QLineEdit):
                le.textChanged.connect(self._mark_dirty)
            for sb in tab_widget.findChildren(QSpinBox):
                sb.valueChanged.connect(self._mark_dirty)
            for cb in tab_widget.findChildren(QCheckBox):
                cb.checkStateChanged.connect(self._mark_dirty)
            for combo in tab_widget.findChildren(QComboBox):
                combo.currentIndexChanged.connect(self._mark_dirty)
            for pte in tab_widget.findChildren(QPlainTextEdit):
                pte.textChanged.connect(self._mark_dirty)
