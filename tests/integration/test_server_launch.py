"""Integration tests: launch the real acServer.exe under various configurations."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from ac_server_gui.core.config import load_config
from ac_server_gui.core.preset_config import PresetConfig
from ac_server_gui.core.preset_manager import copy_preset
from ac_server_gui.core.server_process import ServerProcess, ServerState

# ---------------------------------------------------------------------------
SERVER_01 = Path(
    "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/server/presets/SERVER_01"
)
PRESETS_DIR = Path(
    "C:/Program Files (x86)/Steam/steamapps/common/assettocorsa/server/presets"
)
_READY_TIMEOUT = 35_000  # ms


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sess(name: str, enabled: bool, **kw: str) -> tuple[str, bool, dict[str, str]]:
    """Build args for cfg.session_save."""
    return (name, enabled, kw)


def _make_preset(name: str, modifier=None) -> Path:
    """Copy SERVER_01 to a fresh test preset, optionally mutate with modifier(cfg)."""
    dst = PRESETS_DIR / name
    copy_preset(SERVER_01, dst)
    if modifier:
        cfg = PresetConfig(dst)
        modifier(cfg)
        cfg.save()
    return dst


def _cleanup(name: str) -> None:
    p = PRESETS_DIR / name
    if p.exists():
        shutil.rmtree(p)


def _launch_and_wait(
    qtbot: QtBot, preset_name: str
) -> tuple[ServerProcess, list[str], list[ServerState]]:
    config = load_config()
    proc = ServerProcess()
    lines: list[str] = []
    states: list[ServerState] = []
    proc.output_line.connect(lines.append)
    proc.state_changed.connect(lambda s: states.append(s))
    proc.start(config.server_exe, preset_name, config.server_dir)
    assert proc.state == ServerState.STARTING

    def reached_running() -> None:
        assert ServerState.RUNNING in states, (
            f"States so far: {states}\nLast 15 lines:\n" + "\n".join(lines[-15:])
        )

    qtbot.waitUntil(reached_running, timeout=_READY_TIMEOUT)
    return proc, lines, states


def _stop_and_wait(qtbot: QtBot, proc: ServerProcess) -> None:
    proc.stop(timeout_s=10)

    def stopped() -> None:
        assert proc.state in (ServerState.STOPPED, ServerState.CRASHED)

    qtbot.waitUntil(stopped, timeout=12_000)


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_baseline_launch_and_stop(qtbot: QtBot) -> None:
    """Baseline: copy of SERVER_01 boots, reaches RUNNING, stops cleanly."""
    name = "ITEST_BASELINE"
    _make_preset(name)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
        assert proc.state in (ServerState.STOPPED, ServerState.CRASHED)
        assert any("Starting update loop" in ln for ln in lines), "Ready line not found"
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# Session configurations
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_qualify_only(qtbot: QtBot) -> None:
    """Only qualifying session enabled — server must still boot."""
    def mod(cfg: PresetConfig) -> None:
        cfg.session_save(*_sess("PRACTICE", False, NAME="Practice", TIME="30",
                                IS_OPEN="1", WAIT_TIME="0"))
        cfg.session_save(*_sess("QUALIFY", True, NAME="Qualifying", TIME="30",
                                IS_OPEN="1", WAIT_TIME="0"))
        cfg.session_save(*_sess("RACE", False, NAME="Race", LAPS="5",
                                TIME="0", IS_OPEN="2", WAIT_TIME="60"))

    name = "ITEST_QUALIFY_ONLY"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        assert any("Qualification" in ln or "Qualify" in ln for ln in lines)
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_practice_only(qtbot: QtBot) -> None:
    """Only practice session enabled."""
    def mod(cfg: PresetConfig) -> None:
        cfg.session_save(*_sess("PRACTICE", True, NAME="Practice", TIME="60",
                                IS_OPEN="1", WAIT_TIME="0"))
        cfg.session_save(*_sess("QUALIFY", False, NAME="Qualifying", TIME="20",
                                IS_OPEN="1", WAIT_TIME="0"))
        cfg.session_save(*_sess("RACE", False, NAME="Race", LAPS="5",
                                TIME="0", IS_OPEN="2", WAIT_TIME="60"))

    name = "ITEST_PRACTICE_ONLY"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        assert any("Practice" in ln for ln in lines)
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_race_only_laps(qtbot: QtBot) -> None:
    """Race only, lap-based."""
    def mod(cfg: PresetConfig) -> None:
        cfg.session_save(*_sess("PRACTICE", False, NAME="Practice", TIME="0",
                                IS_OPEN="1", WAIT_TIME="0"))
        cfg.session_save(*_sess("QUALIFY", False, NAME="Qualifying", TIME="0",
                                IS_OPEN="1", WAIT_TIME="0"))
        cfg.session_save(*_sess("RACE", True, NAME="Race", LAPS="3",
                                TIME="0", IS_OPEN="2", WAIT_TIME="30"))

    name = "ITEST_RACE_ONLY"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        assert any("Race" in ln for ln in lines)
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_all_sessions_enabled(qtbot: QtBot) -> None:
    """All three sessions enabled — practice → qualify → race."""
    def mod(cfg: PresetConfig) -> None:
        cfg.session_save(*_sess("PRACTICE", True, NAME="Practice", TIME="10",
                                IS_OPEN="1", WAIT_TIME="0"))
        cfg.session_save(*_sess("QUALIFY", True, NAME="Qualifying", TIME="10",
                                IS_OPEN="1", WAIT_TIME="0"))
        cfg.session_save(*_sess("RACE", True, NAME="Race", LAPS="2",
                                TIME="0", IS_OPEN="2", WAIT_TIME="10"))

    name = "ITEST_ALL_SESSIONS"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# Assists
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_no_assists(qtbot: QtBot) -> None:
    """All assists disabled."""
    def mod(cfg: PresetConfig) -> None:
        cfg.abs_allowed = 0
        cfg.tc_allowed = 0
        cfg.stability_allowed = False
        cfg.autoclutch_allowed = False
        cfg.tyre_blankets_allowed = False

    name = "ITEST_NO_ASSISTS"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_all_assists(qtbot: QtBot) -> None:
    """All assists enabled (any setting)."""
    def mod(cfg: PresetConfig) -> None:
        cfg.abs_allowed = 2
        cfg.tc_allowed = 2
        cfg.stability_allowed = True
        cfg.autoclutch_allowed = True
        cfg.tyre_blankets_allowed = True

    name = "ITEST_ALL_ASSISTS"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# Damage / fuel / tyre wear
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_no_damage_no_fuel_wear(qtbot: QtBot) -> None:
    """Zero damage, zero fuel consumption, zero tyre wear."""
    def mod(cfg: PresetConfig) -> None:
        cfg.damage_multiplier = 0
        cfg.fuel_rate = 0
        cfg.tyre_wear_rate = 0

    name = "ITEST_NO_DMG_FUEL"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_full_damage_fuel_wear(qtbot: QtBot) -> None:
    """100% damage, fuel, tyre wear."""
    def mod(cfg: PresetConfig) -> None:
        cfg.damage_multiplier = 100
        cfg.fuel_rate = 100
        cfg.tyre_wear_rate = 100

    name = "ITEST_FULL_SIM"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# Dynamic track
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_dynamic_track_enabled(qtbot: QtBot) -> None:
    """Dynamic track grip enabled."""
    def mod(cfg: PresetConfig) -> None:
        cfg.dyn_track_save(True, {
            "SESSION_START": "80", "RANDOMNESS": "5",
            "SESSION_TRANSFER": "80", "LAP_GAIN": "10",
        })

    name = "ITEST_DYN_TRACK"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_dynamic_track_disabled(qtbot: QtBot) -> None:
    """Dynamic track grip disabled (stored as __CM_DYNAMIC_TRACK_OFF)."""
    def mod(cfg: PresetConfig) -> None:
        cfg.dyn_track_save(False, {
            "SESSION_START": "95", "RANDOMNESS": "2",
            "SESSION_TRANSFER": "90", "LAP_GAIN": "10",
        })

    name = "ITEST_STATIC_TRACK"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

def _wx(graphics: str, amb: str, road: str, **kw: str) -> dict[str, str]:
    """Build a weather slot dict."""
    return {
        "GRAPHICS": graphics, "__CM_GRAPHICS": graphics,
        "BASE_TEMPERATURE_AMBIENT": amb, "BASE_TEMPERATURE_ROAD": road,
        "VARIATION_AMBIENT": kw.get("var_amb", "1"),
        "VARIATION_ROAD": kw.get("var_road", "1"),
        "WIND_BASE_SPEED_MIN": kw.get("wmin", "0"),
        "WIND_BASE_SPEED_MAX": kw.get("wmax", "0"),
        "WIND_BASE_DIRECTION": kw.get("wdir", "0"),
        "WIND_VARIATION_DIRECTION": kw.get("wvar", "0"),
    }


@pytest.mark.integration
def test_single_weather_slot(qtbot: QtBot) -> None:
    """Single weather slot — clear weather."""
    def mod(cfg: PresetConfig) -> None:
        cfg.weather_save([_wx("3_clear", "20", "5")])

    name = "ITEST_WEATHER_SINGLE"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_multiple_weather_slots(qtbot: QtBot) -> None:
    """Multiple weather slots."""
    def mod(cfg: PresetConfig) -> None:
        cfg.weather_save([
            _wx("3_clear", "20", "5", var_amb="2", wmax="5", wvar="30"),
            _wx("7_heavy_clouds", "15", "-1", wmin="5", wmax="15",
                wdir="90", wvar="45"),
        ])

    name = "ITEST_WEATHER_MULTI"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_custom_http_port(qtbot: QtBot) -> None:
    """Custom HTTP port — server must still start."""
    def mod(cfg: PresetConfig) -> None:
        cfg.http_port = 9090

    name = "ITEST_HTTP_PORT"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        assert any("9090" in ln for ln in lines), "HTTP port not mentioned in log"
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# Server settings
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_pickup_mode_disabled(qtbot: QtBot) -> None:
    """Pickup mode off (booking-style) — server must boot."""
    def mod(cfg: PresetConfig) -> None:
        cfg.pickup_mode = False

    name = "ITEST_BOOKING"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_loop_mode_disabled(qtbot: QtBot) -> None:
    """Loop mode off — sessions don't repeat."""
    def mod(cfg: PresetConfig) -> None:
        cfg.loop_mode = False

    name = "ITEST_NO_LOOP"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_server_name_change(qtbot: QtBot) -> None:
    """Custom server name — must boot."""
    def mod(cfg: PresetConfig) -> None:
        cfg.name = "GUI_TEST_SERVER"

    name = "ITEST_NAME"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_start_rule_teleport(qtbot: QtBot) -> None:
    """Start rule = teleport (1)."""
    def mod(cfg: PresetConfig) -> None:
        cfg.start_rule = 1
        cfg.session_save(*_sess("RACE", True, NAME="Race", LAPS="2",
                                TIME="0", IS_OPEN="2", WAIT_TIME="10"))
        cfg.session_save(*_sess("QUALIFY", False, NAME="Q", TIME="10",
                                IS_OPEN="1", WAIT_TIME="0"))
        cfg.session_save(*_sess("PRACTICE", False, NAME="P", TIME="10",
                                IS_OPEN="1", WAIT_TIME="0"))

    name = "ITEST_START_TELEPORT"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# Entry list
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_fewer_slots_than_max_clients(qtbot: QtBot) -> None:
    """MAX_CLIENTS reduced to match entry list — must boot."""
    def mod(cfg: PresetConfig) -> None:
        cfg.entry_save(cfg.entry_slots()[:4])
        cfg.max_clients = 4

    name = "ITEST_SMALL_GRID"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_ai_slots(qtbot: QtBot) -> None:
    """Some slots marked as AI=auto."""
    def mod(cfg: PresetConfig) -> None:
        slots = cfg.entry_slots()
        for s in slots[:6]:
            s["AI"] = "auto"
        cfg.entry_save(slots)

    name = "ITEST_AI_SLOTS"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


# ---------------------------------------------------------------------------
# Round-trip (no server launch needed)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_preset_config_round_trip(tmp_path: Path) -> None:
    """Save config changes then reload — all values survive."""
    dst = tmp_path / "ROUND_TRIP"
    copy_preset(SERVER_01, dst)

    cfg = PresetConfig(dst)
    cfg.name = "RoundTripTest"
    cfg.max_clients = 6
    cfg.abs_allowed = 0
    cfg.tc_allowed = 2
    cfg.fuel_rate = 50
    cfg.damage_multiplier = 25
    cfg.kick_quorum = 70
    cfg.udp_port = 9700
    cfg.tcp_port = 9700
    cfg.http_port = 8090
    cfg.session_save(*_sess("PRACTICE", True, NAME="P", TIME="15",
                            IS_OPEN="1", WAIT_TIME="0"))
    cfg.session_save(*_sess("QUALIFY", True, NAME="Q", TIME="10",
                            IS_OPEN="1", WAIT_TIME="0"))
    cfg.session_save(*_sess("RACE", True, NAME="R", LAPS="3",
                            TIME="0", IS_OPEN="2", WAIT_TIME="20"))
    cfg.weather_save([_wx("7_heavy_clouds", "12", "-2",
                          var_amb="1", wmin="5", wmax="20",
                          wdir="180", wvar="60")])
    cfg.save()

    cfg2 = PresetConfig(dst)
    assert cfg2.name == "RoundTripTest"
    assert cfg2.max_clients == 6
    assert cfg2.abs_allowed == 0
    assert cfg2.tc_allowed == 2
    assert cfg2.fuel_rate == 50
    assert cfg2.damage_multiplier == 25
    assert cfg2.kick_quorum == 70
    assert cfg2.udp_port == 9700
    assert cfg2.http_port == 8090
    assert cfg2.session_enabled("PRACTICE")
    assert cfg2.session_enabled("QUALIFY")
    assert cfg2.session_enabled("RACE")
    assert cfg2.session_get("RACE", "LAPS") == "3"
    assert cfg2.weather_count() == 1
    wx = cfg2.weather_items(0)
    assert wx["__CM_GRAPHICS"] == "7_heavy_clouds"
    assert wx["BASE_TEMPERATURE_AMBIENT"] == "12"
    assert wx["WIND_BASE_SPEED_MAX"] == "20"


# ---------------------------------------------------------------------------
# extra_cfg plugin configurations
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_extra_cfg_no_plugins(qtbot: QtBot) -> None:
    """Server boots with minimal extra_cfg (no plugins)."""
    from ac_server_gui.core.extra_cfg_generator import ExtraCfgData, generate_extra_cfg

    def mod(cfg: PresetConfig) -> None:
        text = generate_extra_cfg(ExtraCfgData(
            enable_real_time=False,
            enable_weather_fx=False,
        ))
        cfg.extra_cfg_save(text)

    name = "ITEST_NO_PLUGINS"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_extra_cfg_race_challenge_plugin(qtbot: QtBot) -> None:
    """Server boots with RaceChallengePlugin (no config needed)."""
    from ac_server_gui.core.extra_cfg_generator import (
        ExtraCfgData,
        PluginConfig,
        generate_extra_cfg,
    )

    def mod(cfg: PresetConfig) -> None:
        text = generate_extra_cfg(ExtraCfgData(
            enable_real_time=False,
            enable_weather_fx=False,
            plugins=[PluginConfig(name="RaceChallengePlugin", enabled=True)],
        ))
        cfg.extra_cfg_save(text)

    name = "ITEST_RACE_CHALLENGE"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_extra_cfg_random_weather_plugin(qtbot: QtBot) -> None:
    """Server boots with RandomWeatherPlugin configured."""
    from ac_server_gui.core.extra_cfg_generator import (
        ExtraCfgData,
        PluginConfig,
        generate_extra_cfg,
    )

    def mod(cfg: PresetConfig) -> None:
        text = generate_extra_cfg(ExtraCfgData(
            enable_real_time=False,
            enable_weather_fx=True,
            plugins=[PluginConfig(
                name="RandomWeatherPlugin",
                enabled=True,
                fields={
                    "MinWeatherDurationMinutes": "5",
                    "MaxWeatherDurationMinutes": "20",
                    "MinTransitionDurationSeconds": "30",
                    "MaxTransitionDurationSeconds": "90",
                },
            )],
        ))
        cfg.extra_cfg_save(text)

    name = "ITEST_RANDOM_WEATHER"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        assert any("RandomWeatherPlugin" in ln for ln in lines)
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_extra_cfg_live_weather_plugin(qtbot: QtBot) -> None:
    """Server boots with LiveWeatherPlugin (uses existing API key from SERVER_01)."""
    from ac_server_gui.core.extra_cfg_generator import (
        ExtraCfgData,
        PluginConfig,
        generate_extra_cfg,
    )
    from ac_server_gui.core.extra_cfg_generator import (
        parse_extra_cfg as _parse,
    )
    from ac_server_gui.core.preset_config import PresetConfig as _PC

    # Read the existing API key from SERVER_01
    orig = _PC(SERVER_01)
    orig_text = orig.extra_cfg_text()
    orig_data = _parse(orig_text) if orig_text else None
    api_key = ""
    if orig_data:
        for p in orig_data.plugins:
            if p.name == "LiveWeatherPlugin" and p.enabled:
                api_key = p.fields.get("OpenWeatherMapApiKey", "")
                break

    def mod(cfg: PresetConfig) -> None:
        text = generate_extra_cfg(ExtraCfgData(
            enable_real_time=False,
            enable_weather_fx=True,
            plugins=[PluginConfig(
                name="LiveWeatherPlugin",
                enabled=True,
                fields={"OpenWeatherMapApiKey": api_key, "UpdateIntervalMinutes": "10"},
            )],
        ))
        cfg.extra_cfg_save(text)

    name = "ITEST_LIVE_WEATHER"
    _make_preset(name, mod)
    try:
        proc, lines, states = _launch_and_wait(qtbot, name)
        assert ServerState.RUNNING in states
        assert any("LiveWeatherPlugin" in ln for ln in lines)
        _stop_and_wait(qtbot, proc)
    finally:
        _cleanup(name)


@pytest.mark.integration
def test_extra_cfg_roundtrip(tmp_path: Path) -> None:
    """Generate extra_cfg → parse it back → values match."""
    from ac_server_gui.core.extra_cfg_generator import (
        ExtraCfgData,
        PluginConfig,
        generate_extra_cfg,
        parse_extra_cfg,
    )

    data = ExtraCfgData(
        enable_real_time=True,
        enable_weather_fx=False,
        minimum_csp_version="1937",
        server_description="Test server",
        plugins=[
            PluginConfig(
                name="RandomWeatherPlugin",
                enabled=True,
                fields={
                    "MinWeatherDurationMinutes": "8",
                    "MaxWeatherDurationMinutes": "25",
                    "MinTransitionDurationSeconds": "45",
                    "MaxTransitionDurationSeconds": "150",
                },
            ),
            PluginConfig(name="RaceChallengePlugin", enabled=True),
            PluginConfig(name="LiveWeatherPlugin", enabled=False),
        ],
    )
    text = generate_extra_cfg(data)
    recovered = parse_extra_cfg(text)

    assert recovered.enable_real_time is True
    assert recovered.enable_weather_fx is False
    assert recovered.minimum_csp_version == "1937"
    assert recovered.server_description == "Test server"
    enabled = {p.name: p for p in recovered.plugins if p.enabled}
    assert "RandomWeatherPlugin" in enabled
    assert "RaceChallengePlugin" in enabled
    assert "LiveWeatherPlugin" not in enabled
    rw = enabled["RandomWeatherPlugin"]
    assert rw.fields["MinWeatherDurationMinutes"] == "8"
    assert rw.fields["MaxWeatherDurationMinutes"] == "25"
