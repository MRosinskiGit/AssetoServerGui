from pathlib import Path

import pytest

from ac_server_gui.core.preset_manager import copy_preset, list_presets


def test_list_presets(tmp_path: Path):
    (tmp_path / "PRESET_A").mkdir()
    (tmp_path / "PRESET_B").mkdir()
    (tmp_path / "not_a_dir.txt").write_text("x")
    presets = list_presets(tmp_path)
    names = [p.name for p in presets]
    assert names == ["PRESET_A", "PRESET_B"]


def test_list_presets_empty(tmp_path: Path):
    assert list_presets(tmp_path) == []


def test_list_presets_nonexistent(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        list_presets(tmp_path / "does_not_exist")


def test_list_presets_ignores_files(tmp_path: Path):
    (tmp_path / "myfile.ini").write_text("x")
    presets = list_presets(tmp_path)
    assert presets == []


def test_copy_preset(tmp_path: Path):
    src = tmp_path / "SRC"
    src.mkdir()
    (src / "server_cfg.ini").write_text("[SERVER]\n")
    dst = tmp_path / "DST"
    copy_preset(src, dst)
    assert (dst / "server_cfg.ini").exists()


def test_copy_preset_overwrites_existing(tmp_path: Path):
    src = tmp_path / "SRC"
    src.mkdir()
    (src / "file.txt").write_text("new")
    dst = tmp_path / "DST"
    dst.mkdir()
    (dst / "old.txt").write_text("old")
    copy_preset(src, dst)
    assert not (dst / "old.txt").exists()
    assert (dst / "file.txt").exists()
