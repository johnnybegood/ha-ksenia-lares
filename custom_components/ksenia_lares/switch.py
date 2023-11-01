"""This component provides support for Lares zone bypass."""
from datetime import timedelta

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DATA_ZONES,
    ZONE_BYPASS_ON,
    ZONE_STATUS_NOT_USED,
    DATA_COORDINATOR,
)

SCAN_INTERVAL = timedelta(seconds=10)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up zone bypass switches for zones in the Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    device_info = await coordinator.client.device_info()
    zone_descriptions = await coordinator.client.zone_descriptions()

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_entities(
        LaresBypassSwitch(coordinator, idx, zone_descriptions[idx], device_info)
        for idx, zone in enumerate(coordinator.data[DATA_ZONES])
    )


class LaresBypassSwitch(CoordinatorEntity, SwitchEntity):
    """An implementation of a Lares zone bypass switch."""

    _attr_translation_key = "bypass"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:shield-off"

    def __init__(self, coordinator, idx, description, device_info) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._description = description
        self._idx = idx

        self._attr_unique_id = f"lares_bypass_{self._idx}"
        self._attr_device_info = device_info
        self._attr_name = description

        is_used = (
            self._coordinator.data[DATA_ZONES][self._idx]["status"] != ZONE_STATUS_NOT_USED
        )

        self._attr_entity_registry_enabled_default = is_used
        self._attr_entity_registry_visible_default = is_used

    @property
    def is_on(self) -> bool | None:
        """Return true if the zone is bypassed."""
        status = self._coordinator.data[DATA_ZONES][self._idx]["status"]
        return status == ZONE_BYPASS_ON
