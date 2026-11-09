"""Program start / end clock times and the Smart Grid flag."""

import datetime as dt
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from custom_components.miele_lan.const import MieleAppliance  # noqa: E402
from custom_components.miele_lan.program_times import (  # noqa: E402
    program_timestamps,
    stabilise,
)

NOW = dt.datetime(2026, 11, 9, 10, 0, 30, tzinfo=dt.timezone.utc)


def _at(h: int, m: int) -> dt.datetime:
    return dt.datetime(2026, 11, 9, h, m, tzinfo=dt.timezone.utc)


# ------------------------------------------------------------ pure function
def test_running_program_start_and_end() -> None:
    state = {"Status": 5, "ElapsedTime": [1, 34], "RemainingTime": [0, 24], "StartTime": [0, 0]}
    assert program_timestamps(state, NOW) == (_at(8, 26), _at(10, 24))


def test_plain_minutes_format_is_accepted() -> None:
    state = {"Status": 5, "ElapsedTime": 10, "RemainingTime": 50, "StartTime": 0}
    assert program_timestamps(state, NOW) == (_at(9, 50), _at(10, 50))


def test_delayed_start_counts_the_delay() -> None:
    state = {"Status": 4, "StartTime": [2, 0], "RemainingTime": [1, 30], "ElapsedTime": 0}
    assert program_timestamps(state, NOW) == (_at(12, 0), _at(13, 30))


@pytest.mark.parametrize("status", [1, 2, 3, 7, 255])
def test_unknown_when_idle_programmed_or_ended(status: int) -> None:
    state = {"Status": status, "ElapsedTime": [0, 0], "RemainingTime": [0, 5], "StartTime": 0}
    assert program_timestamps(state, NOW) == (None, None)


def test_no_end_without_remaining_time() -> None:
    state = {"Status": 5, "ElapsedTime": [0, 10], "RemainingTime": [0, 0]}
    start, end = program_timestamps(state, NOW)
    assert start == _at(9, 50)
    assert end is None


def test_missing_or_sentinel_fields_give_unknown() -> None:
    state = {"Status": 5, "ElapsedTime": -32768, "RemainingTime": None}
    assert program_timestamps(state, NOW) == (None, None)


def test_rounding_jitter_is_ignored_but_real_changes_pass() -> None:
    prev = _at(10, 24)
    assert stabilise(prev, _at(10, 25)) == prev
    assert stabilise(prev, _at(10, 23)) == prev
    assert stabilise(prev, _at(10, 30)) == _at(10, 30)
    assert stabilise(None, _at(10, 24)) == _at(10, 24)
    assert stabilise(prev, None) is None


# ------------------------------------------------------------------- entity
def _sensor(which: str, state: dict):
    from custom_components.miele_lan import sensor

    (desc,) = [d for d in sensor.PROGRAM_TIME_SENSORS if d.key == which]
    entity = sensor.MieleLanProgramTimeSensor.__new__(sensor.MieleLanProgramTimeSensor)
    entity.entity_description = desc
    entity._last = None
    entity.coordinator = SimpleNamespace(data=SimpleNamespace(state=state))
    return entity


def test_entity_keeps_end_after_program_ended_and_clears_when_idle(monkeypatch) -> None:
    from custom_components.miele_lan import sensor

    monkeypatch.setattr(sensor.dt_util, "utcnow", lambda: NOW)
    state = {"Status": 5, "ElapsedTime": [0, 30], "RemainingTime": [0, 24]}
    entity = _sensor("program_end", state)
    assert entity.native_value == _at(10, 24)

    state.update({"Status": 7, "RemainingTime": [0, 0]})
    assert entity.native_value == _at(10, 24)

    state.update({"Status": 1})
    assert entity.native_value is None


def test_entity_holds_value_through_minute_jitter(monkeypatch) -> None:
    from custom_components.miele_lan import sensor

    clock = {"now": NOW}
    monkeypatch.setattr(sensor.dt_util, "utcnow", lambda: clock["now"])
    state = {"Status": 5, "ElapsedTime": [0, 30], "RemainingTime": [0, 24]}
    entity = _sensor("program_end", state)
    first = entity.native_value
    clock["now"] = NOW + dt.timedelta(seconds=40)  # crosses a minute, same minutes left
    assert entity.native_value == first


def test_cycle_devices_get_both_time_sensors() -> None:
    from custom_components.miele_lan import sensor

    assert {d.key for d in sensor.PROGRAM_TIME_SENSORS} == {"program_start", "program_end"}


# --------------------------------------------------------------- Smart Grid
@pytest.mark.parametrize("remote_enable,expected", [
    ([15, 1, 0], True),
    ([15, 0, 1], False),
    (None, False),
])
def test_smart_grid_reads_remote_enable_middle_element(remote_enable, expected) -> None:
    from custom_components.miele_lan import binary_sensor

    (d,) = [d for d in binary_sensor.BINARY_SENSOR_TYPES if d.description.key == "smart_grid"]
    assert MieleAppliance.WASHING_MACHINE in d.types
    assert MieleAppliance.TUMBLE_DRYER in d.types
    assert d.description.is_on_fn({"RemoteEnable": remote_enable}) is expected
