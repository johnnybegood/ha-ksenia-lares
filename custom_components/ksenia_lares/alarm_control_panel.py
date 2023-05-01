"""This component provides support for Lares alarm  control panel."""
import logging
from datetime import timedelta

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)

from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up alarm control panel of the Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_info = await coordinator.client.device_info()

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_devices([LaresAlarmControlPanel(coordinator, device_info)])


class LaresAlarmControlPanel(CoordinatorEntity, AlarmControlPanelEntity):
    """An implementation of a Lares alarm control panel."""

    TYPE = DOMAIN

    def __init__(self, coordinator, device_info) -> None:
        """Initialize a the switch."""
        super().__init__(coordinator)

        self._cordinator = coordinator
        self._attr_code_format = CodeFormat.NUMBER
        self._attr_device_info = device_info
        self._attr_code_arm_required = False
        self._attr_supported_features = ()

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this entity."""
        name = self._attr_device_info["name"].replace(" ", "_")
        return f"lares_panel_{name}"

    @property
    def name(self):
        """Return the name of this panel."""
        name = self._attr_device_info["name"]
        return f"Panel {name}"

    @property
    def state(self) -> StateType:
        return STATE_ALARM_DISARMED
