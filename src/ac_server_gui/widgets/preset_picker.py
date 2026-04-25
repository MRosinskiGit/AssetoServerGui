from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox, QWidget

from ac_server_gui.core.preset_manager import list_presets


class PresetPicker(QComboBox):
    def __init__(self, presets_dir: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._presets_dir = presets_dir
        self.refresh()

    def refresh(self) -> None:
        current = self.currentText()
        self.clear()
        try:
            presets = list_presets(self._presets_dir)
            for p in presets:
                self.addItem(p.name)
            idx = self.findText(current)
            if idx >= 0:
                self.setCurrentIndex(idx)
        except FileNotFoundError:
            pass

    def selected_preset(self) -> str | None:
        text = self.currentText()
        return text if text else None
