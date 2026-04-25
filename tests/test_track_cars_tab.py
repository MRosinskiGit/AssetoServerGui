"""Tests for TrackCarsTab, _CarDetailPanel, _TrackInfoPanel with real AC content."""
from __future__ import annotations

from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from ac_server_gui.core.content_scanner import (
    CarInfo,
    CarSpecs,
    ContentScanner,
    TrackLayout,
)
from ac_server_gui.widgets.tabs.track_cars_tab import (
    TrackCarsTab,
    _CarDetailPanel,
    _TrackInfoPanel,
)

AC_CONTENT = Path(
    "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/content"
)
REAL_CONTENT_AVAILABLE = AC_CONTENT.exists()


# ---------------------------------------------------------------------------
# _CarDetailPanel — unit
# ---------------------------------------------------------------------------

def test_car_detail_panel_clears_on_init(qtbot: QtBot) -> None:
    panel = _CarDetailPanel()
    qtbot.addWidget(panel)
    assert panel._name_lbl.text() == ""
    assert panel._specs_lbl.text() == ""


def test_car_detail_panel_show_car(qtbot: QtBot) -> None:
    panel = _CarDetailPanel()
    qtbot.addWidget(panel)

    car = CarInfo(
        folder="test_car",
        display_name="Abarth 500",
        brand="Abarth",
        car_class="street",
        year="2012",
        country="Italy",
        source="Kunos Simulazioni",
        tags=["fwd", "street", "turbo"],
        specs=CarSpecs(
            bhp="160bhp",
            torque="230Nm",
            weight="1025kg",
            top_speed="211km/h",
            acceleration="7.4s 0-100",
        ),
    )
    panel.show_car(car)

    assert "Abarth 500" in panel._name_lbl.text()
    assert "street" in panel._meta_lbl.text()
    assert "Italy" in panel._meta_lbl.text()
    assert "Kunos Simulazioni" in panel._source_lbl.text()
    assert "160bhp" in panel._specs_lbl.text()
    assert "230Nm" in panel._specs_lbl.text()
    assert "1025kg" in panel._specs_lbl.text()
    assert "fwd" in panel._tags_lbl.text()


def test_car_detail_panel_no_preview_shows_placeholder(qtbot: QtBot) -> None:
    panel = _CarDetailPanel()
    qtbot.addWidget(panel)
    car = CarInfo(folder="x", display_name="X Car", preview_path=None)
    panel.show_car(car)
    # No crash, image label shows fallback text
    assert panel._img.pixmap().isNull() or "No preview" in (panel._img.text() or "")


def test_car_detail_panel_clear(qtbot: QtBot) -> None:
    panel = _CarDetailPanel()
    qtbot.addWidget(panel)
    car = CarInfo(folder="x", display_name="Test", specs=CarSpecs(bhp="500bhp"))
    panel.show_car(car)
    panel.clear()
    assert panel._name_lbl.text() == ""
    assert panel._specs_lbl.text() == ""


# ---------------------------------------------------------------------------
# _TrackInfoPanel — unit
# ---------------------------------------------------------------------------

def test_track_info_panel_hidden_by_default(qtbot: QtBot) -> None:
    panel = _TrackInfoPanel()
    qtbot.addWidget(panel)
    assert panel.isHidden()


def test_track_info_panel_shows_on_layout(qtbot: QtBot) -> None:
    panel = _TrackInfoPanel()
    qtbot.addWidget(panel)
    lay = TrackLayout(
        config="endurance",
        display_name="Nordschleife - Endurance",
        length="25378",
        pitboxes="12",
        country="Germany",
        city="Nürburg",
    )
    panel.show_layout(lay)
    assert not panel.isHidden()
    assert "Nordschleife - Endurance" in panel._name_lbl.text()
    assert "25378" in panel._stats_lbl.text()
    assert "12" in panel._stats_lbl.text()
    assert "Germany" in panel._stats_lbl.text()


def test_track_info_panel_no_outline_no_crash(qtbot: QtBot) -> None:
    panel = _TrackInfoPanel()
    qtbot.addWidget(panel)
    lay = TrackLayout(config="", display_name="Test Track", outline_path=None)
    panel.show_layout(lay)  # must not raise
    assert not panel.isHidden()


# ---------------------------------------------------------------------------
# TrackCarsTab with mock scanner
# ---------------------------------------------------------------------------

class _FakeScanner:
    @property
    def cars(self) -> list[CarInfo]:
        return [
            CarInfo(
                folder="test_car_a",
                display_name="Brand A Model",
                brand="Brand A",
                car_class="gt3",
                specs=CarSpecs(bhp="500bhp"),
                source="Kunos Simulazioni",
            ),
            CarInfo(
                folder="test_car_b",
                display_name="Brand B Model",
                brand="Brand B",
                car_class="gt4",
                specs=CarSpecs(bhp="350bhp"),
                source="Race Sim Studio",
            ),
        ]

    @property
    def tracks(self) -> list[object]:
        return []

    @property
    def weather_types(self) -> list[str]:
        return []

    def car_info(self, folder: str) -> CarInfo | None:
        return next((c for c in self.cars if c.folder == folder), None)

    def car_display(self, folder: str) -> str:
        info = self.car_info(folder)
        return info.display_name if info else folder

    def skins_for(self, _: str) -> list[str]:
        return []


def test_track_cars_tab_populate_with_cars(qtbot: QtBot) -> None:
    from unittest.mock import MagicMock
    from ac_server_gui.core.preset_config import PresetConfig

    scanner = _FakeScanner()  # type: ignore[arg-type]
    tab = TrackCarsTab(scanner)  # type: ignore[arg-type]
    qtbot.addWidget(tab)

    cfg = MagicMock(spec=PresetConfig)
    cfg.track = ""
    cfg.config_track = ""
    cfg.cars = ["test_car_a"]

    tab.populate(cfg)

    assert tab._sel_list.count() == 1
    assert "Brand A Model" in (tab._sel_list.item(0).text() or "")


def test_track_cars_tab_filter_narrows_avail(qtbot: QtBot) -> None:
    scanner = _FakeScanner()  # type: ignore[arg-type]
    tab = TrackCarsTab(scanner)  # type: ignore[arg-type]
    qtbot.addWidget(tab)

    count_before = tab._avail_list.count()
    tab._filter.setText("Brand A")
    count_after = tab._avail_list.count()
    assert count_after < count_before


def test_track_cars_tab_add_remove_emits_signal(qtbot: QtBot) -> None:
    scanner = _FakeScanner()  # type: ignore[arg-type]
    tab = TrackCarsTab(scanner)  # type: ignore[arg-type]
    qtbot.addWidget(tab)

    emitted: list[list[str]] = []
    tab.cars_changed.connect(emitted.append)

    tab._avail_list.setCurrentRow(0)
    tab._add_cars()
    assert len(emitted) == 1
    assert len(emitted[0]) == 1

    tab._sel_list.setCurrentRow(0)
    tab._remove_cars()
    assert len(emitted) == 2
    assert len(emitted[1]) == 0


def test_track_cars_tab_selecting_car_updates_detail(qtbot: QtBot) -> None:
    scanner = _FakeScanner()  # type: ignore[arg-type]
    tab = TrackCarsTab(scanner)  # type: ignore[arg-type]
    qtbot.addWidget(tab)

    tab._avail_list.setCurrentRow(0)
    # Detail panel should now show car info
    assert "Brand A" in tab._car_detail._name_lbl.text() or \
           "500bhp" in tab._car_detail._specs_lbl.text()


# ---------------------------------------------------------------------------
# Integration: real AC content (skipped if not available)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not REAL_CONTENT_AVAILABLE, reason="AC content not found")
def test_scanner_loads_cars_with_rich_data() -> None:
    scanner = ContentScanner(AC_CONTENT)
    cars = scanner.cars
    assert len(cars) > 100

    kunos = [c for c in cars if c.source == "Kunos Simulazioni"]
    rss = [c for c in cars if c.source == "Race Sim Studio"]
    assert len(kunos) > 0, "No Kunos cars found"
    assert len(rss) > 0, "No RSS cars found"

    with_badge = [c for c in cars if c.badge_path is not None]
    with_preview = [c for c in cars if c.preview_path is not None]
    assert len(with_badge) > len(cars) * 0.8, "Less than 80% of cars have badges"
    assert len(with_preview) > len(cars) * 0.5, "Less than 50% of cars have previews"


@pytest.mark.skipif(not REAL_CONTENT_AVAILABLE, reason="AC content not found")
def test_scanner_loads_track_layouts_with_images() -> None:
    scanner = ContentScanner(AC_CONTENT)
    tracks = scanner.tracks
    assert len(tracks) > 0

    nord = next((t for t in tracks if t.folder == "ks_nordschleife"), None)
    assert nord is not None
    assert len(nord.layouts) >= 4
    layouts_with_outline = [lay for lay in nord.layouts if lay.outline_path is not None]
    assert len(layouts_with_outline) > 0

    endu = next((lay for lay in nord.layouts if lay.config == "endurance"), None)
    assert endu is not None
    assert endu.length != ""
    assert endu.country != ""


@pytest.mark.skipif(not REAL_CONTENT_AVAILABLE, reason="AC content not found")
def test_real_track_cars_tab_opens_without_crash(qtbot: QtBot) -> None:
    scanner = ContentScanner(AC_CONTENT)
    tab = TrackCarsTab(scanner)
    qtbot.addWidget(tab)
    tab.show()
    assert tab.isVisible()
    # Lists should be populated
    assert tab._avail_list.count() > 100
    assert tab._track_combo.count() > 0


@pytest.mark.skipif(not REAL_CONTENT_AVAILABLE, reason="AC content not found")
def test_real_car_detail_shows_on_selection(qtbot: QtBot) -> None:
    scanner = ContentScanner(AC_CONTENT)
    tab = TrackCarsTab(scanner)
    qtbot.addWidget(tab)

    tab._avail_list.setCurrentRow(0)
    # After selecting first available car, detail panel must show something
    assert tab._car_detail._name_lbl.text() != ""


@pytest.mark.skipif(not REAL_CONTENT_AVAILABLE, reason="AC content not found")
def test_real_track_info_shows_on_selection(qtbot: QtBot) -> None:
    scanner = ContentScanner(AC_CONTENT)
    tab = TrackCarsTab(scanner)
    qtbot.addWidget(tab)

    # Select Nordschleife (find its index)
    idx = tab._track_combo.findData("ks_nordschleife")
    if idx >= 0:
        tab._track_combo.setCurrentIndex(idx)
    # isHidden() reflects the widget's own flag regardless of parent visibility
    assert not tab._track_info.isHidden()
    assert "Nordschleife" in tab._track_info._name_lbl.text()
