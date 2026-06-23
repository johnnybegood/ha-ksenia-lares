"""This component provides support for Lares zone bypass."""
import logging
from datetime import timedelta

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LaresDataUpdateCoordinator
from .const import (
    DOMAIN,
    DATA_ZONES,
    DATA_OUTPUTS,
    ZONE_BYPASS_ON,
    ZONE_STATUS_NOT_USED,
    OUTPUT_STATUS_ON,
    OUTPUT_TYPE_NOT_USED,
    DATA_COORDINATOR,
    CONF_PIN,
)

_LOGGER = logging.getLogger(__name__)
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
    output_descriptions = await coordinator.client.output_descriptions()
    options = { CONF_PIN: config_entry.options.get(CONF_PIN)}

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    entities = [
        LaresBypassSwitch(coordinator, idx, zone_descriptions[idx], device_info, options)
        for idx, zone in enumerate(coordinator.data[DATA_ZONES])
    ]

    entities += [
        LaresOutputSwitch(coordinator, idx, output_descriptions[idx], device_info, options)
        for idx, output in enumerate(coordinator.data[DATA_OUTPUTS] or [])
    ]

    async_add_entities(entities)


class LaresBypassSwitch(CoordinatorEntity, SwitchEntity):
    """An implementation of a Lares zone bypass switch."""

    _attr_translation_key = "bypass"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:shield-off"

    def __init__(self, coordinator: LaresDataUpdateCoordinator, idx: int, description: str, device_info: dict, options: dict) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._idx = idx
        self._pin = options[CONF_PIN]

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
        status = self._coordinator.data[DATA_ZONES][self._idx]["bypass"]
        return status == ZONE_BYPASS_ON

    async def async_turn_on(self, **kwargs):
        """Bypass the zone."""
        if self._pin is None:
            _LOGGER.error("Pin needed for bypass zone")
            return

        await self._coordinator.client.bypass_zone(self._idx, self._pin, True)

    async def async_turn_off(self, **kwargs):
        """Unbypass the zone."""
        if self._pin is None:
            _LOGGER.error("Pin needed for unbypass zone")
            return

        await self._coordinator.client.bypass_zone(self._idx, self._pin, False)


class LaresOutputSwitch(CoordinatorEntity, SwitchEntity):
    """An implementation of a Lares output (automation) switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:export"

    def __init__(self, coordinator: LaresDataUpdateCoordinator, idx: int, description: str, device_info: dict, options: dict) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._idx = idx
        self._pin = options[CONF_PIN]

        self._attr_unique_id = f"lares_output_{self._idx}"
        self._attr_device_info = device_info
        self._attr_name = description

        output = self._coordinator.data[DATA_OUTPUTS][self._idx]

        # Only outputs that are in use and remotely controllable are shown by
        # default; everything else stays hidden+disabled in the registry.
        is_controllable = (
            output["type"] != OUTPUT_TYPE_NOT_USED and output["remoteControl"]
        )

        self._attr_entity_registry_enabled_default = is_controllable
        self._attr_entity_registry_visible_default = is_controllable

    @property
    def is_on(self) -> bool | None:
        """Return true if the output is on."""
        status = self._coordinator.data[DATA_OUTPUTS][self._idx]["status"]
        return status == OUTPUT_STATUS_ON

    @property
    def available(self) -> bool:
        """Return True if the output is in use."""
        output = self._coordinator.data[DATA_OUTPUTS][self._idx]
        return output["type"] != OUTPUT_TYPE_NOT_USED

    async def async_turn_on(self, **kwargs):
        """Turn the output on."""
        if self._pin is None:
            _LOGGER.error("Pin needed to control output")
            return

        await self._coordinator.client.set_output(self._idx, self._pin, True)
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the output off."""
        if self._pin is None:
            _LOGGER.error("Pin needed to control output")
            return

        await self._coordinator.client.set_output(self._idx, self._pin, False)
        await self._coordinator.async_request_refresh()