from __future__ import annotations

from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.content_scanner import ContentScanner
from ac_server_gui.core.preset_config import PresetConfig

# AC formula: SUN_ANGLE = 16 × (time_seconds − 46800) / (50400 − 46800)
#                       = 16 × (time_seconds − 46800) / 3600
# Inverse:   time_seconds = SUN_ANGLE × 225 + 46800
# Examples:  00:00 → −208,  08:00 → −80,  13:00 → 0,  18:00 → +80


def angle_to_time(angle: int) -> QTime:
    total_s = int(angle) * 225 + 46800
    total_s = max(0, min(86399, total_s))
    return QTime(total_s // 3600, (total_s % 3600) // 60)


def time_to_angle(t: QTime) -> int:
    total_s = t.hour() * 3600 + t.minute() * 60
    return int(round(16 * (total_s - 46800) / 3600))


class WeatherTab(QWidget):
    def __init__(self, scanner: ContentScanner, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scanner = scanner
        self._slots: list[dict[str, str]] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Left: slot list + add/remove + time-of-day
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left.setFixedWidth(180)
        left_layout.addWidget(QLabel("Weather slots:"))
        self._slot_list = QListWidget()
        left_layout.addWidget(self._slot_list, 1)
        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("+ Add")
        self._btn_remove = QPushButton("− Remove")
        btn_row.addWidget(self._btn_add)
        btn_row.addWidget(self._btn_remove)
        left_layout.addLayout(btn_row)

        tod_box = QGroupBox("Time of Day")
        tod_form = QFormLayout(tod_box)
        self._sun_time = QTimeEdit()
        self._sun_time.setDisplayFormat("HH:mm")
        self._sun_time.setToolTip(
            "Time of day shown in-game (full 24-hour range).\n"
            "Formula: SUN_ANGLE = 16×(seconds − 46800) / 3600\n"
            "  00:00 → −208   08:00 → −80\n"
            "  13:00 →    0   18:00 → +80\n"
            "Note: ignored when EnableWeatherFx is true in AssettoServer tab."
        )
        self._time_mult = QSpinBox()
        self._time_mult.setRange(1, 120)
        self._time_mult.setSuffix("×")
        self._time_mult.setToolTip(
            "Time-of-day speed multiplier (1 = real-time).\n"
            "Ignored when EnableWeatherFx is true."
        )
        tod_form.addRow("Start time:", self._sun_time)
        tod_form.addRow("Time multiplier:", self._time_mult)
        left_layout.addWidget(tod_box)

        layout.addWidget(left)

        # Right: per-slot editor
        self._slot_editor = _SlotEditor(scanner)
        layout.addWidget(self._slot_editor, 1)

        self._slot_list.currentRowChanged.connect(self._on_slot_selected)
        self._btn_add.clicked.connect(self._add_slot)
        self._btn_remove.clicked.connect(self._remove_slot)
        self._slot_editor.changed.connect(self._on_slot_edited)

    def _on_slot_selected(self, row: int) -> None:
        if 0 <= row < len(self._slots):
            self._slot_editor.populate(self._slots[row])

    def _on_slot_edited(self, data: dict[str, str]) -> None:
        row = self._slot_list.currentRow()
        if 0 <= row < len(self._slots):
            self._slots[row] = data

    def _add_slot(self) -> None:
        idx = len(self._slots)
        self._slots.append({
            "GRAPHICS": "3_clear",
            "__CM_GRAPHICS": "3_clear",
            "BASE_TEMPERATURE_AMBIENT": "18",
            "BASE_TEMPERATURE_ROAD": "6",
            "VARIATION_AMBIENT": "1",
            "VARIATION_ROAD": "1",
            "WIND_BASE_SPEED_MIN": "0",
            "WIND_BASE_SPEED_MAX": "0",
            "WIND_BASE_DIRECTION": "0",
            "WIND_VARIATION_DIRECTION": "0",
        })
        self._slot_list.addItem(f"Weather {idx}")
        self._slot_list.setCurrentRow(idx)

    def _remove_slot(self) -> None:
        row = self._slot_list.currentRow()
        if row < 0 or len(self._slots) <= 1:
            return
        self._slots.pop(row)
        self._slot_list.takeItem(row)
        for i in range(self._slot_list.count()):
            item = self._slot_list.item(i)
            if item:
                item.setText(f"Weather {i}")
        self._slot_list.setCurrentRow(max(0, row - 1))

    def populate(self, cfg: PresetConfig) -> None:
        self._sun_time.setTime(angle_to_time(cfg.sun_angle))
        self._time_mult.setValue(cfg.time_of_day_mult)
        count = cfg.weather_count()
        self._slots = [cfg.weather_items(i) for i in range(max(1, count))]
        self._slot_list.clear()
        for i in range(len(self._slots)):
            self._slot_list.addItem(f"Weather {i}")
        if self._slots:
            self._slot_list.setCurrentRow(0)
            self._slot_editor.populate(self._slots[0])

    def collect(self, cfg: PresetConfig) -> None:
        cfg.sun_angle = time_to_angle(self._sun_time.time())
        cfg.time_of_day_mult = self._time_mult.value()
        cfg.weather_save(self._slots)


class _SlotEditor(QWidget):
    from PySide6.QtCore import Signal
    changed = Signal(dict)

    def __init__(self, scanner: ContentScanner, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scanner = scanner
        self._loading = False

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        inner = QWidget()
        scroll.setWidget(inner)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(8, 8, 8, 8)

        wx_box = QGroupBox("Weather Type")
        wx_form = QFormLayout(wx_box)
        self._graphics = QComboBox()
        for w in scanner.weather_types:
            self._graphics.addItem(w)
        wx_form.addRow("Graphics folder:", self._graphics)
        layout.addWidget(wx_box)

        temp_box = QGroupBox("Temperature")
        temp_form = QFormLayout(temp_box)
        self._amb = self._temp_spin()
        self._road = self._road_spin()
        self._var_amb = self._var_spin()
        self._var_road = self._var_spin()
        temp_form.addRow("Base ambient (°C):", self._amb)
        temp_form.addRow("Road offset (°C):", self._road)
        self._var_amb.setToolTip(
            "Random ±°C variation added to the ambient temperature each session.\n"
            "E.g. 2 means actual temp is anywhere from (base-2) to (base+2)°C."
        )
        self._var_road.setToolTip(
            "Random ±°C variation added to the road temperature each session."
        )
        temp_form.addRow("Ambient variation (±°C):", self._var_amb)
        temp_form.addRow("Road variation (±°C):", self._var_road)
        layout.addWidget(temp_box)

        wind_box = QGroupBox("Wind")
        wind_form = QFormLayout(wind_box)
        self._wind_min = QSpinBox()
        self._wind_min.setRange(0, 40)
        self._wind_min.setSuffix(" km/h")
        self._wind_max = QSpinBox()
        self._wind_max.setRange(0, 40)
        self._wind_max.setSuffix(" km/h")
        self._wind_dir = QSpinBox()
        self._wind_dir.setRange(0, 359)
        self._wind_dir.setSuffix("°  (0=N, 90=E, 180=S, 270=W)")
        self._wind_var = QSpinBox()
        self._wind_var.setRange(0, 180)
        self._wind_var.setSuffix("°")
        wind_form.addRow("Min speed:", self._wind_min)
        wind_form.addRow("Max speed:", self._wind_max)
        wind_form.addRow("Direction:", self._wind_dir)
        wind_form.addRow("Direction variation (±°):", self._wind_var)
        layout.addWidget(wind_box)
        layout.addStretch()

        for widget in [self._amb, self._road, self._var_amb, self._var_road,
                       self._wind_min, self._wind_max, self._wind_dir, self._wind_var]:
            widget.valueChanged.connect(self._emit_changed)
        self._graphics.currentTextChanged.connect(self._emit_changed)

    @staticmethod
    def _temp_spin() -> QSpinBox:
        s = QSpinBox()
        s.setRange(-50, 60)
        s.setSuffix(" °C")
        return s

    @staticmethod
    def _road_spin() -> QSpinBox:
        s = QSpinBox()
        s.setRange(-30, 40)
        s.setSuffix(" °C  (added to ambient)")
        return s

    @staticmethod
    def _var_spin() -> QSpinBox:
        s = QSpinBox()
        s.setRange(0, 30)
        return s

    def _emit_changed(self, *_: object) -> None:
        if not self._loading:
            self.changed.emit(self._collect())

    def _collect(self) -> dict[str, str]:
        g = self._graphics.currentText()
        return {
            "GRAPHICS": g,
            "__CM_GRAPHICS": g,
            "BASE_TEMPERATURE_AMBIENT": str(self._amb.value()),
            "BASE_TEMPERATURE_ROAD": str(self._road.value()),
            "VARIATION_AMBIENT": str(self._var_amb.value()),
            "VARIATION_ROAD": str(self._var_road.value()),
            "WIND_BASE_SPEED_MIN": str(self._wind_min.value()),
            "WIND_BASE_SPEED_MAX": str(self._wind_max.value()),
            "WIND_BASE_DIRECTION": str(self._wind_dir.value()),
            "WIND_VARIATION_DIRECTION": str(self._wind_var.value()),
        }

    def populate(self, data: dict[str, str]) -> None:
        self._loading = True
        graphics = data.get("__CM_GRAPHICS") or data.get("GRAPHICS", "")
        if "_type=" in graphics or "_time=" in graphics:
            graphics = graphics.split("_type=")[0]
        idx = self._graphics.findText(graphics)
        if idx >= 0:
            self._graphics.setCurrentIndex(idx)

        def _i(key: str, default: int) -> int:
            try:
                return int(data.get(key, str(default)) or str(default))
            except ValueError:
                return default

        self._amb.setValue(_i("BASE_TEMPERATURE_AMBIENT", 18))
        self._road.setValue(_i("BASE_TEMPERATURE_ROAD", 6))
        self._var_amb.setValue(_i("VARIATION_AMBIENT", 1))
        self._var_road.setValue(_i("VARIATION_ROAD", 1))
        self._wind_min.setValue(_i("WIND_BASE_SPEED_MIN", 0))
        self._wind_max.setValue(_i("WIND_BASE_SPEED_MAX", 0))
        self._wind_dir.setValue(_i("WIND_BASE_DIRECTION", 0))
        self._wind_var.setValue(_i("WIND_VARIATION_DIRECTION", 0))
        self._loading = False
