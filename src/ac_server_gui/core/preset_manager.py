from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PresetInfo:
    name: str
    path: Path


def list_presets(presets_dir: Path) -> list[PresetInfo]:
    if not presets_dir.exists():
        raise FileNotFoundError(f"Presets directory not found: {presets_dir}")
    return sorted(
        [PresetInfo(name=p.name, path=p) for p in presets_dir.iterdir() if p.is_dir()],
        key=lambda p: p.name,
    )


def copy_preset(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
