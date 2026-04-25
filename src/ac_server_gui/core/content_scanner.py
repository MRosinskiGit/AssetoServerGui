from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CarSpecs:
    bhp: str = ""
    torque: str = ""
    weight: str = ""
    top_speed: str = ""
    acceleration: str = ""
    pw_ratio: str = ""


@dataclass
class CarInfo:
    folder: str
    display_name: str
    brand: str = ""
    car_class: str = ""
    year: str = ""
    country: str = ""
    source: str = ""
    tags: list[str] = field(default_factory=list)
    specs: CarSpecs = field(default_factory=CarSpecs)
    description: str = ""
    badge_path: Path | None = None
    preview_path: Path | None = None  # first available skin preview


@dataclass
class TrackLayout:
    config: str  # empty = default / single layout
    display_name: str
    preview_path: Path | None = None
    outline_path: Path | None = None
    length: str = ""
    pitboxes: str = ""
    country: str = ""
    city: str = ""
    description: str = ""


@dataclass
class TrackInfo:
    folder: str
    display_name: str
    layouts: list[TrackLayout] = field(default_factory=list)


def _read_json(path: Path) -> dict[str, object]:
    try:
        text = path.read_bytes().decode("utf-8", errors="replace")
        data: dict[str, object] = json.loads(text, strict=False)
        return data
    except Exception:
        return {}


def _infer_source(folder: str, data: dict[str, object]) -> str:
    author = str(data.get("author", "")).strip()
    raw_tags = data.get("tags")
    tags = [str(t).lower() for t in (raw_tags if isinstance(raw_tags, list) else [])]
    folder_lower = folder.lower()
    if folder_lower.startswith("ks_") or "kunos" in author.lower():
        return "Kunos Simulazioni"
    if "rss" in tags or "race sim studio" in author.lower():
        return "Race Sim Studio"
    if author:
        return author
    return "Community Mod"


def _first_skin_preview(cars_dir: Path, folder: str) -> Path | None:
    skins_dir = cars_dir / folder / "skins"
    if not skins_dir.exists():
        return None
    for skin in sorted(skins_dir.iterdir()):
        if not skin.is_dir():
            continue
        for name in ("preview.jpg", "preview.png"):
            p = skin / name
            if p.exists():
                return p
    return None


def _layout_images(ui_sub: Path) -> tuple[Path | None, Path | None]:
    preview = ui_sub / "preview.png"
    outline = ui_sub / "outline.png"
    return (preview if preview.exists() else None,
            outline if outline.exists() else None)


class ContentScanner:
    def __init__(self, content_dir: Path) -> None:
        self._dir = content_dir
        self._cars: list[CarInfo] | None = None
        self._tracks: list[TrackInfo] | None = None
        self._weather: list[str] | None = None
        self._car_by_folder: dict[str, CarInfo] = {}

    @property
    def cars(self) -> list[CarInfo]:
        if self._cars is None:
            self._cars = self._scan_cars()
            self._car_by_folder = {c.folder: c for c in self._cars}
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

    def car_display(self, folder: str) -> str:
        self.cars  # ensure scanned
        info = self._car_by_folder.get(folder)
        return info.display_name if info else folder

    def car_info(self, folder: str) -> CarInfo | None:
        self.cars  # ensure scanned
        return self._car_by_folder.get(folder)

    # ------------------------------------------------------------------ private
    def _scan_cars(self) -> list[CarInfo]:
        cars_dir = self._dir / "cars"
        if not cars_dir.exists():
            return []
        result: list[CarInfo] = []
        for d in sorted(cars_dir.iterdir()):
            if not d.is_dir():
                continue
            data = _read_json(d / "ui" / "ui_car.json")
            name = str(data.get("name", "")).strip()
            brand = str(data.get("brand", "")).strip()
            display = f"{brand} {name}".strip() if brand else (name or d.name)
            specs_raw_val = data.get("specs")
            specs_raw: dict[str, object] = (
                specs_raw_val if isinstance(specs_raw_val, dict) else {}
            )
            raw_tags2 = data.get("tags")
            tags = [str(t) for t in (raw_tags2 if isinstance(raw_tags2, list) else [])]
            year_raw = data.get("year")
            badge = d / "ui" / "badge.png"
            result.append(CarInfo(
                folder=d.name,
                display_name=display,
                brand=brand,
                car_class=str(data.get("class", "")).strip(),
                year=str(year_raw) if year_raw else "",
                country=str(data.get("country", "")).strip(),
                source=_infer_source(d.name, data),
                tags=tags,
                specs=CarSpecs(
                    bhp=str(specs_raw.get("bhp", "")),
                    torque=str(specs_raw.get("torque", "")),
                    weight=str(specs_raw.get("weight", "")),
                    top_speed=str(specs_raw.get("topspeed", "")),
                    acceleration=str(specs_raw.get("acceleration", "")),
                    pw_ratio=str(specs_raw.get("pwratio", "")),
                ),
                description=str(data.get("description", "")),
                badge_path=badge if badge.exists() else None,
                preview_path=_first_skin_preview(cars_dir, d.name),
            ))
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
                    if not sub.is_dir():
                        continue
                    json_file = sub / "ui_track.json"
                    if not json_file.exists():
                        continue
                    ld = _read_json(json_file)
                    preview, outline = _layout_images(sub)
                    layouts.append(TrackLayout(
                        config=sub.name,
                        display_name=str(ld.get("name", sub.name)),
                        preview_path=preview,
                        outline_path=outline,
                        length=str(ld.get("length", "")),
                        pitboxes=str(ld.get("pitboxes", "")),
                        country=str(ld.get("country", "")),
                        city=str(ld.get("city", "")),
                        description=str(ld.get("description", "")),
                    ))

                if not layouts:
                    root_json = ui_dir / "ui_track.json"
                    if root_json.exists():
                        rd = _read_json(root_json)
                        display = str(rd.get("name", d.name))
                        preview, outline = _layout_images(ui_dir)
                        layouts.append(TrackLayout(
                            config="",
                            display_name=display,
                            preview_path=preview,
                            outline_path=outline,
                            length=str(rd.get("length", "")),
                            pitboxes=str(rd.get("pitboxes", "")),
                            country=str(rd.get("country", "")),
                            city=str(rd.get("city", "")),
                            description=str(rd.get("description", "")),
                        ))
                    else:
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
