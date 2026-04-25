from __future__ import annotations

import configparser
from pathlib import Path


class PresetConfig:
    """Thin wrapper around configparser for server_cfg.ini + entry_list.ini."""

    def __init__(self, preset_path: Path) -> None:
        self.path = preset_path
        self._ini = configparser.RawConfigParser()
        self._ini.optionxform = lambda x: x  # type: ignore[method-assign, assignment]
        self._ini.read(preset_path / "server_cfg.ini", encoding="utf-8")
        self._entry = configparser.RawConfigParser()
        self._entry.optionxform = lambda x: x  # type: ignore[method-assign, assignment]
        self._entry.read(preset_path / "entry_list.ini", encoding="utf-8")

    # ------------------------------------------------------------------ low-level helpers
    def get(self, section: str, key: str, fallback: str = "") -> str:
        return self._ini.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str) -> None:
        if not self._ini.has_section(section):
            self._ini.add_section(section)
        self._ini.set(section, key, value)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        try:
            return int(self.get(section, key, str(fallback)))
        except ValueError:
            return fallback

    def set_int(self, section: str, key: str, value: int) -> None:
        self.set(section, key, str(value))

    # ------------------------------------------------------------------ SERVER fields
    @property
    def name(self) -> str:
        return self.get("SERVER", "NAME", "AC Server")

    @name.setter
    def name(self, v: str) -> None:
        self.set("SERVER", "NAME", v)

    @property
    def password(self) -> str:
        return self.get("SERVER", "PASSWORD", "")

    @password.setter
    def password(self, v: str) -> None:
        self.set("SERVER", "PASSWORD", v)

    @property
    def admin_password(self) -> str:
        return self.get("SERVER", "ADMIN_PASSWORD", "")

    @admin_password.setter
    def admin_password(self, v: str) -> None:
        self.set("SERVER", "ADMIN_PASSWORD", v)

    @property
    def max_clients(self) -> int:
        return self.get_int("SERVER", "MAX_CLIENTS", 12)

    @max_clients.setter
    def max_clients(self, v: int) -> None:
        self.set_int("SERVER", "MAX_CLIENTS", v)

    @property
    def cars(self) -> list[str]:
        raw = self.get("SERVER", "CARS", "")
        return [c for c in raw.split(";") if c]

    @cars.setter
    def cars(self, v: list[str]) -> None:
        self.set("SERVER", "CARS", ";".join(v))

    @property
    def track(self) -> str:
        return self.get("SERVER", "TRACK", "")

    @track.setter
    def track(self, v: str) -> None:
        self.set("SERVER", "TRACK", v)

    @property
    def config_track(self) -> str:
        return self.get("SERVER", "CONFIG_TRACK", "")

    @config_track.setter
    def config_track(self, v: str) -> None:
        self.set("SERVER", "CONFIG_TRACK", v)

    @property
    def register_to_lobby(self) -> bool:
        return self.get_int("SERVER", "REGISTER_TO_LOBBY", 0) == 1

    @register_to_lobby.setter
    def register_to_lobby(self, v: bool) -> None:
        self.set_int("SERVER", "REGISTER_TO_LOBBY", int(v))

    @property
    def pickup_mode(self) -> bool:
        return self.get_int("SERVER", "PICKUP_MODE_ENABLED", 1) == 1

    @pickup_mode.setter
    def pickup_mode(self, v: bool) -> None:
        self.set_int("SERVER", "PICKUP_MODE_ENABLED", int(v))

    @property
    def loop_mode(self) -> bool:
        return self.get_int("SERVER", "LOOP_MODE", 1) == 1

    @loop_mode.setter
    def loop_mode(self, v: bool) -> None:
        self.set_int("SERVER", "LOOP_MODE", int(v))

    @property
    def locked_entry_list(self) -> bool:
        return self.get_int("SERVER", "LOCKED_ENTRY_LIST", 0) == 1

    @locked_entry_list.setter
    def locked_entry_list(self, v: bool) -> None:
        self.set_int("SERVER", "LOCKED_ENTRY_LIST", int(v))

    @property
    def sun_angle(self) -> int:
        return self.get_int("SERVER", "SUN_ANGLE", 16)

    @sun_angle.setter
    def sun_angle(self, v: int) -> None:
        self.set_int("SERVER", "SUN_ANGLE", v)

    @property
    def time_of_day_mult(self) -> int:
        return self.get_int("SERVER", "TIME_OF_DAY_MULT", 1)

    @time_of_day_mult.setter
    def time_of_day_mult(self, v: int) -> None:
        self.set_int("SERVER", "TIME_OF_DAY_MULT", v)

    # Assists
    @property
    def abs_allowed(self) -> int:
        return self.get_int("SERVER", "ABS_ALLOWED", 1)

    @abs_allowed.setter
    def abs_allowed(self, v: int) -> None:
        self.set_int("SERVER", "ABS_ALLOWED", v)

    @property
    def tc_allowed(self) -> int:
        return self.get_int("SERVER", "TC_ALLOWED", 1)

    @tc_allowed.setter
    def tc_allowed(self, v: int) -> None:
        self.set_int("SERVER", "TC_ALLOWED", v)

    @property
    def stability_allowed(self) -> bool:
        return self.get_int("SERVER", "STABILITY_ALLOWED", 0) == 1

    @stability_allowed.setter
    def stability_allowed(self, v: bool) -> None:
        self.set_int("SERVER", "STABILITY_ALLOWED", int(v))

    @property
    def autoclutch_allowed(self) -> bool:
        return self.get_int("SERVER", "AUTOCLUTCH_ALLOWED", 1) == 1

    @autoclutch_allowed.setter
    def autoclutch_allowed(self, v: bool) -> None:
        self.set_int("SERVER", "AUTOCLUTCH_ALLOWED", int(v))

    @property
    def tyre_blankets_allowed(self) -> bool:
        return self.get_int("SERVER", "TYRE_BLANKETS_ALLOWED", 1) == 1

    @tyre_blankets_allowed.setter
    def tyre_blankets_allowed(self, v: bool) -> None:
        self.set_int("SERVER", "TYRE_BLANKETS_ALLOWED", int(v))

    @property
    def force_virtual_mirror(self) -> bool:
        return self.get_int("SERVER", "FORCE_VIRTUAL_MIRROR", 0) == 1

    @force_virtual_mirror.setter
    def force_virtual_mirror(self, v: bool) -> None:
        self.set_int("SERVER", "FORCE_VIRTUAL_MIRROR", int(v))

    # Rules
    @property
    def fuel_rate(self) -> int:
        return self.get_int("SERVER", "FUEL_RATE", 100)

    @fuel_rate.setter
    def fuel_rate(self, v: int) -> None:
        self.set_int("SERVER", "FUEL_RATE", v)

    @property
    def damage_multiplier(self) -> int:
        return self.get_int("SERVER", "DAMAGE_MULTIPLIER", 100)

    @damage_multiplier.setter
    def damage_multiplier(self, v: int) -> None:
        self.set_int("SERVER", "DAMAGE_MULTIPLIER", v)

    @property
    def tyre_wear_rate(self) -> int:
        return self.get_int("SERVER", "TYRE_WEAR_RATE", 100)

    @tyre_wear_rate.setter
    def tyre_wear_rate(self, v: int) -> None:
        self.set_int("SERVER", "TYRE_WEAR_RATE", v)

    @property
    def allowed_tyres_out(self) -> int:
        return self.get_int("SERVER", "ALLOWED_TYRES_OUT", 2)

    @allowed_tyres_out.setter
    def allowed_tyres_out(self, v: int) -> None:
        self.set_int("SERVER", "ALLOWED_TYRES_OUT", v)

    @property
    def start_rule(self) -> int:
        return self.get_int("SERVER", "START_RULE", 0)

    @start_rule.setter
    def start_rule(self, v: int) -> None:
        self.set_int("SERVER", "START_RULE", v)

    @property
    def reversed_grid_positions(self) -> int:
        return self.get_int("SERVER", "REVERSED_GRID_RACE_POSITIONS", 0)

    @reversed_grid_positions.setter
    def reversed_grid_positions(self, v: int) -> None:
        self.set_int("SERVER", "REVERSED_GRID_RACE_POSITIONS", v)

    @property
    def race_gas_penalty_disabled(self) -> bool:
        return self.get_int("SERVER", "RACE_GAS_PENALTY_DISABLED", 0) == 1

    @race_gas_penalty_disabled.setter
    def race_gas_penalty_disabled(self, v: bool) -> None:
        self.set_int("SERVER", "RACE_GAS_PENALTY_DISABLED", int(v))

    @property
    def max_contacts_per_km(self) -> int:
        return self.get_int("SERVER", "MAX_CONTACTS_PER_KM", -1)

    @max_contacts_per_km.setter
    def max_contacts_per_km(self, v: int) -> None:
        self.set_int("SERVER", "MAX_CONTACTS_PER_KM", v)

    @property
    def kick_quorum(self) -> int:
        return self.get_int("SERVER", "KICK_QUORUM", 85)

    @kick_quorum.setter
    def kick_quorum(self, v: int) -> None:
        self.set_int("SERVER", "KICK_QUORUM", v)

    @property
    def voting_quorum(self) -> int:
        return self.get_int("SERVER", "VOTING_QUORUM", 80)

    @voting_quorum.setter
    def voting_quorum(self, v: int) -> None:
        self.set_int("SERVER", "VOTING_QUORUM", v)

    @property
    def vote_duration(self) -> int:
        return self.get_int("SERVER", "VOTE_DURATION", 20)

    @vote_duration.setter
    def vote_duration(self, v: int) -> None:
        self.set_int("SERVER", "VOTE_DURATION", v)

    @property
    def blacklist_mode(self) -> int:
        return self.get_int("SERVER", "BLACKLIST_MODE", 1)

    @blacklist_mode.setter
    def blacklist_mode(self, v: int) -> None:
        self.set_int("SERVER", "BLACKLIST_MODE", v)

    @property
    def race_over_time(self) -> int:
        return self.get_int("SERVER", "RACE_OVER_TIME", 60)

    @race_over_time.setter
    def race_over_time(self, v: int) -> None:
        self.set_int("SERVER", "RACE_OVER_TIME", v)

    @property
    def result_screen_time(self) -> int:
        return self.get_int("SERVER", "RESULT_SCREEN_TIME", 60)

    @result_screen_time.setter
    def result_screen_time(self, v: int) -> None:
        self.set_int("SERVER", "RESULT_SCREEN_TIME", v)

    # Network
    @property
    def udp_port(self) -> int:
        return self.get_int("SERVER", "UDP_PORT", 9600)

    @udp_port.setter
    def udp_port(self, v: int) -> None:
        self.set_int("SERVER", "UDP_PORT", v)

    @property
    def tcp_port(self) -> int:
        return self.get_int("SERVER", "TCP_PORT", 9600)

    @tcp_port.setter
    def tcp_port(self, v: int) -> None:
        self.set_int("SERVER", "TCP_PORT", v)

    @property
    def http_port(self) -> int:
        return self.get_int("SERVER", "HTTP_PORT", 8081)

    @http_port.setter
    def http_port(self, v: int) -> None:
        self.set_int("SERVER", "HTTP_PORT", v)

    @property
    def num_threads(self) -> int:
        return self.get_int("SERVER", "NUM_THREADS", 2)

    @num_threads.setter
    def num_threads(self, v: int) -> None:
        self.set_int("SERVER", "NUM_THREADS", v)

    @property
    def client_send_interval_hz(self) -> int:
        return self.get_int("SERVER", "CLIENT_SEND_INTERVAL_HZ", 18)

    @client_send_interval_hz.setter
    def client_send_interval_hz(self, v: int) -> None:
        self.set_int("SERVER", "CLIENT_SEND_INTERVAL_HZ", v)

    @property
    def sleep_time(self) -> int:
        return self.get_int("SERVER", "SLEEP_TIME", 1)

    @sleep_time.setter
    def sleep_time(self, v: int) -> None:
        self.set_int("SERVER", "SLEEP_TIME", v)

    # ------------------------------------------------------------------ Sessions
    def _session_section(self, base: str) -> tuple[str, bool]:
        """Return (section_name, enabled)."""
        if self._ini.has_section(base):
            return (base, True)
        off = f"__CM_{base}_OFF"
        if self._ini.has_section(off):
            return (off, False)
        return (base, False)

    def session_enabled(self, base: str) -> bool:
        _, enabled = self._session_section(base)
        return enabled

    def session_get(self, base: str, key: str, fallback: str = "") -> str:
        section, _ = self._session_section(base)
        return self._ini.get(section, key, fallback=fallback)

    def session_items(self, base: str) -> dict[str, str]:
        section, _ = self._session_section(base)
        if self._ini.has_section(section):
            return dict(self._ini.items(section))
        return {}

    def session_save(self, base: str, enabled: bool, data: dict[str, str]) -> None:
        for s in [base, f"__CM_{base}_OFF"]:
            if self._ini.has_section(s):
                self._ini.remove_section(s)
        target = base if enabled else f"__CM_{base}_OFF"
        self._ini.add_section(target)
        for k, v in data.items():
            self._ini.set(target, k, v)

    # ------------------------------------------------------------------ Weather
    def weather_count(self) -> int:
        i = 0
        while self._ini.has_section(f"WEATHER_{i}"):
            i += 1
        return i

    def weather_items(self, idx: int) -> dict[str, str]:
        section = f"WEATHER_{idx}"
        if self._ini.has_section(section):
            return dict(self._ini.items(section))
        return {}

    def weather_save(self, slots: list[dict[str, str]]) -> None:
        # Remove all existing WEATHER_N
        i = 0
        while self._ini.has_section(f"WEATHER_{i}"):
            self._ini.remove_section(f"WEATHER_{i}")
            i += 1
        for idx, slot in enumerate(slots):
            section = f"WEATHER_{idx}"
            self._ini.add_section(section)
            for k, v in slot.items():
                self._ini.set(section, k, v)

    # ------------------------------------------------------------------ Dynamic Track
    def dyn_track_section(self) -> str:
        for s in ["DYNAMIC_TRACK", "__CM_DYNAMIC_TRACK_OFF"]:
            if self._ini.has_section(s):
                return s
        return "DYNAMIC_TRACK"

    def dyn_track_get(self, key: str, fallback: str = "") -> str:
        return self._ini.get(self.dyn_track_section(), key, fallback=fallback)

    def dyn_track_enabled(self) -> bool:
        return self._ini.has_section("DYNAMIC_TRACK")

    def dyn_track_save(self, enabled: bool, data: dict[str, str]) -> None:
        for s in ["DYNAMIC_TRACK", "__CM_DYNAMIC_TRACK_OFF"]:
            if self._ini.has_section(s):
                self._ini.remove_section(s)
        target = "DYNAMIC_TRACK" if enabled else "__CM_DYNAMIC_TRACK_OFF"
        self._ini.add_section(target)
        for k, v in data.items():
            self._ini.set(target, k, v)

    # ------------------------------------------------------------------ Entry list
    def entry_slots(self) -> list[dict[str, str]]:
        slots = []
        i = 0
        while self._entry.has_section(f"CAR_{i}"):
            slots.append(dict(self._entry.items(f"CAR_{i}")))
            i += 1
        return slots

    def entry_save(self, slots: list[dict[str, str]]) -> None:
        i = 0
        while self._entry.has_section(f"CAR_{i}"):
            self._entry.remove_section(f"CAR_{i}")
            i += 1
        for idx, slot in enumerate(slots):
            section = f"CAR_{idx}"
            self._entry.add_section(section)
            for k, v in slot.items():
                self._entry.set(section, k, v)

    # ------------------------------------------------------------------ extra_cfg.yml
    def extra_cfg_text(self) -> str:
        p = self.path / "extra_cfg.yml"
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
        return ""

    def extra_cfg_save(self, text: str) -> None:
        (self.path / "extra_cfg.yml").write_text(text, encoding="utf-8")

    # ------------------------------------------------------------------ save
    def save(self) -> None:
        with open(self.path / "server_cfg.ini", "w", encoding="utf-8") as f:
            self._ini.write(f, space_around_delimiters=False)
        with open(self.path / "entry_list.ini", "w", encoding="utf-8") as f:
            self._entry.write(f, space_around_delimiters=False)
