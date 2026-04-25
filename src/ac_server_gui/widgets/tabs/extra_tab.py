from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.extra_cfg_generator import (
    PLUGIN_DEFS,
    ExtraCfgData,
    PluginConfig,
    generate_extra_cfg,
    parse_extra_cfg,
)
from ac_server_gui.core.preset_config import PresetConfig


class ExtraTab(QWidget):
    """Plugin-driven editor that generates extra_cfg.yml."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._global_api_key: str = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Core settings ---
        core_box = QGroupBox("Core AssettoServer Settings")
        core_form = QFormLayout(core_box)
        self._weather_fx = QCheckBox("Enable WeatherFX (smooth weather transitions & rain via CSP)")
        self._real_time = QCheckBox("Enable Real Time (sync server clock with wall clock)")
        self._csp_version = QLineEdit()
        self._csp_version.setPlaceholderText("e.g. 1937  (leave empty = no requirement)")
        self._csp_version.setToolTip(
            "Minimum CSP version required to join.\n"
            "1937 = CSP 0.1.77.  Leave empty to allow any version."
        )
        self._server_desc = QLineEdit()
        self._server_desc.setPlaceholderText("Shown in Content Manager (BBCode supported)")
        core_form.addRow("", self._weather_fx)
        core_form.addRow("", self._real_time)
        core_form.addRow("Min CSP version:", self._csp_version)
        core_form.addRow("Server description:", self._server_desc)
        layout.addWidget(core_box)

        # --- Plugins ---
        plugins_label = QLabel("Plugins  (check to enable, click to configure):")
        layout.addWidget(plugins_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: plugin list with checkboxes
        self._plugin_list = QListWidget()
        self._plugin_list.setMinimumWidth(220)
        self._plugin_list.setMaximumWidth(300)
        for pdef in PLUGIN_DEFS:
            item = QListWidgetItem(pdef.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setToolTip(pdef.description)
            self._plugin_list.addItem(item)
        splitter.addWidget(self._plugin_list)

        # Right: plugin config form
        self._config_area = QScrollArea()
        self._config_area.setWidgetResizable(True)
        self._config_placeholder = QLabel("Select a plugin to configure it.")
        self._config_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._config_placeholder.setStyleSheet("color: #888;")
        self._config_area.setWidget(self._config_placeholder)
        splitter.addWidget(self._config_area)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)

        # Per-plugin field widgets: {plugin_name: {field_key: QLineEdit|QSpinBox}}
        self._plugin_widgets: dict[str, dict[str, QWidget]] = {}
        self._plugin_config_panels: dict[str, QWidget] = {}
        self._build_plugin_panels()

        self._plugin_list.currentRowChanged.connect(self._on_plugin_selected)
        self._plugin_list.itemChanged.connect(self._on_plugin_toggled)

    def _build_plugin_panels(self) -> None:
        for pdef in PLUGIN_DEFS:
            panel: QWidget
            if not pdef.fields:
                lbl = QLabel(
                    f"<b>{pdef.name}</b><br><br>{pdef.description}<br><br>"
                    "No configuration options — just enable the checkbox to activate."
                )
                lbl.setWordWrap(True)
                lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
                lbl.setMargin(12)
                panel = lbl
            else:
                panel = QWidget()
                v = QVBoxLayout(panel)
                v.setContentsMargins(8, 8, 8, 8)
                desc_lbl = QLabel(f"<b>{pdef.name}</b><br><small>{pdef.description}</small>")
                desc_lbl.setWordWrap(True)
                v.addWidget(desc_lbl)
                box = QGroupBox("Configuration")
                form = QFormLayout(box)
                field_widgets: dict[str, QWidget] = {}
                for fdef in pdef.fields:
                    if fdef.is_int:
                        spin = QSpinBox()
                        spin.setRange(0, 999999)
                        try:
                            spin.setValue(int(fdef.default))
                        except ValueError:
                            pass
                        w: QWidget = spin
                    else:
                        w = QLineEdit()
                    if fdef.description:
                        w.setToolTip(fdef.description)
                    form.addRow(f"{fdef.label}:", w)
                    field_widgets[fdef.key] = w
                v.addWidget(box)
                v.addStretch()
                self._plugin_widgets[pdef.name] = field_widgets
            self._plugin_config_panels[pdef.name] = panel

    def _on_plugin_selected(self, row: int) -> None:
        if row < 0 or row >= len(PLUGIN_DEFS):
            return
        pdef = PLUGIN_DEFS[row]
        panel = self._plugin_config_panels[pdef.name]
        self._config_area.setWidget(panel)

    def _on_plugin_toggled(self, item: QListWidgetItem) -> None:
        pass  # dirty tracking handled by config_editor

    def set_global_api_key(self, key: str) -> None:
        """Update the global OpenWeatherMap key used as default for LiveWeatherPlugin."""
        self._global_api_key = key
        # If the LiveWeatherPlugin API key field is currently empty, fill it in now.
        widgets = self._plugin_widgets.get("LiveWeatherPlugin", {})
        w = widgets.get("OpenWeatherMapApiKey")
        if isinstance(w, QLineEdit) and not w.text():
            w.setText(key)

    # ------------------------------------------------------------------ public API
    def populate(self, cfg: PresetConfig) -> None:
        data = parse_extra_cfg(cfg.extra_cfg_text())
        self._weather_fx.setChecked(data.enable_weather_fx)
        self._real_time.setChecked(data.enable_real_time)
        self._csp_version.setText(data.minimum_csp_version)
        self._server_desc.setText(data.server_description)

        enabled_map = {p.name: p for p in data.plugins}
        for row in range(self._plugin_list.count()):
            item = self._plugin_list.item(row)
            if item is None:
                continue
            pname = item.text()
            pconf = enabled_map.get(pname)
            state = Qt.CheckState.Checked if (pconf and pconf.enabled) else Qt.CheckState.Unchecked
            item.setCheckState(state)
            field_widgets = self._plugin_widgets.get(pname, {})
            if pconf:
                for key, widget in field_widgets.items():
                    val = pconf.fields.get(key, "")
                    if isinstance(widget, QSpinBox):
                        try:
                            widget.setValue(int(val))
                        except ValueError:
                            pass
                    elif isinstance(widget, QLineEdit):
                        widget.setText(val)

        # Fall back to global key when the preset has no key stored
        widgets = self._plugin_widgets.get("LiveWeatherPlugin", {})
        api_w = widgets.get("OpenWeatherMapApiKey")
        if isinstance(api_w, QLineEdit) and not api_w.text() and self._global_api_key:
            api_w.setText(self._global_api_key)

    def collect(self, cfg: PresetConfig) -> None:
        plugins: list[PluginConfig] = []
        for row in range(self._plugin_list.count()):
            item = self._plugin_list.item(row)
            if item is None:
                continue
            pname = item.text()
            enabled = item.checkState() == Qt.CheckState.Checked
            fields: dict[str, str] = {}
            for key, widget in self._plugin_widgets.get(pname, {}).items():
                if isinstance(widget, QSpinBox):
                    fields[key] = str(widget.value())
                elif isinstance(widget, QLineEdit):
                    fields[key] = widget.text()
            plugins.append(PluginConfig(name=pname, enabled=enabled, fields=fields))

        data = ExtraCfgData(
            enable_real_time=self._real_time.isChecked(),
            enable_weather_fx=self._weather_fx.isChecked(),
            minimum_csp_version=self._csp_version.text().strip(),
            server_description=self._server_desc.text(),
            plugins=plugins,
        )
        cfg.extra_cfg_save(generate_extra_cfg(data))
