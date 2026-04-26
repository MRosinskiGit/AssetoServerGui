# AC Server GUI

> 🎵✨ **Vibecoded.** This project is still under active vibedebugging 🔍🐛 and vibefixing 🔧💫 ✨🎵

Desktop GUI manager for [AssettoServer](https://github.com/compujuckel/AssettoServer/) (compujuckel fork) on Windows.  
Manage Assetto Corsa server presets, configure every aspect of the server from a graphical interface, start/stop the server, and monitor live logs — all in one window.

---

## Requirements

- Windows 10 / 11
- Python 3.11+
- Assetto Corsa + AssettoServer installed (default Steam path, or edit `app_config.yml`)

---

## Installation

```bat
py -3.11 -m venv .venv
.venv\Scripts\pip install -e .[dev]
```

---

## Running

```bat
run.bat
```

Or directly:

```bat
.venv\Scripts\python -m ac_server_gui
```

> **First run:** Windows Firewall will prompt you to allow `acServer.exe` through the firewall. Click **Allow access**.

---

## Configuration (`app_config.yml`)

```yaml
server_exe:   "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/server/acServer.exe"
server_dir:   "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/server"
presets_dir:  "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/server/presets"
content_dir:  "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/content"
logs_dir:     "logs"
openweathermap_api_key: ""   # set once here, or via ⚙ Settings in the app
```

All paths can be changed to match a non-default Steam installation.  
`openweathermap_api_key` is a global default — set it once and it is pre-filled in every preset's LiveWeatherPlugin configuration.

---

## Layout

```
┌─────────────────┬────────────────────────────────────────────┐
│  Preset         │  Monitor  │  Configuration                  │
│  [dropdown]     │                                             │
│  [New] [Copy]   │  Live log viewer with colour-coded output   │
│                 │                                             │
│  [▶ Start]      │  ── or ──                                   │
│  [■ Stop]       │                                             │
│  ● Running      │  10-tab config editor (see below)           │
│                 │                                             │
│  LAN info       │                                             │
│  IP / ports     │                                             │
│                 │                                             │
│  [⚙ Settings]  │                                             │
└─────────────────┴────────────────────────────────────────────┘
```

---

## Server Control

| Action | Result |
|--------|--------|
| Select preset → **Start** | Launches `acServer.exe -p <preset>`, streams stdout to the log viewer |
| Status indicator | `Stopped` / `Starting` / `Running` (detected from "Starting update loop" log line) / `Crashed` |
| **Stop** | Sends `terminate()`, waits 5 s, then `kill()` if still running |
| Close while running | Dialog: **Stop server** / **Leave running** / **Cancel** |
| Unsaved config changes + Start | Prompts: **Save & Start** / **Start without saving** / **Cancel** |

**LAN connection:** once running, the left panel shows your local IP and the TCP/UDP/HTTP ports. Enter these in Content Manager → Servers → Add server by IP.

---

## Configuration Editor

Select a preset and switch to the **Configuration** tab. All changes are written to disk only when you click **Save Config**. Editing is locked while the server is running.

### Tabs

| Tab | What you can change |
|-----|---------------------|
| **General** | Server name, password, admin password, max clients, pickup/loop/locked/lobby mode |
| **Track & Cars** | Track + layout picker (scans your AC content folder), dual-list car selector with search filter |
| **Sessions** | Practice, Qualifying, Race — enable/disable, duration or lap count, wait time, join policy |
| **Assists** | ABS (off/factory/any), TC, stability control, auto-clutch, tyre blankets, virtual mirror |
| **Rules** | Fuel rate, damage, tyre wear, wheels-off-track limit, start type, reversed grid, race-over time, kick/vote settings, blacklist mode |
| **Weather** | Multiple weather slots (add/remove), per-slot: graphics folder, ambient & road temperature with ±variation, wind speed/direction |
| **Track Grip** | Dynamic track rubber-in: enable/disable, session start grip, randomness, session transfer, laps-per-1%-gain |
| **Network** | UDP/TCP ports (TCP auto-syncs to UDP), HTTP port, server threads, client send rate |
| **Entry List** | Table of car slots — model (dropdown from CARS= list), skin (dropdown per model), AI mode, ballast, restrictor, driver name, GUID. Updating the car list in Track & Cars instantly updates all model dropdowns here. |
| **AssettoServer** | Core toggles (WeatherFX, Real Time, min CSP version, server description) + plugin manager |

### Sessions — Race type

For the Race session, choose **Lap race** (fixed lap count) or **Timed race** (duration in minutes). The inactive field is hidden to avoid confusion.

### Weather — Time of Day

The **Start time** field uses a standard `HH:MM` clock.  
Internally converted to/from `SUN_ANGLE` using the AC formula:

```
SUN_ANGLE = 16 × (time_seconds − 46800) / 3600
```

Examples: `00:00 → −208`, `08:00 → −80`, `13:00 → 0`, `18:00 → +80`

### AssettoServer Plugins

Enable plugins with a checkbox; click the plugin name to configure it:

| Plugin | Notes |
|--------|-------|
| **LiveWeatherPlugin** | Requires an OpenWeatherMap API key (free). Set globally via ⚙ Settings. |
| **RandomWeatherPlugin** | Randomises weather with smooth WeatherFX transitions. Requires `EnableWeatherFx: true`. |
| **AutoModerationPlugin** | Auto-kicks assists/damage/fuel violations. |
| **DiscordAuditPlugin** | Sends chat + moderation events to a Discord webhook. |
| **VotingWeatherPlugin** | Players vote on next weather. |
| **TimeDilationPlugin** | Adjusts time multiplier based on sun position. |
| **RaceChallengePlugin** | Headlight-flash challenge system. |
| **WordFilterPlugin** | Chat and name filter from a word-list file. |
| **GeoIPPlugin** | Logs player countries. |

`extra_cfg.yml` is fully regenerated from the UI on save, preserving all enabled plugin configurations.

### Preset Management

| Button | Action |
|--------|--------|
| **New** | Creates a new preset by copying `SERVER_01` as template, then opens it in the editor |
| **Copy** | Duplicates the currently selected preset under a new name |

---

## Global OpenWeatherMap API Key

1. Click **⚙ Settings** in the left panel.
2. Paste your API key (free tier at [openweathermap.org](https://home.openweathermap.org/api_keys)).
3. Click **OK** — the key is saved to `app_config.yml`.

From that point on, whenever you open a preset whose LiveWeatherPlugin API key is empty, the field is pre-filled from the global key automatically.

---

## Log Files

Each server session is archived to `logs/server_YYYYMMDD_HHMMSS.log`.

Log lines are colour-coded:

| Colour | Meaning |
|--------|---------|
| White | INFO |
| Grey | DEBUG |
| Orange | WARNING |
| Red | ERROR |
| Green | Server ready (`Starting update loop`) |
| Blue | Player joining |
| Orange-red | Player leaving |

Auto-scroll pauses when you scroll up, resumes when you scroll back to the bottom.

---

## Testing

```bat
# Unit tests  (fast, no server required)
.venv\Scripts\pytest -v

# Integration tests  (launches the real server, ~5 min for all 26 tests)
.venv\Scripts\pytest -m integration -v

# Lint
.venv\Scripts\ruff check src tests

# Type check
.venv\Scripts\mypy src
```

Integration tests cover: baseline boot, session combinations (practice-only, qualify-only, race-only, all three), assists on/off, damage/fuel/tyre wear, dynamic track, single/multi weather slots, custom ports, pickup mode, loop mode, server name, start rule, entry-list sizes, AI slots, extra_cfg plugins (no plugins, RaceChallenge, RandomWeather, LiveWeather), and a full config round-trip.

---

## Project Structure

```
ac-server-gui/
├── app_config.yml              global paths and API key
├── run.bat                     launch shortcut
├── src/ac_server_gui/
│   ├── core/
│   │   ├── config.py           AppConfig, load_config, save_config
│   │   ├── content_scanner.py  scan AC install for cars, tracks, skins, weather
│   │   ├── extra_cfg_generator.py  plugin definitions, YAML parser & generator
│   │   ├── log_parser.py       classify log lines → LogEvent
│   │   ├── network_info.py     LAN IP, read ports from server_cfg.ini
│   │   ├── preset_config.py    read/write server_cfg.ini + entry_list.ini
│   │   ├── preset_manager.py   list/copy presets
│   │   └── server_process.py   QProcess wrapper, state machine
│   ├── widgets/
│   │   ├── config_editor.py    10-tab config editor container
│   │   ├── log_viewer.py       colourised live log, auto-scroll, archive
│   │   ├── preset_picker.py    preset dropdown
│   │   ├── status_panel.py     Stopped/Starting/Running/Crashed indicator
│   │   └── tabs/               one file per config tab
│   └── main_window.py          main window, server control, settings dialog
├── tests/
│   ├── test_*.py               unit tests (83 tests)
│   └── integration/            server-launch integration tests (26 tests)
└── logs/                       archived session logs
```
