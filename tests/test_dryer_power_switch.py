"""Tumble dryers get the power switch; washers do not."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from custom_components.miele_lan.const import MieleAppliance, wants_power_switch  # noqa: E402


def test_tumble_dryer_gets_the_power_switch() -> None:
    assert wants_power_switch(MieleAppliance.TUMBLE_DRYER, hood_dop1_supported=False)


def test_washers_get_no_power_switch() -> None:
    for device_type in (
        MieleAppliance.WASHING_MACHINE,
        MieleAppliance.WASHER_DRYER,
    ):
        assert not wants_power_switch(device_type, hood_dop1_supported=False)


def test_switch_reads_off_as_status_1() -> None:
    from custom_components.miele_lan import switch

    (d,) = [d for d in switch.SWITCH_TYPES if d.description.key == "power"]
    assert MieleAppliance.TUMBLE_DRYER in d.types
    assert d.description.is_on_fn({"Status": 1}) is False
    assert d.description.is_on_fn({"Status": 7}) is True
