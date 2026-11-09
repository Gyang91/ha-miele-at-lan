"""Transport and lifecycle reliability.

- Every aiohttp failure becomes NetworkConnectionError, so user commands get
  a readable error instead of "Unknown error".
- Requests to one appliance run one at a time.
- /State writes: 400 is a no-op success, any other status a readable error.
- TwinDos entities exist only for washers, never for dryers.
- Runtime cleanup never raises and closes everything.
"""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import aiohttp
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from asyncmiele import MieleClient  # noqa: E402
from asyncmiele.exceptions.network import (  # noqa: E402
    NetworkConnectionError,
    ResponseError,
)
from homeassistant.exceptions import HomeAssistantError  # noqa: E402

from custom_components.miele_lan.api import MieleLanClient, _install_patches  # noqa: E402
from custom_components.miele_lan.const import (  # noqa: E402
    LAUNDRY_FAMILY,
    TWINDOS_FAMILY,
    MieleAppliance,
)
from custom_components.miele_lan.dop2 import dos_container_field  # noqa: E402
from custom_components.miele_lan.runtime import MieleLanRuntimeData  # noqa: E402

GROUP_ID = "00" * 8
GROUP_KEY = "11" * 64


class _Response:
    status = 200
    headers: dict = {}

    async def read(self) -> bytes:
        return b""


class _Request:
    def __init__(self, session: "_Session") -> None:
        self._session = session

    async def __aenter__(self) -> _Response:
        s = self._session
        s.active += 1
        s.max_active = max(s.max_active, s.active)
        try:
            await asyncio.sleep(s.delay)
            if s.exc is not None:
                raise s.exc
        finally:
            s.active -= 1
        return _Response()

    async def __aexit__(self, *exc_info) -> None:
        return None


class _Session:
    def __init__(self, exc: Exception | None = None, delay: float = 0.0) -> None:
        self.exc = exc
        self.delay = delay
        self.active = 0
        self.max_active = 0

    def request(self, *args, **kwargs) -> _Request:
        return _Request(self)


def _raw_client(session: _Session) -> MieleClient:
    _install_patches()
    client = MieleClient.from_hex("192.0.2.1", GROUP_ID, GROUP_KEY)
    client._get_session = AsyncMock(return_value=session)  # type: ignore[method-assign]
    return client


# ------------------------------------------------------------------ transport
@pytest.mark.parametrize(
    "exc",
    [
        aiohttp.ServerDisconnectedError(),
        aiohttp.ClientOSError(104, "Connection reset by peer"),
        aiohttp.ClientPayloadError("truncated"),
    ],
)
def test_any_aiohttp_error_becomes_network_connection_error(exc: Exception) -> None:
    client = _raw_client(_Session(exc=exc))
    with pytest.raises(NetworkConnectionError) as info:
        asyncio.run(client._request_bytes("GET", "/Devices/x/State"))
    assert type(exc).__name__ in str(info.value)


def test_dropped_connection_gives_a_readable_command_error() -> None:
    client = MieleLanClient(
        _raw_client(_Session(exc=aiohttp.ServerDisconnectedError())), route="x"
    )
    with pytest.raises(HomeAssistantError) as info:
        asyncio.run(client.send_process_action(1))
    assert str(info.value) == "Could not connect to the appliance."


def test_requests_to_one_appliance_run_one_at_a_time() -> None:
    session = _Session(delay=0.01)
    client = _raw_client(session)

    async def burst() -> None:
        await asyncio.gather(*(client._request_bytes("GET", f"/r{i}") for i in range(5)))

    asyncio.run(burst())
    assert session.max_active == 1


def test_different_appliances_are_not_serialised_against_each_other() -> None:
    session = _Session(delay=0.01)
    a, b = _raw_client(session), _raw_client(session)

    async def both() -> None:
        await asyncio.gather(a._request_bytes("GET", "/a"), b._request_bytes("GET", "/b"))

    asyncio.run(both())
    assert session.max_active == 2


# ------------------------------------------------------------- /State writes
class _StatusRaw:
    def __init__(self, status: int) -> None:
        self.status = status

    async def _request_bytes(self, *args, **kwargs):
        raise ResponseError(self.status, "stub")


def test_put_state_400_is_a_no_op_success() -> None:
    client = MieleLanClient(_StatusRaw(400), route="x")
    assert asyncio.run(client.light_on()) is None


def test_put_state_other_status_is_a_readable_error() -> None:
    client = MieleLanClient(_StatusRaw(500), route="x")
    with pytest.raises(HomeAssistantError) as info:
        asyncio.run(client.light_on())
    assert str(info.value) == "The appliance refused this command (HTTP 500)."


# ------------------------------------------------------------------- TwinDos
def test_twindos_family_is_washers_only() -> None:
    dryers = {
        MieleAppliance.TUMBLE_DRYER,
        MieleAppliance.TUMBLE_DRYER_SEMI_PROFESSIONAL,
        MieleAppliance.DRYER_PROFESSIONAL,
    }
    assert set(TWINDOS_FAMILY) == set(LAUNDRY_FAMILY) - dryers


@pytest.mark.parametrize("module,defs", [
    ("sensor", "DEVICE_CONTEXT_SENSORS"),
    ("binary_sensor", "DEVICE_CONTEXT_BINARY_SENSORS"),
])
def test_dryer_gets_no_twindos_entities_but_washer_does(module: str, defs: str) -> None:
    import importlib

    mod = importlib.import_module(f"custom_components.miele_lan.{module}")

    def keys(device_type: MieleAppliance) -> set[str]:
        return {
            d.description.key for d in getattr(mod, defs)
            if device_type in d.types and d.description.key.startswith("twindos")
        }

    assert keys(MieleAppliance.TUMBLE_DRYER) == set()
    assert keys(MieleAppliance.WASHING_MACHINE)


def test_dryer_keeps_wash2dry() -> None:
    from custom_components.miele_lan import sensor

    (wash2dry,) = [
        d for d in sensor.DEVICE_CONTEXT_SENSORS if d.description.key == "wash2dry_state"
    ]
    assert MieleAppliance.TUMBLE_DRYER in wash2dry.types


def test_container_field_is_unknown_when_not_inserted() -> None:
    ctx = {"dos_containers": [
        {"bitmask_inserted": False, "bitmask_empty": False, "filling_level_pct": 0},
        {"bitmask_inserted": True, "bitmask_empty": True, "filling_level_pct": 0},
    ]}
    assert dos_container_field(ctx, 0, "bitmask_empty") is None
    assert dos_container_field(ctx, 1, "bitmask_empty") is True
    assert dos_container_field(ctx, 2, "bitmask_empty") is None
    assert dos_container_field({}, 0, "filling_level_pct") is None


# ------------------------------------------------------------------- runtime
def test_runtime_close_never_raises_and_closes_everything() -> None:
    listener = SimpleNamespace(stop=AsyncMock(side_effect=OSError("port")))
    good = SimpleNamespace(__aexit__=AsyncMock())
    bad = SimpleNamespace(__aexit__=AsyncMock(side_effect=RuntimeError("boom")))
    last = SimpleNamespace(__aexit__=AsyncMock())

    class _Client:
        def __init__(self, ns: SimpleNamespace) -> None:
            self.ns = ns

        async def __aexit__(self, *exc_info) -> None:
            await self.ns.__aexit__(*exc_info)

    runtime = MieleLanRuntimeData(
        listener=listener,  # type: ignore[arg-type]
        clients=[_Client(good), _Client(bad), _Client(last)],  # type: ignore[list-item]
    )
    asyncio.run(runtime.async_close())
    listener.stop.assert_awaited_once()
    for ns in (good, bad, last):
        ns.__aexit__.assert_awaited_once()
