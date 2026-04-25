from __future__ import annotations

import re

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.content_scanner import CarInfo, ContentScanner, TrackLayout
from ac_server_gui.core.preset_config import PresetConfig

_BADGE_SIZE = 24
_PREVIEW_W, _PREVIEW_H = 220, 145
_OUTLINE_W, _OUTLINE_H = 160, 105


def _load_pixmap(path: object, w: int, h: int) -> QPixmap | None:
    from pathlib import Path
    if not isinstance(path, Path) or not path.exists():
        return None
    try:
        pix = QPixmap(str(path))
        if pix.isNull():
            return None
        return pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
    except Exception:
        return None


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


class _CarDetailPanel(QWidget):
    """Shows preview image + specs for a selected car."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(175)
        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)

        # Preview image
        self._img = QLabel()
        self._img.setFixedSize(_PREVIEW_W, _PREVIEW_H)
        self._img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img.setStyleSheet("background:#1e1e1e; border:1px solid #444; color:#666;")
        self._img.setText("No preview")
        root.addWidget(self._img)

        # Text info
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        info_w = QWidget()
        self._info_layout = QVBoxLayout(info_w)
        self._info_layout.setContentsMargins(8, 0, 0, 0)
        self._info_layout.setSpacing(2)
        self._name_lbl = QLabel()
        self._name_lbl.setStyleSheet("font-size:13px; font-weight:bold;")
        self._name_lbl.setWordWrap(True)
        self._meta_lbl = QLabel()
        self._meta_lbl.setStyleSheet("color:#aaa; font-size:11px;")
        self._source_lbl = QLabel()
        self._source_lbl.setStyleSheet("color:#88aaff; font-size:11px;")
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#444;")
        self._specs_lbl = QLabel()
        self._specs_lbl.setStyleSheet("font-size:11px;")
        self._specs_lbl.setWordWrap(True)
        self._tags_lbl = QLabel()
        self._tags_lbl.setStyleSheet("color:#888; font-size:10px; font-style:italic;")
        self._tags_lbl.setWordWrap(True)
        for w in [self._name_lbl, self._meta_lbl, self._source_lbl,
                  sep, self._specs_lbl, self._tags_lbl]:
            self._info_layout.addWidget(w)
        self._info_layout.addStretch()
        scroll.setWidget(info_w)
        root.addWidget(scroll, 1)

        self.clear()

    def clear(self) -> None:
        self._img.setPixmap(QPixmap())
        self._img.setText("Select a car")
        self._name_lbl.setText("")
        self._meta_lbl.setText("")
        self._source_lbl.setText("")
        self._specs_lbl.setText("")
        self._tags_lbl.setText("")

    def show_car(self, car: CarInfo) -> None:
        pix = _load_pixmap(car.preview_path, _PREVIEW_W, _PREVIEW_H)
        if pix:
            self._img.setPixmap(pix)
            self._img.setText("")
        else:
            self._img.setPixmap(QPixmap())
            self._img.setText("No preview")

        self._name_lbl.setText(car.display_name)
        meta_parts = [p for p in [car.car_class, car.year, car.country] if p]
        self._meta_lbl.setText("  ·  ".join(meta_parts))
        self._source_lbl.setText(f"Source: {car.source}" if car.source else "")

        s = car.specs
        rows: list[str] = []
        if s.bhp:
            rows.append(f"<b>Power:</b> {s.bhp}")
        if s.torque:
            rows.append(f"<b>Torque:</b> {s.torque}")
        if s.weight:
            rows.append(f"<b>Weight:</b> {s.weight}")
        if s.top_speed:
            rows.append(f"<b>Top speed:</b> {s.top_speed}")
        if s.acceleration:
            rows.append(f"<b>0–100:</b> {s.acceleration}")
        if s.pw_ratio:
            rows.append(f"<b>Power/weight:</b> {s.pw_ratio}")
        self._specs_lbl.setText("<br>".join(rows))

        visible_tags = [t for t in car.tags if not t.startswith("#")][:8]
        self._tags_lbl.setText("  ".join(visible_tags) if visible_tags else "")


class _TrackInfoPanel(QWidget):
    """Shows outline image + metadata for the selected track layout."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMaximumHeight(130)
        root = QHBoxLayout(self)
        root.setContentsMargins(4, 2, 4, 2)

        self._img = QLabel()
        self._img.setFixedSize(_OUTLINE_W, _OUTLINE_H)
        self._img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img.setStyleSheet("background:#1e1e1e; border:1px solid #444; color:#666;")
        root.addWidget(self._img)

        info_w = QWidget()
        v = QVBoxLayout(info_w)
        v.setContentsMargins(8, 0, 0, 0)
        v.setSpacing(2)
        self._name_lbl = QLabel()
        self._name_lbl.setStyleSheet("font-weight:bold;")
        self._stats_lbl = QLabel()
        self._stats_lbl.setStyleSheet("color:#aaa; font-size:11px;")
        self._stats_lbl.setWordWrap(True)
        v.addWidget(self._name_lbl)
        v.addWidget(self._stats_lbl)
        v.addStretch()
        root.addWidget(info_w, 1)

        self.setVisible(False)

    def show_layout(self, layout: TrackLayout) -> None:
        pix = _load_pixmap(layout.outline_path, _OUTLINE_W, _OUTLINE_H)
        if pix:
            self._img.setPixmap(pix)
            self._img.setText("")
        else:
            self._img.setPixmap(QPixmap())
            self._img.setText("No outline")
        self._name_lbl.setText(layout.display_name)
        parts: list[str] = []
        if layout.length:
            parts.append(f"Length: {layout.length}")
        if layout.pitboxes:
            parts.append(f"Pits: {layout.pitboxes}")
        if layout.country:
            parts.append(layout.country)
        if layout.city:
            parts.append(layout.city)
        self._stats_lbl.setText("  ·  ".join(parts))
        self.setVisible(True)


class TrackCarsTab(QWidget):
    cars_changed = Signal(list)  # emits list[str] of selected car folders

    def __init__(self, scanner: ContentScanner, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scanner = scanner
        self._icon_cache: dict[str, QIcon] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # ── Track section ─────────────────────────────────────────────────────
        track_box = QGroupBox("Track")
        track_v = QVBoxLayout(track_box)
        combos = QHBoxLayout()
        combos.addWidget(QLabel("Track:"))
        self._track_combo = QComboBox()
        self._track_combo.setMinimumWidth(240)
        combos.addWidget(self._track_combo, 1)
        combos.addWidget(QLabel("Layout:"))
        self._layout_combo = QComboBox()
        self._layout_combo.setMinimumWidth(180)
        combos.addWidget(self._layout_combo, 1)
        track_v.addLayout(combos)
        self._track_info = _TrackInfoPanel()
        track_v.addWidget(self._track_info)
        layout.addWidget(track_box)

        # ── Cars section ──────────────────────────────────────────────────────
        cars_box = QGroupBox("Cars  (CARS= list)")
        cars_v = QVBoxLayout(cars_box)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Dual list
        lists_w = QWidget()
        lists_layout = QHBoxLayout(lists_w)
        lists_layout.setContentsMargins(0, 0, 0, 0)

        avail_col = QVBoxLayout()
        avail_col.addWidget(QLabel("Available:"))
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filter…")
        avail_col.addWidget(self._filter)
        self._avail_list = QListWidget()
        self._avail_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._avail_list.setIconSize(QSize(_BADGE_SIZE, _BADGE_SIZE))
        avail_col.addWidget(self._avail_list)
        lists_layout.addLayout(avail_col, 1)

        btn_col = QVBoxLayout()
        btn_col.addStretch()
        self._btn_add = QPushButton("→ Add")
        self._btn_remove = QPushButton("← Remove")
        btn_col.addWidget(self._btn_add)
        btn_col.addWidget(self._btn_remove)
        btn_col.addStretch()
        lists_layout.addLayout(btn_col)

        sel_col = QVBoxLayout()
        sel_col.addWidget(QLabel("Selected (CARS=):"))
        self._sel_list = QListWidget()
        self._sel_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._sel_list.setIconSize(QSize(_BADGE_SIZE, _BADGE_SIZE))
        sel_col.addWidget(self._sel_list)
        lists_layout.addLayout(sel_col, 1)

        splitter.addWidget(lists_w)

        # Car detail panel
        self._car_detail = _CarDetailPanel()
        splitter.addWidget(self._car_detail)
        splitter.setSizes([300, 175])

        cars_v.addWidget(splitter)
        layout.addWidget(cars_box, 1)

        # ── Init content ──────────────────────────────────────────────────────
        self._all_car_infos: list[CarInfo] = []
        self._populate_track_combo()
        self._populate_avail_cars()

        # ── Signals ───────────────────────────────────────────────────────────
        self._track_combo.currentIndexChanged.connect(self._on_track_changed)
        self._layout_combo.currentIndexChanged.connect(self._on_layout_changed)
        self._filter.textChanged.connect(self._apply_car_filter)
        self._btn_add.clicked.connect(self._add_cars)
        self._btn_remove.clicked.connect(self._remove_cars)
        self._avail_list.itemDoubleClicked.connect(lambda _: self._add_cars())
        self._sel_list.itemDoubleClicked.connect(lambda _: self._remove_cars())
        self._avail_list.currentItemChanged.connect(self._on_avail_selected)
        self._sel_list.currentItemChanged.connect(self._on_sel_selected)

    # ── Track ─────────────────────────────────────────────────────────────────
    def _populate_track_combo(self) -> None:
        self._track_combo.blockSignals(True)
        self._track_combo.clear()
        for t in self._scanner.tracks:
            self._track_combo.addItem(f"{t.folder}  ({t.display_name})", userData=t.folder)
        self._track_combo.blockSignals(False)

    def _on_track_changed(self) -> None:
        folder = self._track_combo.currentData()
        self._layout_combo.blockSignals(True)
        self._layout_combo.clear()
        if folder is not None:
            for t in self._scanner.tracks:
                if t.folder == folder:
                    for lay in t.layouts:
                        label = lay.display_name if lay.config else "(default)"
                        self._layout_combo.addItem(label, userData=lay)
                    break
        self._layout_combo.blockSignals(False)
        self._on_layout_changed()

    def _on_layout_changed(self) -> None:
        lay: TrackLayout | None = self._layout_combo.currentData()
        if lay is not None:
            self._track_info.show_layout(lay)
        else:
            self._track_info.setVisible(False)

    # ── Cars ──────────────────────────────────────────────────────────────────
    def _populate_avail_cars(self) -> None:
        self._all_car_infos = list(self._scanner.cars)
        self._apply_car_filter()

    def _car_icon(self, car: CarInfo) -> QIcon:
        if car.folder not in self._icon_cache:
            pix = _load_pixmap(car.badge_path, _BADGE_SIZE, _BADGE_SIZE)
            self._icon_cache[car.folder] = QIcon(pix) if pix else QIcon()
        return self._icon_cache[car.folder]

    def _make_item(self, car: CarInfo) -> QListWidgetItem:
        parts: list[str] = []
        if car.brand:
            parts.append(car.brand)
        parts.append(car.display_name if car.brand not in car.display_name else
                     car.display_name.replace(car.brand, "").strip() or car.display_name)
        suffix_parts = []
        if car.car_class:
            suffix_parts.append(car.car_class)
        if car.specs.bhp:
            suffix_parts.append(car.specs.bhp)
        suffix = f"  ({', '.join(suffix_parts)})" if suffix_parts else ""
        item = QListWidgetItem(self._car_icon(car), car.display_name + suffix)
        item.setData(Qt.ItemDataRole.UserRole, car.folder)
        item.setData(Qt.ItemDataRole.UserRole + 1, car)
        tip = "\n".join(p for p in [
            car.source,
            f"Class: {car.car_class}" if car.car_class else "",
            f"Year: {car.year}" if car.year else "",
            f"Power: {car.specs.bhp}" if car.specs.bhp else "",
            f"Weight: {car.specs.weight}" if car.specs.weight else "",
        ] if p)
        item.setToolTip(tip)
        return item

    def _apply_car_filter(self) -> None:
        flt = self._filter.text().lower()
        selected_folders = self._selected_folders()
        self._avail_list.clear()
        for car in self._all_car_infos:
            if car.folder in selected_folders:
                continue
            if flt and not any(flt in s.lower() for s in [
                car.folder, car.display_name, car.brand, car.car_class, car.source
            ]):
                continue
            self._avail_list.addItem(self._make_item(car))

    def _selected_folders(self) -> set[str]:
        result: set[str] = set()
        for i in range(self._sel_list.count()):
            it = self._sel_list.item(i)
            if it:
                result.add(str(it.data(Qt.ItemDataRole.UserRole)))
        return result

    def _current_car_folders(self) -> list[str]:
        return [
            str(self._sel_list.item(i).data(Qt.ItemDataRole.UserRole))
            for i in range(self._sel_list.count())
            if self._sel_list.item(i) is not None
        ]

    def _add_cars(self) -> None:
        for item in self._avail_list.selectedItems():
            folder = str(item.data(Qt.ItemDataRole.UserRole))
            if folder not in self._selected_folders():
                car: CarInfo | None = item.data(Qt.ItemDataRole.UserRole + 1)
                if car:
                    self._sel_list.addItem(self._make_item(car))
        self._apply_car_filter()
        self.cars_changed.emit(self._current_car_folders())

    def _remove_cars(self) -> None:
        for item in self._sel_list.selectedItems():
            self._sel_list.takeItem(self._sel_list.row(item))
        self._apply_car_filter()
        self.cars_changed.emit(self._current_car_folders())

    def _on_avail_selected(self, current: QListWidgetItem | None, _: object) -> None:
        if current is None:
            return
        car: CarInfo | None = current.data(Qt.ItemDataRole.UserRole + 1)
        if car:
            self._car_detail.show_car(car)

    def _on_sel_selected(self, current: QListWidgetItem | None, _: object) -> None:
        if current is None:
            return
        car: CarInfo | None = current.data(Qt.ItemDataRole.UserRole + 1)
        if car:
            self._car_detail.show_car(car)

    # ── Public API ────────────────────────────────────────────────────────────
    def populate(self, cfg: PresetConfig) -> None:
        idx = self._track_combo.findData(cfg.track)
        if idx >= 0:
            self._track_combo.setCurrentIndex(idx)
        self._on_track_changed()
        for i in range(self._layout_combo.count()):
            lay: TrackLayout | None = self._layout_combo.itemData(i)
            if lay is not None and lay.config == cfg.config_track:
                self._layout_combo.setCurrentIndex(i)
                break

        self._sel_list.clear()
        for folder in cfg.cars:
            car = self._scanner.car_info(folder)
            if car:
                self._sel_list.addItem(self._make_item(car))
            else:
                item = QListWidgetItem(folder)
                item.setData(Qt.ItemDataRole.UserRole, folder)
                self._sel_list.addItem(item)
        self._apply_car_filter()
        self.cars_changed.emit(self._current_car_folders())

    def collect(self, cfg: PresetConfig) -> None:
        cfg.track = str(self._track_combo.currentData() or "")
        lay: TrackLayout | None = self._layout_combo.currentData()
        cfg.config_track = lay.config if lay else ""
        cfg.cars = self._current_car_folders()
