from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.preset_config import PresetConfig


class DynamicTrackTab(QWidget):
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

        box = QGroupBox("Dynamic Track (rubber-in)")
        form = QFormLayout(box)
        self._enabled = QCheckBox("Enable dynamic track")
        self._session_start = QSpinBox()
        self._session_start.setRange(0, 100)
        self._session_start.setSuffix("%")
        self._session_start.setToolTip("Initial grip at session start")
        self._randomness = QSpinBox()
        self._randomness.setRange(0, 100)
        self._randomness.setSuffix("%")
        self._randomness.setToolTip("Random variation added to starting grip")
        self._session_transfer = QSpinBox()
        self._session_transfer.setRange(0, 100)
        self._session_transfer.setSuffix("%")
        self._session_transfer.setToolTip("How much gained grip carries to next session")
        self._lap_gain = QSpinBox()
        self._lap_gain.setRange(1, 999)
        self._lap_gain.setToolTip("Laps needed to gain 1% grip")
        form.addRow("", self._enabled)
        form.addRow("Session start grip:", self._session_start)
        form.addRow("Randomness:", self._randomness)
        form.addRow("Session transfer:", self._session_transfer)
        form.addRow("Laps per 1% gain:", self._lap_gain)
        layout.addWidget(box)
        layout.addStretch()

    def populate(self, cfg: PresetConfig) -> None:
        self._enabled.setChecked(cfg.dyn_track_enabled())
        self._session_start.setValue(int(cfg.dyn_track_get("SESSION_START", "95") or "95"))
        self._randomness.setValue(int(cfg.dyn_track_get("RANDOMNESS", "2") or "2"))
        self._session_transfer.setValue(int(cfg.dyn_track_get("SESSION_TRANSFER", "90") or "90"))
        self._lap_gain.setValue(int(cfg.dyn_track_get("LAP_GAIN", "10") or "10"))

    def collect(self, cfg: PresetConfig) -> None:
        cfg.dyn_track_save(
            self._enabled.isChecked(),
            {
                "SESSION_START": str(self._session_start.value()),
                "RANDOMNESS": str(self._randomness.value()),
                "SESSION_TRANSFER": str(self._session_transfer.value()),
                "LAP_GAIN": str(self._lap_gain.value()),
            },
        )
