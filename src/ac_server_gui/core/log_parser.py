from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

# Two log formats:
#   file:   2026-04-24 21:09:26.881 +02:00 [INF] message
#   stdout: [09:27:40 INF] message
_LVL_BRACKET = r"\[(?:\d{2}:\d{2}:\d{2} )?(INF|DBG|WRN|ERR)\]"
_LEVEL_RE = re.compile(_LVL_BRACKET + r"\s*(.*)$")
_PLAYER_JOIN_RE = re.compile(r"\[(?:\d{2}:\d{2}:\d{2} )?INF\].*is attempting to connect")
_PLAYER_LEAVE_RE = re.compile(r"\[(?:\d{2}:\d{2}:\d{2} )?INF\].*(disconnected|left the server)")
_READY_RE = re.compile(r"\[(?:\d{2}:\d{2}:\d{2} )?INF\].*Starting update loop")


class LogLevel(Enum):
    DEBUG = "DBG"
    INFO = "INF"
    WARNING = "WRN"
    ERROR = "ERR"
    UNKNOWN = "UNK"


class EventType(Enum):
    READY = "ready"
    ERROR = "error"
    PLAYER_JOIN = "player_join"
    PLAYER_LEAVE = "player_leave"
    INFO = "info"
    UNKNOWN = "unknown"


@dataclass
class LogEvent:
    level: LogLevel
    event_type: EventType
    raw: str
    message: str


def classify_line(line: str) -> LogEvent:
    stripped = line.strip()
    if not stripped:
        return LogEvent(
            level=LogLevel.UNKNOWN,
            event_type=EventType.UNKNOWN,
            raw=line,
            message="",
        )

    level_match = _LEVEL_RE.search(stripped)
    if level_match is None:
        return LogEvent(
            level=LogLevel.UNKNOWN,
            event_type=EventType.UNKNOWN,
            raw=line,
            message=stripped,
        )

    level_str = level_match.group(1)
    message = level_match.group(2)
    level = LogLevel(level_str)

    if _READY_RE.search(stripped):
        event_type = EventType.READY
    elif level == LogLevel.ERROR:
        event_type = EventType.ERROR
    elif _PLAYER_JOIN_RE.search(stripped):
        event_type = EventType.PLAYER_JOIN
    elif _PLAYER_LEAVE_RE.search(stripped):
        event_type = EventType.PLAYER_LEAVE
    elif level in (LogLevel.INFO, LogLevel.DEBUG, LogLevel.WARNING):
        event_type = EventType.INFO
    else:
        event_type = EventType.UNKNOWN

    return LogEvent(level=level, event_type=event_type, raw=line, message=message)
