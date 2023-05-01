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
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMING,
)

from .coordinator import DataUpdateCoordinator
from .const import (
    DOMAIN,
    DATA_COORDINATOR,
    DATA_PARTITIONS,
    PARTITION_STATUS_ARMED,
    PARTITION_STATUS_ARMED_IMMEDIATE,
    PARTITION_STATUS_ARMING,
    CONF_PARTITION_AWAY,
    CONF_PARTITION_HOME,
    CONF_PARTITION_NIGHT,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up alarm control panel of the Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    device_info = await coordinator.client.device_info()
    partition_descriptions = await coordinator.client.partition_descriptions()

    options = {
        CONF_PARTITION_AWAY: config_entry.options.get(CONF_PARTITION_AWAY, []),
        CONF_PARTITION_HOME: config_entry.options.get(CONF_PARTITION_HOME, []),
        CONF_PARTITION_NIGHT: config_entry.options.get(CONF_PARTITION_NIGHT, []),
    }

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_devices(
        [
            LaresAlarmControlPanel(
                coordinator, device_info, partition_descriptions, options
            )
        ]
    )


class LaresAlarmControlPanel(CoordinatorEntity, AlarmControlPanelEntity):
    """An implementation of a Lares alarm control panel."""

    TYPE = DOMAIN
    ARMED_STATUS = [PARTITION_STATUS_ARMED, PARTITION_STATUS_ARMED_IMMEDIATE]

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_info: dict,
        partition_descriptions: dict,
        options: dict,
    ) -> None:
        """Initialize a the switch."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._partition_descriptions = partition_descriptions
        self._options = options
        self._attr_code_format = CodeFormat.NUMBER
        self._attr_device_info = device_info
        self._attr_code_arm_required = True

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
        """Return the state of this panel."""
        if self.has_partition_with_status(PARTITION_STATUS_ARMING):
            return STATE_ALARM_ARMING

        if self.is_armed(CONF_PARTITION_AWAY):
            return STATE_ALARM_ARMED_AWAY

        if self.is_armed(CONF_PARTITION_HOME):
            return STATE_ALARM_ARMED_HOME

        if self.is_armed(CONF_PARTITION_NIGHT):
            return STATE_ALARM_ARMED_NIGHT

        # If any of the not mapped partitions is armed, show custom as fallback
        if self.has_partition_with_status(self.ARMED_STATUS):
            return STATE_ALARM_ARMED_CUSTOM_BYPASS

        return STATE_ALARM_DISARMED

    def has_partition_with_status(self, status_list: list[str]) -> bool:
        """Return if any partitions is arming."""
        partitions = enumerate(self._coordinator.data[DATA_PARTITIONS])
        in_state = list(
            idx for idx, partition in partitions if partition["status"] in status_list
        )

        _LOGGER.debug("%s in status %s", in_state, status_list)

        return len(in_state) > 0

    def is_armed(self, key: str) -> bool:
        """Return if all partitions linked to the configuration key are armed."""
        partition_names = self._options[key]

        # Skip the check if no partitions are linked
        if len(partition_names) == 0:
            _LOGGER.debug("Skipping %s armed check, no definition", key)
            return False

        descriptions = enumerate(self._partition_descriptions)
        to_check = (idx for idx, name in descriptions if name in partition_names)

        _LOGGER.debug("Checking %s (%s) for %s", partition_names, to_check, key)

        for idx in to_check:
            if (
                self._coordinator.data[DATA_PARTITIONS][idx]["status"]
                not in self.ARMED_STATUS
            ):
                return False

        return True
