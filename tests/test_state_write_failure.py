"""/State writes the appliance acknowledges with HTTP 200 and a `Failure` entry.

Ported from upstream 849e65b: a Wake (DeviceAction 2) on an oven and on a
G6992 dishwasher answered [{"Failure":{"DeviceAction":null}}] and did nothing.
"""
import asyncio

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.miele_lan.api import ActionRejectedError, MieleLanClient

FAB = "000000000000"
FAILURE = b'[{"Failure":{"DeviceAction":null}}]'


class _QueuedRawClient:
    def __init__(self, answers):
        self._answers = list(answers)
        self.calls = []

    async def _request_bytes(self, method, resource, body=None, allowed_status=None):
        self.calls.append((method, resource, body))
        return self._answers.pop(0)


def _run(coro):
    return asyncio.run(coro)


def test_wake_failure_response_is_an_error_not_a_success() -> None:
    stub = _QueuedRawClient([(200, FAILURE)])
    with pytest.raises(ActionRejectedError) as exc_info:
        _run(MieleLanClient(stub, route=FAB).wake())
    message = str(exc_info.value)
    assert "does not support this action" in message
    assert "DeviceAction" in message


def test_wake_success_response_is_returned() -> None:
    stub = _QueuedRawClient([(200, b'[{"Success":{"DeviceAction":0}}]')])
    assert _run(MieleLanClient(stub, route=FAB).wake()) == {"Success": {"DeviceAction": 0}}


def test_light_failure_response_is_an_error() -> None:
    stub = _QueuedRawClient([(200, b'[{"Failure":{"Light":null}}]')])
    with pytest.raises(HomeAssistantError):
        _run(MieleLanClient(stub, route=FAB).light_on())


def test_process_action_failure_response_is_an_error() -> None:
    stub = _QueuedRawClient([(200, b'[{"Failure":{"ProcessAction":null}}]')])
    with pytest.raises(ActionRejectedError):
        _run(MieleLanClient(stub, route=FAB).start_process())


@pytest.mark.parametrize("raw", [b"", b"not json", b"[]", b'[{"Success":{"Light":2}}]'])
def test_responses_without_a_failure_entry_are_accepted(raw) -> None:
    stub = _QueuedRawClient([(200, raw)])
    _run(MieleLanClient(stub, route=FAB).wake())
    stub = _QueuedRawClient([(200, raw)])
    _run(MieleLanClient(stub, route=FAB).start_process())
