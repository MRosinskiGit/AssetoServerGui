from __future__ import annotations

import pytest
from PySide6.QtCore import QTime

from ac_server_gui.widgets.tabs.weather_tab import angle_to_time, time_to_angle

# AC formula: SUN_ANGLE = 16 * (time_seconds - 46800) / 3600
# 00:00 → -208,  08:00 → -80,  12:00 → -16,  13:00 → 0,  18:00 → 80,  23:59 → 175


# ---------------------------------------------------------------------------
# angle_to_time
# ---------------------------------------------------------------------------

def test_midnight():
    t = angle_to_time(-208)
    assert t.hour() == 0
    assert t.minute() == 0


def test_dawn():
    t = angle_to_time(-80)
    assert t.hour() == 8
    assert t.minute() == 0


def test_noon():
    t = angle_to_time(-16)
    assert t.hour() == 12
    assert t.minute() == 0


def test_midday():
    t = angle_to_time(0)
    assert t.hour() == 13
    assert t.minute() == 0


def test_dusk():
    t = angle_to_time(80)
    assert t.hour() == 18
    assert t.minute() == 0


def test_intermediate_positive():
    # 40 → time_s = 40*225+46800 = 55800 = 15h30m
    t = angle_to_time(40)
    assert t.hour() == 15
    assert t.minute() == 30


def test_intermediate_negative():
    # -40 → time_s = -40*225+46800 = 37800 = 10h30m
    t = angle_to_time(-40)
    assert t.hour() == 10
    assert t.minute() == 30


def test_clamped_below_zero():
    # Extreme negative should not produce invalid time
    t = angle_to_time(-999)
    assert t.isValid()
    assert t == QTime(0, 0)


def test_clamped_above_day():
    # Extreme positive should not exceed 23:59
    t = angle_to_time(999)
    assert t.isValid()
    assert t.hour() <= 23


# ---------------------------------------------------------------------------
# time_to_angle
# ---------------------------------------------------------------------------

def test_time_to_angle_midnight():
    assert time_to_angle(QTime(0, 0)) == -208


def test_time_to_angle_dawn():
    assert time_to_angle(QTime(8, 0)) == -80


def test_time_to_angle_noon():
    assert time_to_angle(QTime(12, 0)) == -16


def test_time_to_angle_midday():
    assert time_to_angle(QTime(13, 0)) == 0


def test_time_to_angle_dusk():
    assert time_to_angle(QTime(18, 0)) == 80


def test_time_to_angle_15_30():
    assert time_to_angle(QTime(15, 30)) == 40


def test_time_to_angle_10_30():
    assert time_to_angle(QTime(10, 30)) == -40


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("angle", [-208, -112, -80, -40, -16, 0, 40, 80, 112, 175])
def test_roundtrip_angle(angle: int) -> None:
    t = angle_to_time(angle)
    recovered = time_to_angle(t)
    assert recovered == angle
