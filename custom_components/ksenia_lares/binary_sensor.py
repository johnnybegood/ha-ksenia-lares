"""This component provides support for Lares motion/door events."""
import asyncio
import datetime
from datetime import timedelta
import logging

import async_timeout

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .base import LaresBase
from .const import (
    DEFAULT_TIMEOUT,
    ZONE_BYPASS_ON,
    ZONE_STATUS_ALARM,
    ZONE_STATUS_NOT_USED,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)

DEFAULT_DEVICE_CLASS = "motion"
DOOR_DEVICE_CLASS = "door"


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up binary sensors attached to a Lares alarm device from a config entry."""

    client = LaresBase(config_entry.data)
    descriptions = await client.zoneDescriptions()
    device_info = await client.device_info()

    async def async_update_data():
        """Perform the actual updates."""

        async with async_timeout.timeout(DEFAULT_TIMEOUT):
            return await client.zones()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="lares_zones",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_devices(
        LaresSensor(coordinator, idx, descriptions[idx], device_info)
        for idx, zone in enumerate(coordinator.data)
    )


class LaresSensor(CoordinatorEntity, BinarySensorEntity):
    """An implementation of a Lares door/window/motion sensor."""

    def __init__(self, coordinator, idx, description, device_info):
        """Initialize a the switch."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._description = description
        self._idx = idx
        self._device_info = device_info

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"lares_zones_{self._idx}"

    @property
    def name(self):
        """Return the name of this camera."""
        return self._description

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._coordinator.data[self._idx]["status"] == ZONE_STATUS_ALARM

    @property
    def available(self):
        """Return True if entity is available."""
        status = self._coordinator.data[self._idx]["status"]

        return status != ZONE_STATUS_NOT_USED or status == ZONE_BYPASS_ON

    @property
    def device_class(self):
        """Return the class of this device."""
        return DEFAULT_DEVICE_CLASS

    @property
    def device_info(self):
        """Return basic information of this device."""
        return self._device_info
