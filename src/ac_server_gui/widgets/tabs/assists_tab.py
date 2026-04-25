from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.preset_config import PresetConfig

_ASSIST_OPTIONS = ["Disabled (0)", "Factory default (1)", "Any setting (2)"]


def _assist_combo() -> QComboBox:
    c = QComboBox()
    for o in _ASSIST_OPTIONS:
        c.addItem(o)
    return c


class AssistsTab(QWidget):
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

        aids_box = QGroupBox("Driving Aids")
        form = QFormLayout(aids_box)
        self._abs = _assist_combo()
        self._tc = _assist_combo()
        self._stability = QCheckBox("Stability control allowed")
        self._autoclutch = QCheckBox("Auto-clutch allowed")
        self._tyre_blankets = QCheckBox("Tyre blankets allowed")
        self._virtual_mirror = QCheckBox("Force virtual mirror")
        form.addRow("ABS:", self._abs)
        form.addRow("Traction control:", self._tc)
        form.addRow("", self._stability)
        form.addRow("", self._autoclutch)
        form.addRow("", self._tyre_blankets)
        form.addRow("", self._virtual_mirror)
        layout.addWidget(aids_box)
        layout.addStretch()

    def populate(self, cfg: PresetConfig) -> None:
        self._abs.setCurrentIndex(max(0, min(2, cfg.abs_allowed)))
        self._tc.setCurrentIndex(max(0, min(2, cfg.tc_allowed)))
        self._stability.setChecked(cfg.stability_allowed)
        self._autoclutch.setChecked(cfg.autoclutch_allowed)
        self._tyre_blankets.setChecked(cfg.tyre_blankets_allowed)
        self._virtual_mirror.setChecked(cfg.force_virtual_mirror)

    def collect(self, cfg: PresetConfig) -> None:
        cfg.abs_allowed = self._abs.currentIndex()
        cfg.tc_allowed = self._tc.currentIndex()
        cfg.stability_allowed = self._stability.isChecked()
        cfg.autoclutch_allowed = self._autoclutch.isChecked()
        cfg.tyre_blankets_allowed = self._tyre_blankets.isChecked()
        cfg.force_virtual_mirror = self._virtual_mirror.isChecked()
