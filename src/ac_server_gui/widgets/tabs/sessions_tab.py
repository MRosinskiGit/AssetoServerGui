from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.preset_config import PresetConfig

_IS_OPEN_OPTIONS = ["Closed (0)", "Free join (1)", "Free until first car (2)"]


class _SessionGroup(QGroupBox):
    def __init__(
        self,
        title: str,
        has_laps: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(title, parent)
        self._has_laps = has_laps
        self._form = QFormLayout(self)

        self._enabled = QCheckBox("Enabled")
        self._name = QLineEdit()

        self._time = QSpinBox()
        self._time.setRange(0, 9999)
        self._time.setSuffix(" min")

        self._laps = QSpinBox()
        self._laps.setRange(1, 9999)
        self._laps.setSuffix(" laps")

        self._wait = QSpinBox()
        self._wait.setRange(0, 3600)
        self._wait.setSuffix(" s")

        self._is_open = QComboBox()
        for o in _IS_OPEN_OPTIONS:
            self._is_open.addItem(o)

        self._form.addRow("", self._enabled)
        self._form.addRow("Session name:", self._name)

        if has_laps:
            # Race mode selector
            mode_w = QWidget()
            mode_row = QHBoxLayout(mode_w)
            mode_row.setContentsMargins(0, 0, 0, 0)
            self._btn_group = QButtonGroup(self)
            self._mode_laps = QRadioButton("Lap race")
            self._mode_timed = QRadioButton("Timed race")
            self._mode_laps.setChecked(True)
            self._btn_group.addButton(self._mode_laps)
            self._btn_group.addButton(self._mode_timed)
            mode_row.addWidget(self._mode_laps)
            mode_row.addWidget(self._mode_timed)
            self._form.addRow("Race type:", mode_w)
            self._form.addRow("Laps:", self._laps)
            self._form.addRow("Duration:", self._time)
            self._mode_laps.toggled.connect(self._sync_race_mode)
            self._sync_race_mode(True)
        else:
            self._form.addRow("Duration:", self._time)

        self._form.addRow("Wait time:", self._wait)
        self._form.addRow("Mid-session join:", self._is_open)

    def _sync_race_mode(self, laps_selected: bool) -> None:
        # Show laps field, hide time field (or vice versa)
        for widget, visible in [(self._laps, laps_selected), (self._time, not laps_selected)]:
            widget.setVisible(visible)
            label = self._form.labelForField(widget)
            if label:
                label.setVisible(visible)

    def populate(self, enabled: bool, data: dict[str, str]) -> None:
        self._enabled.setChecked(enabled)
        self._name.setText(data.get("NAME", ""))
        try:
            self._wait.setValue(int(data.get("WAIT_TIME", "0") or "0"))
        except ValueError:
            pass
        try:
            self._is_open.setCurrentIndex(max(0, min(2, int(data.get("IS_OPEN", "1")))))
        except ValueError:
            pass

        if self._has_laps:
            laps = int(data.get("LAPS", "0") or "0")
            time_val = int(data.get("TIME", "0") or "0")
            if laps > 0:
                self._mode_laps.setChecked(True)
                self._laps.setValue(laps)
            else:
                self._mode_timed.setChecked(True)
                self._time.setValue(time_val if time_val > 0 else 30)
        else:
            try:
                self._time.setValue(int(data.get("TIME", "0") or "0"))
            except ValueError:
                pass

    def collect_data(self) -> dict[str, str]:
        d: dict[str, str] = {
            "NAME": self._name.text(),
            "IS_OPEN": str(self._is_open.currentIndex()),
            "WAIT_TIME": str(self._wait.value()),
        }
        if self._has_laps:
            if self._mode_laps.isChecked():
                d["LAPS"] = str(self._laps.value())
                d["TIME"] = "0"
            else:
                d["TIME"] = str(self._time.value())
                d["LAPS"] = "0"
        else:
            d["TIME"] = str(self._time.value())
        return d

    def is_enabled(self) -> bool:
        return self._enabled.isChecked()


class SessionsTab(QWidget):
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

        self._practice = _SessionGroup("Practice", has_laps=False)
        self._qualify = _SessionGroup("Qualifying", has_laps=False)
        self._race = _SessionGroup("Race", has_laps=True)
        layout.addWidget(self._practice)
        layout.addWidget(self._qualify)
        layout.addWidget(self._race)
        layout.addStretch()

    def populate(self, cfg: PresetConfig) -> None:
        self._practice.populate(
            cfg.session_enabled("PRACTICE"),
            cfg.session_items("PRACTICE")
            or {"NAME": "Practice", "TIME": "30", "IS_OPEN": "1", "WAIT_TIME": "0"},
        )
        self._qualify.populate(
            cfg.session_enabled("QUALIFY"),
            cfg.session_items("QUALIFY")
            or {"NAME": "Qualifying", "TIME": "20", "IS_OPEN": "1", "WAIT_TIME": "0"},
        )
        self._race.populate(
            cfg.session_enabled("RACE"),
            cfg.session_items("RACE")
            or {"NAME": "Race", "LAPS": "5", "TIME": "0", "IS_OPEN": "2", "WAIT_TIME": "60"},
        )

    def collect(self, cfg: PresetConfig) -> None:
        cfg.session_save("PRACTICE", self._practice.is_enabled(), self._practice.collect_data())
        cfg.session_save("QUALIFY", self._qualify.is_enabled(), self._qualify.collect_data())
        cfg.session_save("RACE", self._race.is_enabled(), self._race.collect_data())
