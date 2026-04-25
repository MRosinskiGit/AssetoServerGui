from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CarInfo:
    folder: str
    display_name: str


@dataclass
class TrackLayout:
    config: str  # empty = default / single layout
    display_name: str


@dataclass
class TrackInfo:
    folder: str
    display_name: str
    layouts: list[TrackLayout] = field(default_factory=list)


def _read_json(path: Path) -> dict[str, object]:
    try:
        data: dict[str, object] = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data
    except Exception:
        return {}


class ContentScanner:
    def __init__(self, content_dir: Path) -> None:
        self._dir = content_dir
        self._cars: list[CarInfo] | None = None
        self._tracks: list[TrackInfo] | None = None
        self._weather: list[str] | None = None

    @property
    def cars(self) -> list[CarInfo]:
        if self._cars is None:
            self._cars = self._scan_cars()
        return self._cars

    @property
    def tracks(self) -> list[TrackInfo]:
        if self._tracks is None:
            self._tracks = self._scan_tracks()
        return self._tracks

    @property
    def weather_types(self) -> list[str]:
        if self._weather is None:
            self._weather = self._scan_weather()
        return self._weather

    def skins_for(self, car_folder: str) -> list[str]:
        skins_dir = self._dir / "cars" / car_folder / "skins"
        if not skins_dir.exists():
            return []
        return sorted(p.name for p in skins_dir.iterdir() if p.is_dir())

    def _scan_cars(self) -> list[CarInfo]:
        cars_dir = self._dir / "cars"
        if not cars_dir.exists():
            return []
        result: list[CarInfo] = []
        for d in sorted(cars_dir.iterdir()):
            if not d.is_dir():
                continue
            display = d.name
            data = _read_json(d / "ui" / "ui_car.json")
            name = str(data.get("name", ""))
            brand = str(data.get("brand", ""))
            if name:
                display = f"{brand} {name}".strip() if brand else name
            result.append(CarInfo(folder=d.name, display_name=display))
        return result

    def _scan_tracks(self) -> list[TrackInfo]:
        tracks_dir = self._dir / "tracks"
        if not tracks_dir.exists():
            return []
        result: list[TrackInfo] = []
        for d in sorted(tracks_dir.iterdir()):
            if not d.is_dir():
                continue
            ui_dir = d / "ui"
            display = d.name
            layouts: list[TrackLayout] = []

            if ui_dir.exists():
                for sub in sorted(ui_dir.iterdir()):
                    if sub.is_dir() and (sub / "ui_track.json").exists():
                        sub_data = _read_json(sub / "ui_track.json")
                        layouts.append(
                            TrackLayout(
                                config=sub.name,
                                display_name=str(sub_data.get("name", sub.name)),
                            )
                        )
                if not layouts:
                    root_json = ui_dir / "ui_track.json"
                    if root_json.exists():
                        root_data = _read_json(root_json)
                        display = str(root_data.get("name", d.name))
                    layouts.append(TrackLayout(config="", display_name=display))
            else:
                layouts.append(TrackLayout(config="", display_name=display))

            result.append(TrackInfo(folder=d.name, display_name=display, layouts=layouts))
        return result

    def _scan_weather(self) -> list[str]:
        weather_dir = self._dir / "weather"
        if not weather_dir.exists():
            return []
        return sorted(d.name for d in weather_dir.iterdir() if d.is_dir())

    def car_display(self, folder: str) -> str:
        for c in self.cars:
            if c.folder == folder:
                return c.display_name
        return folder
