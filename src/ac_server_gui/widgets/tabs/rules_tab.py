from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.preset_config import PresetConfig


class RulesTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        inner = QWidget()
        scroll.setWidget(inner)
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(12, 12, 12, 12)

        # Damage/fuel
        dmg_box = QGroupBox("Simulation")
        form1 = QFormLayout(dmg_box)
        self._fuel = self._pct_spin()
        self._damage = self._pct_spin()
        self._tyre_wear = self._pct_spin()
        self._tyres_out = QSpinBox()
        self._tyres_out.setRange(-1, 4)
        self._tyres_out.setSpecialValueText("No limit (-1)")
        form1.addRow("Fuel rate (%):", self._fuel)
        form1.addRow("Damage multiplier (%):", self._damage)
        form1.addRow("Tyre wear rate (%):", self._tyre_wear)
        form1.addRow("Wheels off track allowed:", self._tyres_out)
        layout.addWidget(dmg_box)

        # Race rules
        race_box = QGroupBox("Race Rules")
        form2 = QFormLayout(race_box)
        self._start_rule = QComboBox()
        for o in ["Locked grid (0)", "Teleport to grid (1)", "Drive-through (2)"]:
            self._start_rule.addItem(o)
        self._reversed_grid = QSpinBox()
        self._reversed_grid.setRange(-1, 99)
        self._reversed_grid.setSpecialValueText("Fully reversed (-1)")
        self._reversed_grid.setToolTip("0 = no reversal; N = reverse first N positions; -1 = all")
        self._race_over_time = QSpinBox()
        self._race_over_time.setRange(0, 9999)
        self._race_over_time.setSuffix(" s")
        self._result_screen = QSpinBox()
        self._result_screen.setRange(0, 9999)
        self._result_screen.setSuffix(" s")
        self._gas_penalty = QCheckBox("Disable throttle-cut gas penalty")
        self._max_contacts = QSpinBox()
        self._max_contacts.setRange(-1, 9999)
        self._max_contacts.setSpecialValueText("No limit (-1)")
        form2.addRow("Race start type:", self._start_rule)
        form2.addRow("Reversed grid positions:", self._reversed_grid)
        form2.addRow("Race over time:", self._race_over_time)
        form2.addRow("Result screen time:", self._result_screen)
        form2.addRow("", self._gas_penalty)
        form2.addRow("Max contacts/km:", self._max_contacts)
        layout.addWidget(race_box)

        # Voting/admin
        vote_box = QGroupBox("Voting & Moderation")
        form3 = QFormLayout(vote_box)
        self._kick_quorum = self._pct_spin()
        self._voting_quorum = self._pct_spin()
        self._vote_duration = QSpinBox()
        self._vote_duration.setRange(1, 300)
        self._vote_duration.setSuffix(" s")
        self._blacklist_mode = QComboBox()
        self._blacklist_mode.addItem("By Steam name (0)")
        self._blacklist_mode.addItem("By Steam ID (1)")
        form3.addRow("Kick quorum (%):", self._kick_quorum)
        form3.addRow("Voting quorum (%):", self._voting_quorum)
        form3.addRow("Vote duration:", self._vote_duration)
        form3.addRow("Blacklist mode:", self._blacklist_mode)
        layout.addWidget(vote_box)

        layout.addStretch()

    @staticmethod
    def _pct_spin() -> QSpinBox:
        s = QSpinBox()
        s.setRange(0, 999)
        s.setSuffix("%")
        return s

    def populate(self, cfg: PresetConfig) -> None:
        self._fuel.setValue(cfg.fuel_rate)
        self._damage.setValue(cfg.damage_multiplier)
        self._tyre_wear.setValue(cfg.tyre_wear_rate)
        self._tyres_out.setValue(cfg.allowed_tyres_out)
        self._start_rule.setCurrentIndex(max(0, min(2, cfg.start_rule)))
        self._reversed_grid.setValue(cfg.reversed_grid_positions)
        self._race_over_time.setValue(cfg.race_over_time)
        self._result_screen.setValue(cfg.result_screen_time)
        self._gas_penalty.setChecked(cfg.race_gas_penalty_disabled)
        self._max_contacts.setValue(cfg.max_contacts_per_km)
        self._kick_quorum.setValue(cfg.kick_quorum)
        self._voting_quorum.setValue(cfg.voting_quorum)
        self._vote_duration.setValue(cfg.vote_duration)
        self._blacklist_mode.setCurrentIndex(max(0, min(1, cfg.blacklist_mode)))

    def collect(self, cfg: PresetConfig) -> None:
        cfg.fuel_rate = self._fuel.value()
        cfg.damage_multiplier = self._damage.value()
        cfg.tyre_wear_rate = self._tyre_wear.value()
        cfg.allowed_tyres_out = self._tyres_out.value()
        cfg.start_rule = self._start_rule.currentIndex()
        cfg.reversed_grid_positions = self._reversed_grid.value()
        cfg.race_over_time = self._race_over_time.value()
        cfg.result_screen_time = self._result_screen.value()
        cfg.race_gas_penalty_disabled = self._gas_penalty.isChecked()
        cfg.max_contacts_per_km = self._max_contacts.value()
        cfg.kick_quorum = self._kick_quorum.value()
        cfg.voting_quorum = self._voting_quorum.value()
        cfg.vote_duration = self._vote_duration.value()
        cfg.blacklist_mode = self._blacklist_mode.currentIndex()
