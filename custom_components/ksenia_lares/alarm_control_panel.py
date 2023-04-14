"""This component provides support for Lares alarm  control panel."""
import logging
import async_timeout
from datetime import timedelta

from voluptuous.validators import Switch

from homeassistant.core import callback
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    FORMAT_NUMBER,
)
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)

from .base import LaresBase
from .const import DOMAIN, DEFAULT_TIMEOUT, DISARMED_STATE

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up alarm control panel of the Lares alarm device from a config entry."""

    client = LaresBase(config_entry.data)
    device_info = await client.device_info()

    async def async_update_data():
        """Perform the actual updates."""
        async with async_timeout.timeout(DEFAULT_TIMEOUT):
            return await client.paritions()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="lares_panel",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_devices(
        [LaresAlarmControlPanel(coordinator, coordinator.data, device_info)]
    )


class LaresAlarmControlPanel(CoordinatorEntity, AlarmControlPanelEntity):
    """An implementation of a Lares alarm control panel."""

    TYPE = DOMAIN

    _attr_code_arm_required = False
    _attr_supported_features = SUPPORT_ALARM_ARM_AWAY | SUPPORT_ALARM_ARM_HOME

    def __init__(self, coordinator, partitions, device_info):
        """Initialize a the switch."""
        super().__init__(coordinator)

        self._cordinator = coordinator
        self._device_info = device_info
        self._partitions = partitions
        self._attr_state = STATE_ALARM_DISARMED

    @property
    def code_format(self):
        """Return the alarm code format."""
        return FORMAT_NUMBER

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this entity."""
        name = self._device_info["name"]
        return f"lares_panel_{name}"

    @property
    def device_info(self):
        """Return basic information of this device."""
        return self._device_info

    @property
    def name(self):
        """Return the name of this camera."""
        name = self._device_info["name"]
        return f"Panel {name}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        disarmed = len(filter(lambda p: p[1] == DISARMED_STATE, self._partitions))
        total = len(self._partitions)

        if disarmed == 0:
            self._attr_state = STATE_ALARM_ARMED_AWAY

        elif disarmed == total:
            self._attr_state = STATE_ALARM_ARMED_HOME

        else:
            self._attr_state = STATE_ALARM_DISARMED

        self._attr_changed_by = self._device_info["name"]
        super()._handle_coordinator_update()
