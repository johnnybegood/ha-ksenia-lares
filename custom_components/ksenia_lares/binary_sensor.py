"""This component provides support for Lares motion/door events."""
from datetime import timedelta
import logging


from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DATA_ZONES,
    ZONE_BYPASS_ON,
    ZONE_STATUS_ALARM,
    ZONE_STATUS_NOT_USED,
    DATA_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)

DEFAULT_DEVICE_CLASS = "motion"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors attached to a Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    device_info = await coordinator.client.device_info()
    zone_descriptions = await coordinator.client.zone_descriptions()

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_entities(
        LaresBinarySensor(coordinator, idx, zone_descriptions[idx], device_info)
        for idx, zone in enumerate(coordinator.data[DATA_ZONES])
    )


class LaresBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """An implementation of a Lares door/window/motion sensor."""

    def __init__(self, coordinator, idx, description, device_info) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._description = description
        self._idx = idx

        self._attr_device_info = device_info
        self._attr_device_class = DEFAULT_DEVICE_CLASS

        # Hide sensor if it is indicated as not used
        is_used = (
            self._coordinator.data[DATA_ZONES][self._idx]["status"]
            != ZONE_STATUS_NOT_USED
        )

        self._attr_entity_registry_enabled_default = is_used
        self._attr_entity_registry_visible_default = is_used

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
        return (
            self._coordinator.data[DATA_ZONES][self._idx]["status"] == ZONE_STATUS_ALARM
        )

    @property
    def available(self):
        """Return True if entity is available."""
        status = self._coordinator.data[DATA_ZONES][self._idx]["status"]

        return status != ZONE_STATUS_NOT_USED
