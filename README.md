# AC Server GUI

Desktop GUI manager for **AssettoServer** (compujuckel fork) on Windows. Start, stop, and monitor a LAN-only Assetto Corsa server with live log streaming and connection info.

## Prerequisites

- Python 3.11+
- AssettoServer installed at the default Steam path (or configure `app_config.yml`)
- Windows 10/11

## Installation

```bat
py -3.11 -m venv .venv
.venv\Scripts\pip install -e .[dev]
```

## Running

```bat
run.bat
```

Or:

```bat
.venv\Scripts\python -m ac_server_gui
```

## Configuration

Edit `app_config.yml` to change server paths:

```yaml
server_exe: "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/server/acServer.exe"
server_dir: "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/server"
presets_dir: "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/server/presets"
logs_dir: "logs"
```

## Usage

1. Select a preset from the dropdown
2. Click **Start** — logs stream in real time, status indicator turns green when ready
3. LAN info panel shows the IP + ports for connecting via Content Manager → Add server by IP
4. Click **Stop** to shut down the server
5. Closing while the server runs shows a dialog: Stop / Leave running / Cancel

> **First run**: Windows Firewall will prompt you to allow `acServer.exe` — click Allow.

## Testing

```bat
# Unit tests
.venv\Scripts\pytest -v

# Integration test (launches the real server, ~13 s)
.venv\Scripts\pytest -m integration -v

# Lint
.venv\Scripts\ruff check src tests

# Type check
.venv\Scripts\mypy src
```

## Log files

Each server session is archived to `logs/server_YYYYMMDD_HHMMSS.log`.
