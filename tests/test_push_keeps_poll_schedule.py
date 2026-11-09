"""A push updates entities but must not postpone the next poll.

A running appliance pushes about every 30 s. When each push restarted the
60 s poll timer, the appliance was never polled during a programme, so the
poll-only reads (DOP2 2/1585, WLAN, hours of operation) went stale.
"""

from types import SimpleNamespace

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import frame

from custom_components.miele_lan.const import MieleAppliance
from custom_components.miele_lan.coordinator import MieleLanCoordinator
from custom_components.miele_lan.push_listener import PushEvent

FAB = "000000000001"


def _push(content: dict) -> PushEvent:
    return PushEvent(
        peer_fab=FAB, resource=f"/Devices/{FAB}/State/", content=content,
        host_name=None, raw_plain="",
    )


@pytest.mark.asyncio
async def test_push_updates_listeners_without_moving_the_poll(tmp_path, monkeypatch):
    monkeypatch.setattr(frame, "report_usage", lambda *args, **kwargs: None)
    hass = HomeAssistant(str(tmp_path))
    coord = MieleLanCoordinator(
        hass, SimpleNamespace(entry_id="test"),
        SimpleNamespace(route=FAB, host="192.0.2.1"), FAB,
    )
    coord._data.ident = {"device_type": int(MieleAppliance.TUMBLE_DRYER)}

    calls = []
    remove = coord.async_add_listener(lambda: calls.append(dict(coord.data.state)))
    scheduled = coord._unsub_refresh
    assert scheduled is not None  # a listener schedules the next poll

    coord.apply_push(_push({"Status": 5, "RemainingTime": [1, 30]}))
    coord.apply_push(_push({"RemainingTime": [1, 29]}))

    assert coord._unsub_refresh is scheduled  # poll timer untouched
    assert calls[-1]["RemainingTime"] == [1, 29]
    assert calls[-1]["Status"] == 5
    assert coord.last_update_success is True
    remove()
    await hass.async_stop(force=True)
