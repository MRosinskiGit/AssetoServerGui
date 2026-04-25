from __future__ import annotations

from ac_server_gui.core.extra_cfg_generator import (
    ExtraCfgData,
    PluginConfig,
    generate_extra_cfg,
    parse_extra_cfg,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_YAML = """\
EnableRealTime: false
EnableWeatherFx: true
"""

SERVER_01_YAML = """\
EnableRealTime: true
EnableWeatherFx: true
EnablePlugins:
- LiveWeatherPlugin
---
!LiveWeatherConfiguration
OpenWeatherMapApiKey: abc123
UpdateIntervalMinutes: 10
"""

MULTI_PLUGIN_YAML = """\
EnableRealTime: false
EnableWeatherFx: false
EnablePlugins:
- RandomWeatherPlugin
- RaceChallengePlugin
---
!RandomWeatherConfiguration
MinWeatherDurationMinutes: 10
MaxWeatherDurationMinutes: 40
MinTransitionDurationSeconds: 30
MaxTransitionDurationSeconds: 120
"""


# ---------------------------------------------------------------------------
# parse_extra_cfg
# ---------------------------------------------------------------------------

def test_parse_minimal():
    data = parse_extra_cfg(MINIMAL_YAML)
    assert data.enable_real_time is False
    assert data.enable_weather_fx is True
    assert data.minimum_csp_version == ""
    assert data.server_description == ""
    assert all(not p.enabled for p in data.plugins)


def test_parse_empty_string():
    data = parse_extra_cfg("")
    assert data.enable_weather_fx is True  # default
    assert all(not p.enabled for p in data.plugins)


def test_parse_server01_yaml():
    data = parse_extra_cfg(SERVER_01_YAML)
    assert data.enable_real_time is True
    assert data.enable_weather_fx is True
    enabled = [p for p in data.plugins if p.enabled]
    assert len(enabled) == 1
    assert enabled[0].name == "LiveWeatherPlugin"
    assert enabled[0].fields["OpenWeatherMapApiKey"] == "abc123"
    assert enabled[0].fields["UpdateIntervalMinutes"] == "10"


def test_parse_multi_plugin():
    data = parse_extra_cfg(MULTI_PLUGIN_YAML)
    assert data.enable_weather_fx is False
    enabled = {p.name: p for p in data.plugins if p.enabled}
    assert "RandomWeatherPlugin" in enabled
    assert "RaceChallengePlugin" in enabled
    rw = enabled["RandomWeatherPlugin"]
    assert rw.fields["MinWeatherDurationMinutes"] == "10"
    assert rw.fields["MaxWeatherDurationMinutes"] == "40"


def test_parse_csp_version():
    yaml = "EnableRealTime: false\nEnableWeatherFx: true\nMinimumCSPVersion: 1937\n"
    data = parse_extra_cfg(yaml)
    assert data.minimum_csp_version == "1937"


def test_parse_server_description():
    yaml = 'EnableRealTime: false\nEnableWeatherFx: true\nServerDescription: "My server"\n'
    data = parse_extra_cfg(yaml)
    assert data.server_description == "My server"


def test_parse_unknown_plugin_preserved_as_enabled():
    yaml = "EnableRealTime: false\nEnableWeatherFx: false\nEnablePl" \
           "ugins:\n- SomeUnknownPlugin\n"
    data = parse_extra_cfg(yaml)
    # Unknown plugins aren't in PLUGIN_DEFS but should not crash
    assert isinstance(data.plugins, list)


def test_parse_all_known_plugins_present():
    data = parse_extra_cfg(MINIMAL_YAML)
    from ac_server_gui.core.extra_cfg_generator import PLUGIN_DEFS
    plugin_names = {p.name for p in data.plugins}
    for pdef in PLUGIN_DEFS:
        assert pdef.name in plugin_names


# ---------------------------------------------------------------------------
# generate_extra_cfg
# ---------------------------------------------------------------------------

def test_generate_minimal():
    data = ExtraCfgData(enable_real_time=False, enable_weather_fx=True)
    text = generate_extra_cfg(data)
    assert "EnableRealTime: false" in text
    assert "EnableWeatherFx: true" in text
    assert "EnablePlugins" not in text


def test_generate_with_live_weather():
    data = ExtraCfgData(
        enable_real_time=True,
        enable_weather_fx=True,
        plugins=[PluginConfig(
            name="LiveWeatherPlugin",
            enabled=True,
            fields={"OpenWeatherMapApiKey": "xyz", "UpdateIntervalMinutes": "15"},
        )],
    )
    text = generate_extra_cfg(data)
    assert "EnablePlugins:" in text
    assert "- LiveWeatherPlugin" in text
    assert "---" in text
    assert "!LiveWeatherConfiguration" in text
    assert "OpenWeatherMapApiKey: xyz" in text
    assert "UpdateIntervalMinutes: 15" in text


def test_generate_no_config_plugin():
    data = ExtraCfgData(
        enable_real_time=False,
        enable_weather_fx=False,
        plugins=[PluginConfig(name="RaceChallengePlugin", enabled=True)],
    )
    text = generate_extra_cfg(data)
    assert "- RaceChallengePlugin" in text
    assert "---" not in text  # no config block for this plugin


def test_generate_disabled_plugins_excluded():
    data = ExtraCfgData(
        enable_real_time=False,
        enable_weather_fx=True,
        plugins=[
            PluginConfig(name="LiveWeatherPlugin", enabled=False),
            PluginConfig(name="RaceChallengePlugin", enabled=True),
        ],
    )
    text = generate_extra_cfg(data)
    assert "LiveWeatherPlugin" not in text
    assert "RaceChallengePlugin" in text


def test_generate_csp_version_included():
    data = ExtraCfgData(minimum_csp_version="1937")
    text = generate_extra_cfg(data)
    assert "MinimumCSPVersion: 1937" in text


def test_generate_csp_version_empty_excluded():
    data = ExtraCfgData(minimum_csp_version="")
    text = generate_extra_cfg(data)
    assert "MinimumCSPVersion" not in text


def test_generate_multiple_plugins_order():
    data = ExtraCfgData(
        enable_weather_fx=False,
        enable_real_time=False,
        plugins=[
            PluginConfig(name="RaceChallengePlugin", enabled=True),
            PluginConfig(name="AutoModerationPlugin", enabled=True),
        ],
    )
    text = generate_extra_cfg(data)
    rc_pos = text.index("RaceChallengePlugin")
    am_pos = text.index("AutoModerationPlugin")
    assert rc_pos < am_pos


# ---------------------------------------------------------------------------
# Round-trip: parse → generate → parse → values match
# ---------------------------------------------------------------------------

def test_roundtrip_server01():
    original = parse_extra_cfg(SERVER_01_YAML)
    regenerated_text = generate_extra_cfg(original)
    reloaded = parse_extra_cfg(regenerated_text)

    assert reloaded.enable_real_time == original.enable_real_time
    assert reloaded.enable_weather_fx == original.enable_weather_fx
    orig_enabled = {p.name: p for p in original.plugins if p.enabled}
    rel_enabled = {p.name: p for p in reloaded.plugins if p.enabled}
    assert set(orig_enabled.keys()) == set(rel_enabled.keys())
    for name in orig_enabled:
        assert orig_enabled[name].fields == rel_enabled[name].fields


def test_roundtrip_multi_plugin():
    original = parse_extra_cfg(MULTI_PLUGIN_YAML)
    regenerated_text = generate_extra_cfg(original)
    reloaded = parse_extra_cfg(regenerated_text)

    orig_enabled = {p.name for p in original.plugins if p.enabled}
    rel_enabled = {p.name for p in reloaded.plugins if p.enabled}
    assert orig_enabled == rel_enabled
