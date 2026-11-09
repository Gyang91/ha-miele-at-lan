"""Sleep-vs-unsupported handling for the DOP2 2/1585 (device context) poll.

A sleeping XKM answers HTTP 500 (empty body) to every DOP2 read, and
latching *that* as "unsupported" would permanently hide AutoDos/salt/
rinse-aid entities on an appliance that happened to be in deep standby at
HA startup. This read is a background poll, so it must also never wake
the appliance: `PUT /State {"DeviceAction": 2}` every 10 minutes kept
dryers from reaching standby (drum light switching on at night).

Coordinator is constructed standalone (no HA imports): a minimal stub
client reports scripted statuses, and the real
`_maybe_refresh_device_context` runs against it.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import custom_components.miele_lan.coordinator as coordinator_mod  # noqa: E402
from custom_components.miele_lan.const import MieleAppliance  # noqa: E402
from custom_components.miele_lan.coordinator import (  # noqa: E402
    DEVICE_CONTEXT_MAX_MISS_CYCLES,
)

FIXTURE = Path(__file__).parent / "fixtures" / "g7655_dop2_1585.hex"
LEAF_URL_BODY = (200, bytes.fromhex(FIXTURE.read_text().replace("\n", "")))

IN_USE = 5  # /State.Status while a programme runs: the XKM is awake
ON = 2  # switched on, no programme
OFF = 1


class _StubRaw:
    def __init__(self, statuses: list[int]) -> None:
        self._statuses = list(statuses)
        self.calls = 0

    async def _request_bytes(self, method: str, resource: str, **kwargs: Any):
        self.calls += 1
        status = self._statuses.pop(0)
        if status == 200:
            return LEAF_URL_BODY
        return (status, b"")


class _BoomRaw(_StubRaw):
    async def _request_bytes(self, method: str, resource: str, **kwargs: Any):
        self.calls += 1
        raise TimeoutError()


class _StubClient:
    def __init__(self, statuses: list[int]) -> None:
        self.raw = _StubRaw(statuses)
        self.wake = AsyncMock(return_value={})

    def set_statuses(self, statuses: list[int]) -> None:
        self.raw._statuses = list(statuses)
        self.raw.calls = 0


def _make_coordinator(
    statuses: list[int], device_type: MieleAppliance, status: int | None = None
) -> Any:
    """Build a coordinator-shaped object without running DataUpdateCoordinator.__init__."""
    coord = coordinator_mod.MieleLanCoordinator.__new__(  # type: ignore[misc]
        coordinator_mod.MieleLanCoordinator
    )
    coord.client = _StubClient(statuses)  # type: ignore[assignment]
    coord.fab = "000106908768"
    # device_type is a read-only property derived from ident (self._data).
    coord._data = coordinator_mod.MieleLanData()
    coord._data.ident = {"device_type": int(device_type)}
    if status is not None:
        coord._data.state = {"Status": status}
    coord._device_context_unsupported = False
    coord._device_context_last_fetch = float("-inf")  # fresh runners: monotonic() starts ~0
    coord._device_context_miss_cycles = 0
    coord._device_context_answered = False
    return coord


def _reset_throttle(coord: Any) -> None:
    coord._device_context_last_fetch = float("-inf")  # fresh runners: monotonic() starts ~0


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test may sleep for real, whatever path the code takes."""
    async def _instant(_delay: float) -> None:  # pragma: no cover - trivial
        return None

    monkeypatch.setattr(coordinator_mod.asyncio, "sleep", _instant)


async def _run(coord: Any) -> None:
    t0 = time.monotonic()
    await coord._maybe_refresh_device_context()
    assert time.monotonic() - t0 < 10


def _cycle(coord: Any, statuses: list[int]) -> None:
    """One full-refresh poll cycle with the given scripted answers."""
    coord.client.set_statuses(statuses)
    _reset_throttle(coord)
    asyncio.run(_run(coord))


# --------------------------------------------------------- asleep (idle) path
def test_sleep_500_does_not_latch_unsupported() -> None:
    coord = _make_coordinator([500], MieleAppliance.DISHWASHER)
    coord.client.set_statuses([500])
    asyncio.run(_run(coord))
    assert coord._device_context_unsupported is False


@pytest.mark.parametrize("status", [None, ON, 4, 7])
def test_sleep_500_never_wakes_and_counts_no_miss(status: int | None) -> None:
    """Background read: a 500 without a running programme means asleep."""
    coord = _make_coordinator([500], MieleAppliance.TUMBLE_DRYER, status)
    coord.client.set_statuses([500])
    asyncio.run(_run(coord))
    coord.client.wake.assert_not_awaited()
    assert coord.client.raw.calls == 1
    assert coord._device_context_miss_cycles == 0
    assert coord._device_context_unsupported is False


def test_sleeping_appliance_is_never_latched() -> None:
    """Asleep all night: many 500 cycles, still no wake and no latch."""
    coord = _make_coordinator([500], MieleAppliance.DISHWASHER, ON)
    for _ in range(DEVICE_CONTEXT_MAX_MISS_CYCLES * 3):
        _cycle(coord, [500])
    coord.client.wake.assert_not_awaited()
    assert coord._device_context_miss_cycles == 0
    assert coord._device_context_unsupported is False


def test_sleep_500_keeps_last_value() -> None:
    coord = _make_coordinator([200], MieleAppliance.DISHWASHER, IN_USE)
    coord.client.set_statuses([200])
    asyncio.run(_run(coord))
    assert coord._data.device_context.get("salt_percent") == 77
    coord._data.state = {"Status": ON}
    _cycle(coord, [500])
    assert coord._data.device_context.get("salt_percent") == 77
    coord.client.wake.assert_not_awaited()


def test_fetch_failure_while_idle_counts_no_miss() -> None:
    coord = _make_coordinator([], MieleAppliance.DISHWASHER, ON)
    coord.client.raw = _BoomRaw([])  # type: ignore[assignment]
    asyncio.run(_run(coord))
    assert coord._device_context_miss_cycles == 0
    assert coord._device_context_unsupported is False
    coord.client.wake.assert_not_awaited()


@pytest.mark.parametrize("status", [OFF, 255])
def test_off_or_not_connected_skips_the_read(status: int) -> None:
    """Switched off: no request at all, and the throttle is not advanced."""
    coord = _make_coordinator([200], MieleAppliance.TUMBLE_DRYER, status)
    coord.client.set_statuses([200])
    asyncio.run(_run(coord))
    assert coord.client.raw.calls == 0
    coord.client.wake.assert_not_awaited()
    assert coord._device_context_last_fetch == float("-inf")


def test_read_happens_on_first_poll_after_switch_on() -> None:
    coord = _make_coordinator([200], MieleAppliance.TUMBLE_DRYER, OFF)
    coord.client.set_statuses([200])
    asyncio.run(_run(coord))
    assert coord.client.raw.calls == 0
    coord._data.state = {"Status": IN_USE}
    asyncio.run(_run(coord))  # no throttle reset needed: it was never advanced
    assert coord.client.raw.calls == 1
    assert coord._data.device_context


# ------------------------------------------------------------- 200 / 403 / 404
def test_awake_200_stores_device_context() -> None:
    coord = _make_coordinator([200], MieleAppliance.DISHWASHER, IN_USE)
    coord.client.set_statuses([200])
    asyncio.run(_run(coord))
    assert coord.client.raw.calls == 1
    assert coord._data.device_context.get("salt_percent") == 77
    assert coord._device_context_miss_cycles == 0
    coord.client.wake.assert_not_awaited()


def test_404_latches_unsupported() -> None:
    coord = _make_coordinator([500], MieleAppliance.DISHWASHER)
    coord.client.set_statuses([404])
    asyncio.run(_run(coord))
    assert coord._device_context_unsupported is True


def test_404_latch_clears_cached_device_context() -> None:
    coord = _make_coordinator([200], MieleAppliance.DISHWASHER)
    coord.client.set_statuses([200])
    asyncio.run(_run(coord))
    assert coord._data.device_context
    _cycle(coord, [404])
    assert coord._device_context_unsupported is True
    assert coord._data.device_context == {}


# ----------------------------------------------- awake 500 (issue #16, G7310)
def test_awake_500_counts_one_miss_without_waking() -> None:
    coord = _make_coordinator([500], MieleAppliance.DISHWASHER, IN_USE)
    coord.client.set_statuses([500])
    asyncio.run(_run(coord))
    assert coord._device_context_unsupported is False
    assert coord._device_context_miss_cycles == 1
    assert coord.client.raw.calls == 1
    coord.client.wake.assert_not_awaited()


def test_first_and_second_miss_never_latch() -> None:
    coord = _make_coordinator([500], MieleAppliance.DISHWASHER, IN_USE)
    _cycle(coord, [500])
    assert coord._device_context_unsupported is False
    _cycle(coord, [500])
    assert coord._device_context_unsupported is False


def test_miss_cycles_latch_after_three_without_200() -> None:
    """PR-review bound: 3 consecutive awake cycles without a 200 latch the leaf."""
    coord = _make_coordinator([500], MieleAppliance.DISHWASHER, IN_USE)
    _cycle(coord, [500])
    _cycle(coord, [500])
    assert coord._device_context_unsupported is False
    _cycle(coord, [500])
    assert coord._device_context_unsupported is True
    coord.client.wake.assert_not_awaited()


def test_miss_latch_clears_cached_device_context() -> None:
    """Latch must not leave frozen stale levels behind (review note)."""
    coord = _make_coordinator([200], MieleAppliance.DISHWASHER, IN_USE)
    coord.client.set_statuses([200])
    asyncio.run(_run(coord))
    assert coord._data.device_context.get("salt_percent") == 77
    # Already 2 seeded misses; one more miss cycle latches + clears.
    coord._device_context_miss_cycles = 2
    _cycle(coord, [500])
    assert coord._device_context_unsupported is True
    assert coord._data.device_context == {}


def test_idle_cycles_neither_count_nor_reset_the_miss_streak() -> None:
    coord = _make_coordinator([500], MieleAppliance.DISHWASHER, IN_USE)
    _cycle(coord, [500])
    _cycle(coord, [500])
    coord._data.state = {"Status": ON}
    _cycle(coord, [500])
    assert coord._device_context_miss_cycles == 2
    coord._data.state = {"Status": IN_USE}
    _cycle(coord, [500])
    assert coord._device_context_unsupported is True


def test_200_resets_the_miss_counter() -> None:
    coord = _make_coordinator([500], MieleAppliance.DISHWASHER, IN_USE)
    _cycle(coord, [500])  # miss 1
    _cycle(coord, [500])  # miss 2
    assert coord._device_context_miss_cycles == 2
    # A 200 on one cycle clears the streak entirely…
    _cycle(coord, [200])
    assert coord._device_context_miss_cycles == 0
    assert coord._device_context_unsupported is False
    # …so three further misses (not one) are needed to latch.
    _cycle(coord, [500])
    _cycle(coord, [500])
    assert coord._device_context_unsupported is False
    _cycle(coord, [500])
    assert coord._device_context_unsupported is True


def test_fetch_failure_while_awake_counts_as_a_miss() -> None:
    """A timeout during a programme is a cycle that ended without a 200."""
    coord = _make_coordinator([], MieleAppliance.DISHWASHER, IN_USE)
    coord.client.raw = _BoomRaw([])  # type: ignore[assignment]
    asyncio.run(_run(coord))
    assert coord._device_context_miss_cycles == 1
    assert coord._device_context_unsupported is False


# ------------------------------------------------------------------- families
def test_non_dw_family_never_polls() -> None:
    coord = _make_coordinator([500], MieleAppliance.OVEN)
    coord.client.set_statuses([500, 200])
    asyncio.run(_run(coord))
    assert coord.client.raw.calls == 0


def test_laundry_family_still_polls() -> None:
    """Gate extension must not regress the original TwinDos consumers."""
    coord = _make_coordinator([500], MieleAppliance.WASHING_MACHINE)
    coord.client.set_statuses([200])
    asyncio.run(_run(coord))
    assert coord.client.raw.calls == 1
    assert coord._data.device_context.get("dos_containers") is not None


# --------------------------------------------------------------- user actions
def test_wake_button_still_wakes() -> None:
    """Waking after a user action stays: the wake button calls client.wake()."""
    from custom_components.miele_lan import button

    (wake_def,) = [d for d in button.BUTTONS if d.description.key == "wake"]
    coord = _make_coordinator([], MieleAppliance.TUMBLE_DRYER, OFF)
    asyncio.run(wake_def.description.press_fn(coord))
    coord.client.wake.assert_awaited_once()
