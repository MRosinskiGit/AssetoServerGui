from __future__ import annotations

import configparser
import socket
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Ports:
    tcp: int
    udp: int
    http: int


def get_lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return str(s.getsockname()[0])
    except OSError:
        return "127.0.0.1"


def read_ports_from_cfg(preset_path: Path) -> Ports:
    cfg_file = preset_path / "server_cfg.ini"
    parser = configparser.ConfigParser()
    parser.optionxform = lambda x: x  # type: ignore[method-assign, assignment]
    parser.read(cfg_file, encoding="utf-8")
    section = parser["SERVER"]
    return Ports(
        tcp=int(section["TCP_PORT"]),
        udp=int(section["UDP_PORT"]),
        http=int(section["HTTP_PORT"]),
    )
