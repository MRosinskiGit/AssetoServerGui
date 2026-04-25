from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.content_scanner import ContentScanner
from ac_server_gui.core.preset_config import PresetConfig


class TrackCarsTab(QWidget):
    cars_changed = Signal(list)  # emits list[str] of selected car folders
    def __init__(self, scanner: ContentScanner, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scanner = scanner
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Track section
        track_box = QGroupBox("Track")
        track_layout = QVBoxLayout(track_box)
        row = QHBoxLayout()
        row.addWidget(QLabel("Track:"))
        self._track_combo = QComboBox()
        self._track_combo.setMinimumWidth(240)
        row.addWidget(self._track_combo, 1)
        row.addWidget(QLabel("Layout:"))
        self._layout_combo = QComboBox()
        self._layout_combo.setMinimumWidth(180)
        row.addWidget(self._layout_combo, 1)
        track_layout.addLayout(row)
        layout.addWidget(track_box)

        # Cars section
        cars_box = QGroupBox("Cars")
        cars_layout = QHBoxLayout(cars_box)

        # Available cars (left)
        avail_col = QVBoxLayout()
        avail_col.addWidget(QLabel("Available:"))
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter…")
        avail_col.addWidget(self._filter)
        self._avail_list = QListWidget()
        self._avail_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        avail_col.addWidget(self._avail_list)
        cars_layout.addLayout(avail_col, 1)

        # Buttons
        btn_col = QVBoxLayout()
        btn_col.addStretch()
        self._btn_add = QPushButton("→ Add")
        self._btn_remove = QPushButton("← Remove")
        btn_col.addWidget(self._btn_add)
        btn_col.addWidget(self._btn_remove)
        btn_col.addStretch()
        cars_layout.addLayout(btn_col)

        # Selected cars (right)
        sel_col = QVBoxLayout()
        sel_col.addWidget(QLabel("Selected (CARS=):"))
        self._sel_list = QListWidget()
        self._sel_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        sel_col.addWidget(self._sel_list)
        cars_layout.addLayout(sel_col, 1)

        layout.addWidget(cars_box, 1)

        self._populate_track_combo()
        self._populate_avail_cars()

        self._track_combo.currentIndexChanged.connect(self._on_track_changed)
        self._filter.textChanged.connect(self._apply_car_filter)
        self._btn_add.clicked.connect(self._add_cars)
        self._btn_remove.clicked.connect(self._remove_cars)
        self._avail_list.itemDoubleClicked.connect(
            lambda _: self._add_cars()
        )
        self._sel_list.itemDoubleClicked.connect(
            lambda _: self._remove_cars()
        )

    def _populate_track_combo(self) -> None:
        self._track_combo.blockSignals(True)
        self._track_combo.clear()
        for t in self._scanner.tracks:
            self._track_combo.addItem(f"{t.folder}  ({t.display_name})", userData=t.folder)
        self._track_combo.blockSignals(False)

    def _populate_avail_cars(self) -> None:
        self._all_car_items: list[tuple[str, str]] = [
            (c.folder, c.display_name) for c in self._scanner.cars
        ]
        self._apply_car_filter()

    def _apply_car_filter(self) -> None:
        flt = self._filter.text().lower()
        selected_folders = self._selected_folders()
        self._avail_list.clear()
        for folder, display in self._all_car_items:
            if folder in selected_folders:
                continue
            if flt and flt not in folder.lower() and flt not in display.lower():
                continue
            item = QListWidgetItem(f"{folder}  ({display})")
            item.setData(Qt.ItemDataRole.UserRole, folder)
            self._avail_list.addItem(item)

    def _selected_folders(self) -> set[str]:
        result = set()
        for i in range(self._sel_list.count()):
            item = self._sel_list.item(i)
            if item:
                result.add(str(item.data(Qt.ItemDataRole.UserRole)))
        return result

    def _on_track_changed(self) -> None:
        folder = self._track_combo.currentData()
        self._layout_combo.clear()
        if folder is None:
            return
        for t in self._scanner.tracks:
            if t.folder == folder:
                for lay in t.layouts:
                    label = lay.display_name if lay.config else "(default)"
                    self._layout_combo.addItem(label, userData=lay.config)
                break

    def _add_cars(self) -> None:
        for item in self._avail_list.selectedItems():
            folder = str(item.data(Qt.ItemDataRole.UserRole))
            if folder not in self._selected_folders():
                sel_item = QListWidgetItem(item.text())
                sel_item.setData(Qt.ItemDataRole.UserRole, folder)
                self._sel_list.addItem(sel_item)
        self._apply_car_filter()
        self.cars_changed.emit(self._current_car_folders())

    def _remove_cars(self) -> None:
        for item in self._sel_list.selectedItems():
            self._sel_list.takeItem(self._sel_list.row(item))
        self._apply_car_filter()
        self.cars_changed.emit(self._current_car_folders())

    def _current_car_folders(self) -> list[str]:
        return [
            str(self._sel_list.item(i).data(Qt.ItemDataRole.UserRole))
            for i in range(self._sel_list.count())
            if self._sel_list.item(i) is not None
        ]

    def populate(self, cfg: PresetConfig) -> None:
        # Track
        idx = self._track_combo.findData(cfg.track)
        if idx >= 0:
            self._track_combo.setCurrentIndex(idx)
        self._on_track_changed()
        layout_idx = self._layout_combo.findData(cfg.config_track)
        if layout_idx >= 0:
            self._layout_combo.setCurrentIndex(layout_idx)

        # Cars
        self._sel_list.clear()
        for folder in cfg.cars:
            display = self._scanner.car_display(folder)
            item = QListWidgetItem(f"{folder}  ({display})")
            item.setData(Qt.ItemDataRole.UserRole, folder)
            self._sel_list.addItem(item)
        self._apply_car_filter()
        self.cars_changed.emit(self._current_car_folders())

    def collect(self, cfg: PresetConfig) -> None:
        cfg.track = str(self._track_combo.currentData() or "")
        cfg.config_track = str(self._layout_combo.currentData() or "")
        cfg.cars = [
            str(self._sel_list.item(i).data(Qt.ItemDataRole.UserRole))
            for i in range(self._sel_list.count())
            if self._sel_list.item(i) is not None
        ]
