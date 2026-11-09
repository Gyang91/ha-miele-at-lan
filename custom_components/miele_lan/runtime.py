"""Per-entry runtime state, stored on `ConfigEntry.runtime_data`."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry

from .api import MieleLanClient
from .coordinator import MieleLanCoordinator
from .push_listener import MielePushListener

_LOGGER = logging.getLogger(__name__)


@dataclass
class MieleLanRuntimeData:
    """What one household entry holds while it is loaded.

    `coordinators` is keyed by fab number. `setup_complete` turns True once
    every enrolled appliance has its coordinator; pushes that arrive before
    then are an expected race, not an unknown appliance.
    """

    coordinators: dict[str, MieleLanCoordinator] = field(default_factory=dict)
    clients: list[MieleLanClient] = field(default_factory=list)
    listener: MielePushListener | None = None
    setup_complete: bool = False

    async def async_close(self) -> None:
        """Stop the push listener and close every client. Never raises.

        Used by every setup failure path and by unload: a half-started
        listener still holds an mDNS registration and a bound port, and
        leaving it alive makes the next setup attempt fail (issue #2).
        """
        if self.listener is not None:
            try:
                await self.listener.stop()
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("listener stop failed (ignored): %s", err)
        for client in self.clients:
            try:
                await client.__aexit__(None, None, None)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("client close failed (ignored): %s", err)


type MieleLanConfigEntry = ConfigEntry[MieleLanRuntimeData]
