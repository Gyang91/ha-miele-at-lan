"""DOP2 2/1585 entities appear once the leaf first answers.

An appliance asleep when Home Assistant starts has no device context yet.
Its Wash2Dry / TwinDos / consumable entities must then be added when the
first answer arrives, not only after a reload (before, a wake at startup
forced that first answer).
"""

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from custom_components.miele_lan import binary_sensor, sensor  # noqa: E402
from custom_components.miele_lan.const import MieleAppliance  # noqa: E402
from custom_components.miele_lan.coordinator import MieleLanData  # noqa: E402
from custom_components.miele_lan.entity import add_entities_when_ready  # noqa: E402

CONTEXT = {
    "wash2dry_state": "activatable",
    "dos_containers": [
        {"bitmask_inserted": True, "filling_level_pct": 80, "current_dosage_ml": 60},
        {"bitmask_inserted": True, "filling_level_pct": 40, "current_dosage_ml": 30},
    ],
}


class _Coord:
    """Coordinator stand-in: holds data and lets the test fire updates."""

    def __init__(self, device_type: MieleAppliance, context: dict | None = None) -> None:
        self.data = MieleLanData()
        self.data.ident = {"device_type": int(device_type)}
        self.data.device_context = dict(context or {})
        self.device_type = device_type
        self.client = SimpleNamespace(route="000000000001", host="192.0.2.1")
        self.listeners: list = []
        self.removed = 0

    def async_add_listener(self, cb):
        self.listeners.append(cb)

        def remove() -> None:
            self.listeners.remove(cb)
            self.removed += 1

        return remove

    def fire(self) -> None:
        for cb in list(self.listeners):
            cb()


class _Entry:
    def __init__(self) -> None:
        self.on_unload: list = []

    def async_on_unload(self, fn) -> None:
        self.on_unload.append(fn)

    def unload(self) -> None:
        for fn in self.on_unload:
            fn()


def _keys(added: list) -> set[str]:
    return {e.entity_description.key for batch in added for e in batch}


def test_added_immediately_when_context_present() -> None:
    coord, entry, added = _Coord(MieleAppliance.WASHING_MACHINE, CONTEXT), _Entry(), []
    add_entities_when_ready(entry, coord, sensor._device_context_sensors, added.append)
    assert "wash2dry_state" in _keys(added)
    assert "twindos_2_level" in _keys(added)
    assert coord.listeners == []


def test_added_once_when_first_answer_arrives_later() -> None:
    coord, entry, added = _Coord(MieleAppliance.TUMBLE_DRYER), _Entry(), []
    add_entities_when_ready(entry, coord, sensor._device_context_sensors, added.append)
    assert added == []
    coord.fire()  # a poll without an answer from the leaf
    assert added == []

    coord.data.device_context = dict(CONTEXT)
    coord.fire()
    assert _keys(added) == {"wash2dry_state"}  # dryer: no TwinDos
    assert coord.listeners == []

    coord.fire()
    assert len(added) == 1  # never added twice


def test_binary_sensors_follow_the_same_path() -> None:
    coord, entry, added = _Coord(MieleAppliance.WASHING_MACHINE), _Entry(), []
    add_entities_when_ready(
        entry, coord, binary_sensor._device_context_binary_sensors, added.append
    )
    assert added == []
    coord.data.device_context = dict(CONTEXT)
    coord.fire()
    assert _keys(added) == {"twindos_1_empty", "twindos_2_empty"}


def test_unload_removes_a_waiting_listener_exactly_once() -> None:
    coord, entry, added = _Coord(MieleAppliance.TUMBLE_DRYER), _Entry(), []
    add_entities_when_ready(entry, coord, sensor._device_context_sensors, added.append)
    entry.unload()
    assert coord.listeners == []
    assert coord.removed == 1


def test_unload_after_late_add_does_not_remove_twice() -> None:
    coord, entry, added = _Coord(MieleAppliance.TUMBLE_DRYER), _Entry(), []
    add_entities_when_ready(entry, coord, sensor._device_context_sensors, added.append)
    coord.data.device_context = dict(CONTEXT)
    coord.fire()
    entry.unload()
    assert coord.removed == 1
