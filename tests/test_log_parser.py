import pytest

from ac_server_gui.core.log_parser import EventType, LogLevel, classify_line

# File log format (with full timestamp)
INFO_READY = (
    "2026-04-24 21:09:29.938 +02:00 [INF] Starting update loop with an update rate of 18hz"
)
INFO_START = "2026-04-24 21:09:27.418 +02:00 [INF] Starting server"
INFO_TCP = "2026-04-24 21:09:29.928 +02:00 [INF] Starting TCP server on port 9600"
WRN_LINE = "2026-04-24 21:09:27.375 +02:00 [WRN] Do not use WeatherFX start times"
DBG_LINE = "2026-04-24 21:09:26.911 +02:00 [DBG] Loading server_cfg.ini from C:\\foo"
ERR_LINE = (
    '2026-04-24 21:09:29.502 +02:00 [ERR] Connection id "0HNL26K1AESJ9": unhandled'
)
JOIN_LINE = (
    "2026-04-24 21:09:45.960 +02:00 [INF] wygazowanamusztarda "
    "(76561198159238241 - 100.120.25.61:52404) is attempting to connect"
)
LEAVE_LINE = "2026-04-24 21:09:50.000 +02:00 [INF] Player ABC disconnected"

# Stdout format (short timestamp inside bracket)
STDOUT_READY = "[09:27:41 INF] Starting update loop with an update rate of 18hz"
STDOUT_INFO = "[09:27:40 INF] Starting server"
STDOUT_WRN = "[09:27:40 WRN] Do not use WeatherFX start times"
STDOUT_DBG = "[09:27:40 DBG] Loading server_cfg.ini"
STDOUT_ERR = "[09:27:41 ERR] Unhandled exception thrown"
STDOUT_JOIN = "[09:27:45 INF] PlayerX (123 - 1.2.3.4:5000) is attempting to connect"
STDOUT_LEAVE = "[09:27:50 INF] PlayerX disconnected"


def test_ready_line():
    ev = classify_line(INFO_READY)
    assert ev.level == LogLevel.INFO
    assert ev.event_type == EventType.READY


def test_info_line():
    ev = classify_line(INFO_START)
    assert ev.level == LogLevel.INFO
    assert ev.event_type == EventType.INFO


def test_info_tcp():
    ev = classify_line(INFO_TCP)
    assert ev.level == LogLevel.INFO
    assert ev.event_type == EventType.INFO


def test_warning_line():
    ev = classify_line(WRN_LINE)
    assert ev.level == LogLevel.WARNING
    assert ev.event_type == EventType.INFO


def test_debug_line():
    ev = classify_line(DBG_LINE)
    assert ev.level == LogLevel.DEBUG
    assert ev.event_type == EventType.INFO


def test_error_line():
    ev = classify_line(ERR_LINE)
    assert ev.level == LogLevel.ERROR
    assert ev.event_type == EventType.ERROR


def test_player_join():
    ev = classify_line(JOIN_LINE)
    assert ev.level == LogLevel.INFO
    assert ev.event_type == EventType.PLAYER_JOIN


def test_player_leave():
    ev = classify_line(LEAVE_LINE)
    assert ev.level == LogLevel.INFO
    assert ev.event_type == EventType.PLAYER_LEAVE


def test_unknown_line():
    ev = classify_line("some random text without level marker")
    assert ev.level == LogLevel.UNKNOWN
    assert ev.event_type == EventType.UNKNOWN


def test_empty_line():
    ev = classify_line("")
    assert ev.level == LogLevel.UNKNOWN
    assert ev.event_type == EventType.UNKNOWN


def test_whitespace_only():
    ev = classify_line("   \t  ")
    assert ev.level == LogLevel.UNKNOWN
    assert ev.event_type == EventType.UNKNOWN


# Stdout format tests
@pytest.mark.parametrize("line,expected_level,expected_type", [
    (STDOUT_READY, LogLevel.INFO, EventType.READY),
    (STDOUT_INFO, LogLevel.INFO, EventType.INFO),
    (STDOUT_WRN, LogLevel.WARNING, EventType.INFO),
    (STDOUT_DBG, LogLevel.DEBUG, EventType.INFO),
    (STDOUT_ERR, LogLevel.ERROR, EventType.ERROR),
    (STDOUT_JOIN, LogLevel.INFO, EventType.PLAYER_JOIN),
    (STDOUT_LEAVE, LogLevel.INFO, EventType.PLAYER_LEAVE),
])
def test_stdout_format(line: str, expected_level: LogLevel, expected_type: EventType):
    ev = classify_line(line)
    assert ev.level == expected_level
    assert ev.event_type == expected_type
