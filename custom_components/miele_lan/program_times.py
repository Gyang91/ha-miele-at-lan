"""Program start and end as points in time, derived from `/State`.

No Home Assistant imports, so it can be unit-tested directly (same pattern
as polling.py). The appliance only reports durations in whole minutes:
`StartTime` (delay until a delayed start), `ElapsedTime` and
`RemainingTime`. Turning them into clock times needs "now", which the
caller passes in.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from .const import is_idle_state, parse_minutes_field

STATUS_PROGRAMMED = 3
STATUS_WAITING_TO_START = 4
STATUS_PROGRAM_ENDED = 7

# The reported minutes are whole minutes, so a value computed one poll later
# can differ by up to a minute without anything having changed. Moves below
# this are ignored, so the sensor does not write a new state every minute.
STABLE_WITHIN = dt.timedelta(seconds=90)


def _to_minute(value: dt.datetime) -> dt.datetime:
    return value.replace(second=0, microsecond=0)


def program_timestamps(
    state: dict[str, Any], now: dt.datetime
) -> tuple[dt.datetime | None, dt.datetime | None]:
    """Return (start, end) of the current program, or None where unknown.

    - Idle (off, on without a program, failure, ...): both unknown.
    - Programmed but not started: both unknown, the user has not chosen when.
    - Delayed start: start = now + StartTime, end = start + RemainingTime.
    - Running, paused or interrupted: start = now - ElapsedTime,
      end = now + RemainingTime. A pause moves the end later, as it should.
    - Program ended: unknown here; the entity keeps the end it last showed.
    """
    status = state.get("Status")
    if is_idle_state(state) or status in (STATUS_PROGRAMMED, STATUS_PROGRAM_ENDED):
        return None, None
    start_in = parse_minutes_field(state.get("StartTime"))
    elapsed = parse_minutes_field(state.get("ElapsedTime"))
    remaining = parse_minutes_field(state.get("RemainingTime"))

    if status == STATUS_WAITING_TO_START:
        if start_in is None:
            return None, None
        start = now + dt.timedelta(minutes=start_in)
        end = start + dt.timedelta(minutes=remaining) if remaining else None
        return _to_minute(start), _to_minute(end) if end else None

    start = now - dt.timedelta(minutes=elapsed) if elapsed is not None else None
    end = now + dt.timedelta(minutes=remaining) if remaining else None
    return (
        _to_minute(start) if start else None,
        _to_minute(end) if end else None,
    )


def stabilise(
    previous: dt.datetime | None, current: dt.datetime | None
) -> dt.datetime | None:
    """Keep `previous` while `current` only differs by rounding."""
    if previous is not None and current is not None and abs(current - previous) < STABLE_WITHIN:
        return previous
    return current


__all__ = ["STABLE_WITHIN", "program_timestamps", "stabilise"]
