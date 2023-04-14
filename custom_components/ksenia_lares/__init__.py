"""The Ksenia Lares Alarm integration."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict
from async_timeout import timeout

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .base import LaresBase
from .const import DOMAIN, DEFAULT_TIMEOUT

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
PLATFORMS = ["binary_sensor", "alarm_control_panel"]
SCAN_INTERVAL = timedelta(seconds=10)
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Ksenia Lares Alarm component."""

    coordinator = LaresDataUpdateCoordinator(hass, config)
    await coordinator.async_config_entry_first_refresh()
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Ksenia Lares Alarm from a config entry."""
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *(
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            )
        )
    )

    return unload_ok


class LaresDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching data from Ksenia Lares API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict,
    ) -> None:
        """Initialize."""
        self._config = config
        self._hass = hass
        self._client = LaresBase(self._config)

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        async with timeout(DEFAULT_TIMEOUT):
            zones = await self._client.zones()
            partitions = await self._client.paritions()

        return {**zones, **partitions}
