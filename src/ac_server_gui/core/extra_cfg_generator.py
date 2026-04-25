"""Parser and generator for AssettoServer extra_cfg.yml."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class PluginField:
    key: str
    label: str
    default: str
    description: str = ""
    is_int: bool = False


@dataclass
class PluginDef:
    name: str
    config_tag: str  # empty = no config block
    description: str
    fields: list[PluginField] = field(default_factory=list)


PLUGIN_DEFS: list[PluginDef] = [
    PluginDef(
        name="LiveWeatherPlugin",
        config_tag="LiveWeatherConfiguration",
        description="Fetches real-time weather from OpenWeatherMap API.",
        fields=[
            PluginField("OpenWeatherMapApiKey", "API key", "",
                        "Free key from openweathermap.org"),
            PluginField("UpdateIntervalMinutes", "Update interval (min)", "10",
                        "How often to poll for new weather", is_int=True),
        ],
    ),
    PluginDef(
        name="RandomWeatherPlugin",
        config_tag="RandomWeatherConfiguration",
        description="Randomises weather with smooth transitions during the session.",
        fields=[
            PluginField("MinWeatherDurationMinutes", "Min duration (min)", "5",
                        "Minimum minutes before next weather change", is_int=True),
            PluginField("MaxWeatherDurationMinutes", "Max duration (min)", "30",
                        "Maximum minutes before next weather change", is_int=True),
            PluginField("MinTransitionDurationSeconds", "Min transition (s)", "60",
                        "Minimum seconds for transition between weathers", is_int=True),
            PluginField("MaxTransitionDurationSeconds", "Max transition (s)", "180",
                        "Maximum seconds for transition between weathers", is_int=True),
        ],
    ),
    PluginDef(
        name="AutoModerationPlugin",
        config_tag="",
        description=(
            "Automatically kicks players who use disallowed assists, "
            "exceed contact limits, or have excessive fuel/tyre usage."
        ),
    ),
    PluginDef(
        name="DiscordAuditPlugin",
        config_tag="DiscordAuditConfiguration",
        description="Sends chat messages, kicks, and bans to a Discord channel.",
        fields=[
            PluginField("WebhookUrl", "Webhook URL", "",
                        "Discord channel webhook URL"),
        ],
    ),
    PluginDef(
        name="VotingWeatherPlugin",
        config_tag="VotingWeatherConfiguration",
        description="Lets players vote on the next weather type.",
        fields=[
            PluginField("VotingIntervalMinutes", "Voting interval (min)", "30",
                        "Minutes between voting rounds", is_int=True),
            PluginField("VotingDurationSeconds", "Voting duration (s)", "60",
                        "Seconds players have to vote", is_int=True),
            PluginField("NumChoices", "Number of choices", "3",
                        "How many weather options to present", is_int=True),
        ],
    ),
    PluginDef(
        name="TimeDilationPlugin",
        config_tag="TimeDilationConfiguration",
        description="Adjusts the time-of-day multiplier based on sun position.",
        fields=[
            PluginField("DurationSeconds", "Day cycle duration (s)", "86400",
                        "Real-world seconds for a full 24-hour game day", is_int=True),
        ],
    ),
    PluginDef(
        name="RaceChallengePlugin",
        config_tag="",
        description="Players can challenge each other to a race by flashing headlights.",
    ),
    PluginDef(
        name="WordFilterPlugin",
        config_tag="WordFilterConfiguration",
        description="Filters chat messages and driver names.",
        fields=[
            PluginField("FilePath", "Word list file", "word_filter.txt",
                        "Path (relative to server dir) to a file with banned words, one per line"),
        ],
    ),
    PluginDef(
        name="GeoIPPlugin",
        config_tag="",
        description="Shows player countries in the server log.",
    ),
]

PLUGIN_BY_NAME: dict[str, PluginDef] = {p.name: p for p in PLUGIN_DEFS}


@dataclass
class PluginConfig:
    name: str
    enabled: bool
    fields: dict[str, str] = field(default_factory=dict)


@dataclass
class ExtraCfgData:
    enable_real_time: bool = False
    enable_weather_fx: bool = True
    minimum_csp_version: str = ""
    server_description: str = ""
    plugins: list[PluginConfig] = field(default_factory=list)


def _split_documents(text: str) -> list[str]:
    """Split a multi-document YAML string on '---' separators."""
    normalized = text.replace("\r\n", "\n")
    return re.split(r"\n---\n|^---\n", normalized, flags=re.MULTILINE)


def parse_extra_cfg(text: str) -> ExtraCfgData:
    """Parse extra_cfg.yml text into ExtraCfgData."""
    result = ExtraCfgData()
    plugin_field_cache: dict[str, dict[str, str]] = {}
    enabled_names: list[str] = []

    docs = _split_documents(text.strip())

    if docs:
        try:
            main: dict[str, Any] = yaml.safe_load(docs[0]) or {}
        except Exception:
            main = {}
        result.enable_real_time = bool(main.get("EnableRealTime", False))
        result.enable_weather_fx = bool(main.get("EnableWeatherFx", True))
        csp = main.get("MinimumCSPVersion")
        result.minimum_csp_version = str(csp) if csp is not None else ""
        result.server_description = str(main.get("ServerDescription", ""))
        raw = main.get("EnablePlugins", [])
        enabled_names = [str(p) for p in (raw if isinstance(raw, list) else [])]

    for doc in docs[1:]:
        lines = doc.strip().splitlines()
        if not lines:
            continue
        first = lines[0].strip()
        tag, rest = ("", doc)
        if first.startswith("!"):
            tag = first[1:]
            rest = "\n".join(lines[1:])
        try:
            cfg: dict[str, Any] = yaml.safe_load(rest) or {}
        except Exception:
            cfg = {}
        for pdef in PLUGIN_DEFS:
            if pdef.config_tag and pdef.config_tag == tag:
                plugin_field_cache[pdef.name] = {k: str(v) for k, v in cfg.items()}
                break

    seen: set[str] = set()
    result.plugins = []
    for pname in enabled_names:
        seen.add(pname)
        result.plugins.append(PluginConfig(
            name=pname,
            enabled=True,
            fields=plugin_field_cache.get(pname, {}),
        ))
    for pdef in PLUGIN_DEFS:
        if pdef.name not in seen:
            result.plugins.append(PluginConfig(name=pdef.name, enabled=False))

    return result


def generate_extra_cfg(data: ExtraCfgData) -> str:
    """Generate extra_cfg.yml text from ExtraCfgData."""
    lines: list[str] = []
    lines.append(f"EnableRealTime: {'true' if data.enable_real_time else 'false'}")
    lines.append(f"EnableWeatherFx: {'true' if data.enable_weather_fx else 'false'}")
    if data.minimum_csp_version.strip():
        lines.append(f"MinimumCSPVersion: {data.minimum_csp_version.strip()}")
    if data.server_description.strip():
        safe = data.server_description.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'ServerDescription: "{safe}"')

    active = [p for p in data.plugins if p.enabled]
    if active:
        lines.append("EnablePlugins:")
        for p in active:
            lines.append(f"- {p.name}")

    for p in active:
        pdef = PLUGIN_BY_NAME.get(p.name)
        if not pdef or not pdef.config_tag or not pdef.fields:
            continue
        lines.append("---")
        lines.append(f"!{pdef.config_tag}")
        for fdef in pdef.fields:
            val = p.fields.get(fdef.key, fdef.default)
            lines.append(f"{fdef.key}: {val}")

    return "\n".join(lines) + "\n"
