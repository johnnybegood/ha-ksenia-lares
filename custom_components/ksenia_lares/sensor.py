"""This component provides support for Lares partitions."""
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DATA_PARTITIONS,
    PARTITION_STATUS_DISARMED,
    PARTITION_STATUS_ARMED,
    PARTITION_STATUS_ARMED_IMMEDIATE,
    PARTITION_STATUS_ARMING,
    PARTITION_STATUS_PENDING,
    PARTITION_STATUS_ALARM,
    DATA_COORDINATOR,
)

SCAN_INTERVAL = timedelta(seconds=10)
DEFAULT_DEVICE_CLASS = "motion"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors attached to a Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    device_info = await coordinator.client.device_info()
    partition_descriptions = await coordinator.client.partition_descriptions()

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_entities(
        LaresSensor(coordinator, idx, partition_descriptions[idx], device_info)
        for idx, zone in enumerate(coordinator.data[DATA_PARTITIONS])
    )


class LaresSensor(CoordinatorEntity, SensorEntity):
    """An implementation of a Lares partition sensor."""

    def __init__(self, coordinator, idx, description, device_info) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._description = description
        self._idx = idx

        self._attr_icon = "mdi:shield"
        self._attr_device_info = device_info
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = [
            PARTITION_STATUS_DISARMED,
            PARTITION_STATUS_ARMED,
            PARTITION_STATUS_ARMED_IMMEDIATE,
            PARTITION_STATUS_ARMING,
            PARTITION_STATUS_PENDING,
            PARTITION_STATUS_ALARM,
        ]

        # Hide sensor if it has no description
        is_inactive = not self._description

        self._attr_entity_registry_enabled_default = not is_inactive
        self._attr_entity_registry_visible_default = not is_inactive

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"lares_partitions_{self._idx}"

    @property
    def name(self):
        """Return the name of this entity."""
        return self._description

    @property
    def native_value(self):
        """Return the status of this partition."""
        return self._coordinator.data[DATA_PARTITIONS][self._idx]["status"]
