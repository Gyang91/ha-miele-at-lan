"""Lifetime energy / water totals from DOP2 2/1585 attributes 5 and 6."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from custom_components.miele_lan import sensor  # noqa: E402
from custom_components.miele_lan.const import MieleAppliance  # noqa: E402
from custom_components.miele_lan.coordinator import MieleLanData  # noqa: E402
from custom_components.miele_lan.dop2 import parse_global_device_context  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def _ctx(name: str) -> dict:
    raw = (FIXTURES / name).read_text().replace("\n", "").replace(" ", "")
    return parse_global_device_context(bytes.fromhex(raw))


@pytest.mark.parametrize("fixture,energy_wh,water_l", [
    # G7655 values match the Miele app on the capture date (upstream PR #63).
    ("g7655_dop2_1585.hex", 182600, 2447),
    # EK037 tumble dryer: keeps energy (~231 kWh fits ~0.4 kWh per run in
    # the app), keeps no water counter.
    ("ek037_tumble_dryer_dop2_1585.hex", 231112, None),
    # A washer-dryer capture without these attributes.
    ("wtw870_dop2_1585.hex", None, None),
])
def test_lifetime_counters(fixture: str, energy_wh, water_l) -> None:
    ctx = _ctx(fixture)
    assert ctx["lifetime_energy_wh"] == energy_wh
    assert ctx["lifetime_water_l"] == water_l


def test_program_counter_rises_with_the_lifetime_counter() -> None:
    """Two captures of one drying run, about 20 minutes apart."""
    before = _ctx("ek037_tumble_dryer_dop2_1585.hex")
    after = _ctx("ek037_tumble_dryer_dop2_1585_later.hex")
    assert (before["program_energy_wh"], after["program_energy_wh"]) == (56, 109)
    assert after["lifetime_energy_wh"] - before["lifetime_energy_wh"] == 53
    assert after["program_energy_wh"] - before["program_energy_wh"] == 53
    assert after["program_water_l"] is None


def test_dishwashers_keep_no_program_counters() -> None:
    ctx = _ctx("g7655_dop2_1585.hex")
    assert ctx["program_energy_wh"] is None
    assert ctx["program_water_l"] is None


def test_dryer_parse_keeps_wash2dry() -> None:
    assert _ctx("ek037_tumble_dryer_dop2_1585.hex")["wash2dry_state"] == "active"


class _Coord:
    def __init__(self, device_type: MieleAppliance, ctx: dict) -> None:
        from types import SimpleNamespace

        self.data = MieleLanData()
        self.data.ident = {"device_type": int(device_type)}
        self.data.device_context = ctx
        self.device_type = device_type
        self.client = SimpleNamespace(route="000000000001", host="192.0.2.1")


def _keys(coord) -> set[str]:
    return {e.entity_description.key for e in sensor._device_context_sensors(coord)}


def test_dryer_gets_energy_but_no_water_sensors() -> None:
    keys = _keys(_Coord(MieleAppliance.TUMBLE_DRYER, _ctx("ek037_tumble_dryer_dop2_1585.hex")))
    assert {"lifetime_energy", "program_energy"} <= keys
    assert keys.isdisjoint({"lifetime_water", "program_water"})


def test_dishwasher_gets_both_sensors() -> None:
    keys = _keys(_Coord(MieleAppliance.DISHWASHER, _ctx("g7655_dop2_1585.hex")))
    assert {"lifetime_energy", "lifetime_water"} <= keys


def test_no_sensor_without_the_counter() -> None:
    keys = _keys(_Coord(MieleAppliance.WASHER_DRYER, _ctx("wtw870_dop2_1585.hex")))
    assert keys.isdisjoint({"lifetime_energy", "lifetime_water"})


def test_energy_sensor_is_energy_dashboard_ready() -> None:
    from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

    (d,) = [d for d in sensor.DEVICE_CONTEXT_SENSORS if d.description.key == "lifetime_energy"]
    assert d.description.device_class is SensorDeviceClass.ENERGY
    assert d.description.state_class is SensorStateClass.TOTAL_INCREASING
    assert d.description.native_unit_of_measurement == "Wh"
