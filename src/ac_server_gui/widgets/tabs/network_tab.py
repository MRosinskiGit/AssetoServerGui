from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ac_server_gui.core.preset_config import PresetConfig


class NetworkTab(QWidget):
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

        ports_box = QGroupBox("Ports  (firewall must allow these)")
        form = QFormLayout(ports_box)
        self._udp = self._port_spin()
        self._tcp = self._port_spin()
        self._http = self._port_spin()
        self._note = QLabel("TCP port must equal UDP port (AssettoServer requirement).")
        self._note.setStyleSheet("color: #FFA500;")
        form.addRow("UDP port:", self._udp)
        form.addRow("TCP port:", self._tcp)
        form.addRow("HTTP port:", self._http)
        form.addRow("", self._note)
        layout.addWidget(ports_box)

        perf_box = QGroupBox("Performance")
        pform = QFormLayout(perf_box)
        self._threads = QSpinBox()
        self._threads.setRange(1, 64)
        self._client_hz = QSpinBox()
        self._client_hz.setRange(1, 60)
        self._client_hz.setSuffix(" Hz")
        self._sleep = QSpinBox()
        self._sleep.setRange(0, 100)
        self._sleep.setSuffix(" ms")
        pform.addRow("Server threads:", self._threads)
        pform.addRow("Client send interval:", self._client_hz)
        pform.addRow("Server sleep time:", self._sleep)
        layout.addWidget(perf_box)
        layout.addStretch()

        self._udp.valueChanged.connect(self._sync_tcp)

    def _sync_tcp(self, val: int) -> None:
        self._tcp.blockSignals(True)
        self._tcp.setValue(val)
        self._tcp.blockSignals(False)

    @staticmethod
    def _port_spin() -> QSpinBox:
        s = QSpinBox()
        s.setRange(1024, 65535)
        return s

    def populate(self, cfg: PresetConfig) -> None:
        self._udp.setValue(cfg.udp_port)
        self._tcp.setValue(cfg.tcp_port)
        self._http.setValue(cfg.http_port)
        self._threads.setValue(cfg.num_threads)
        self._client_hz.setValue(cfg.client_send_interval_hz)
        self._sleep.setValue(cfg.sleep_time)

    def collect(self, cfg: PresetConfig) -> None:
        cfg.udp_port = self._udp.value()
        cfg.tcp_port = self._tcp.value()
        cfg.http_port = self._http.value()
        cfg.num_threads = self._threads.value()
        cfg.client_send_interval_hz = self._client_hz.value()
        cfg.sleep_time = self._sleep.value()
