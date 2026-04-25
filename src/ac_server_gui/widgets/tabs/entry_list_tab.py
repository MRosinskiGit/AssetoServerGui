from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.content_scanner import ContentScanner
from ac_server_gui.core.preset_config import PresetConfig

_AI_OPTIONS = ["none", "auto", "fixed"]
_COLS = ["Model", "Skin", "AI", "Ballast (kg)", "Restrictor (%)", "Driver Name", "GUID", "Team"]


class EntryListTab(QWidget):
    def __init__(self, scanner: ContentScanner, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scanner = scanner
        self._car_models: list[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        info = QLabel("Slots ≥ Max Clients. Model must be in the CARS= list (Track & Cars tab).")
        info.setStyleSheet("color: #888;")
        layout.addWidget(info)

        self._table = QTableWidget(0, len(_COLS))
        self._table.setHorizontalHeaderLabels(_COLS)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("+ Add slot")
        self._btn_remove = QPushButton("− Remove selected")
        btn_row.addWidget(self._btn_add)
        btn_row.addWidget(self._btn_remove)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._btn_add.clicked.connect(self._add_row)
        self._btn_remove.clicked.connect(self._remove_selected)

    def _add_row(self) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        model = self._car_models[0] if self._car_models else ""
        self._fill_row(row, {
            "MODEL": model, "SKIN": "", "AI": "none",
            "BALLAST": "0", "RESTRICTOR": "0",
            "DRIVERNAME": "", "GUID": "", "TEAM": "",
        })

    def _remove_selected(self) -> None:
        rows = sorted({idx.row() for idx in self._table.selectedIndexes()}, reverse=True)
        for r in rows:
            self._table.removeRow(r)

    def _fill_row(self, row: int, data: dict[str, str]) -> None:
        # Model combo
        model_combo = QComboBox()
        for m in self._car_models:
            model_combo.addItem(m)
        idx = model_combo.findText(data.get("MODEL", ""))
        if idx >= 0:
            model_combo.setCurrentIndex(idx)
        self._table.setCellWidget(row, 0, model_combo)

        # Skin combo
        skin_combo = QComboBox()
        skin_combo.setEditable(True)
        model_combo.currentTextChanged.connect(
            lambda m, sc=skin_combo: self._update_skins(sc, m)
        )
        self._update_skins(skin_combo, model_combo.currentText())
        skin_idx = skin_combo.findText(data.get("SKIN", ""))
        if skin_idx >= 0:
            skin_combo.setCurrentIndex(skin_idx)
        elif data.get("SKIN"):
            skin_combo.setCurrentText(data["SKIN"])
        self._table.setCellWidget(row, 1, skin_combo)

        # AI combo
        ai_combo = QComboBox()
        for opt in _AI_OPTIONS:
            ai_combo.addItem(opt)
        ai_idx = ai_combo.findText(data.get("AI", "none"))
        if ai_idx >= 0:
            ai_combo.setCurrentIndex(ai_idx)
        self._table.setCellWidget(row, 2, ai_combo)

        # Numeric cells
        for col, key, lo, hi in [(3, "BALLAST", 0, 300), (4, "RESTRICTOR", 0, 30)]:
            spin = QSpinBox()
            spin.setRange(lo, hi)
            try:
                spin.setValue(int(data.get(key, "0") or "0"))
            except ValueError:
                pass
            self._table.setCellWidget(row, col, spin)

        # Text cells
        for col, key in [(5, "DRIVERNAME"), (6, "GUID"), (7, "TEAM")]:
            item = QTableWidgetItem(data.get(key, ""))
            self._table.setItem(row, col, item)

    def _update_skins(self, combo: QComboBox, model: str) -> None:
        current = combo.currentText()
        combo.clear()
        for skin in self._scanner.skins_for(model):
            combo.addItem(skin)
        idx = combo.findText(current)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def set_car_models(self, models: list[str]) -> None:
        """Update every model combo in the table to reflect a new CARS= list."""
        self._car_models = models
        for row in range(self._table.rowCount()):
            combo = self._table.cellWidget(row, 0)
            if not isinstance(combo, QComboBox):
                continue
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            for m in models:
                combo.addItem(m)
            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            elif current:
                # Keep the old model even if it was removed from CARS=,
                # so the user can see and decide what to do.
                combo.addItem(current)
                combo.setCurrentText(current)
            combo.blockSignals(False)

    def populate(self, cfg: PresetConfig) -> None:
        self._car_models = cfg.cars
        self._table.setRowCount(0)
        for slot in cfg.entry_slots():
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._fill_row(row, slot)

    def collect(self, cfg: PresetConfig) -> None:
        slots: list[dict[str, str]] = []
        for row in range(self._table.rowCount()):
            model_w = self._table.cellWidget(row, 0)
            skin_w = self._table.cellWidget(row, 1)
            ai_w = self._table.cellWidget(row, 2)
            ballast_w = self._table.cellWidget(row, 3)
            rest_w = self._table.cellWidget(row, 4)
            driver_item = self._table.item(row, 5)
            guid_item = self._table.item(row, 6)
            team_item = self._table.item(row, 7)

            slots.append({
                "MODEL": model_w.currentText() if isinstance(model_w, QComboBox) else "",
                "SKIN": skin_w.currentText() if isinstance(skin_w, QComboBox) else "",
                "AI": ai_w.currentText() if isinstance(ai_w, QComboBox) else "none",
                "BALLAST": str(ballast_w.value() if isinstance(ballast_w, QSpinBox) else 0),
                "RESTRICTOR": str(rest_w.value() if isinstance(rest_w, QSpinBox) else 0),
                "DRIVERNAME": driver_item.text() if driver_item else "",
                "GUID": guid_item.text() if guid_item else "",
                "TEAM": team_item.text() if team_item else "",
                "SPECTATOR_MODE": "0",
            })
        cfg.entry_save(slots)
