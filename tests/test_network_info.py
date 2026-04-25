import re
from pathlib import Path

from ac_server_gui.core.network_info import get_lan_ip, read_ports_from_cfg

IPV4_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def test_get_lan_ip_returns_ipv4():
    ip = get_lan_ip()
    assert IPV4_RE.match(ip), f"Not an IPv4: {ip!r}"


def test_read_ports_from_cfg(server_cfg_ini: Path):
    ports = read_ports_from_cfg(server_cfg_ini)
    assert ports.tcp == 9600
    assert ports.udp == 9600
    assert ports.http == 8081


def test_read_ports_custom(tmp_path: Path):
    cfg = tmp_path / "server_cfg.ini"
    cfg.write_text("[SERVER]\nTCP_PORT=7777\nUDP_PORT=7778\nHTTP_PORT=8090\n", encoding="utf-8")
    ports = read_ports_from_cfg(tmp_path)
    assert ports.tcp == 7777
    assert ports.udp == 7778
    assert ports.http == 8090
