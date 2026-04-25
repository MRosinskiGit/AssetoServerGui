from pathlib import Path

import pytest


@pytest.fixture
def server_cfg_ini(tmp_path: Path) -> Path:
    cfg = tmp_path / "server_cfg.ini"
    cfg.write_text(
        "[SERVER]\nTCP_PORT=9600\nUDP_PORT=9600\nHTTP_PORT=8081\n",
        encoding="utf-8",
    )
    return tmp_path
