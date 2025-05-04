"""Component to interface with a Lares Ksenia alarm control panel."""

from datetime import timedelta
import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_PARTITION_AWAY,
    CONF_PARTITION_HOME,
    CONF_PARTITION_NIGHT,
    CONF_SCENARIO_AWAY,
    CONF_SCENARIO_DISARM,
    CONF_SCENARIO_HOME,
    CONF_SCENARIO_NIGHT,
    DATA_COORDINATOR,
    DATA_PARTITIONS,
    DOMAIN,
    PARTITION_STATUS_ARMED,
    PARTITION_STATUS_ARMED_IMMEDIATE,
    PARTITION_STATUS_ARMING,
)
from .coordinator import LaresDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up alarm control panel of the Lares alarm device from a config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    device_info = await coordinator.client.device_info()
    partition_descriptions = await coordinator.client.partition_descriptions()
    scenario_descriptions = await coordinator.client.scenario_descriptions()

    options = {
        CONF_PARTITION_AWAY: config_entry.options.get(CONF_PARTITION_AWAY, []),
        CONF_PARTITION_HOME: config_entry.options.get(CONF_PARTITION_HOME, []),
        CONF_PARTITION_NIGHT: config_entry.options.get(CONF_PARTITION_NIGHT, []),
        CONF_SCENARIO_NIGHT: config_entry.options.get(CONF_SCENARIO_NIGHT, []),
        CONF_SCENARIO_HOME: config_entry.options.get(CONF_SCENARIO_HOME, []),
        CONF_SCENARIO_AWAY: config_entry.options.get(CONF_SCENARIO_AWAY, []),
        CONF_SCENARIO_DISARM: config_entry.options.get(CONF_SCENARIO_DISARM, []),
    }

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_devices(
        [
            LaresAlarmControlPanel(
                coordinator,
                device_info,
                partition_descriptions,
                scenario_descriptions,
                options,
            )
        ]
    )


class LaresAlarmControlPanel(CoordinatorEntity, AlarmControlPanelEntity):
    """An implementation of a Lares alarm control panel."""

    TYPE = DOMAIN
    ARMED_STATUS = [PARTITION_STATUS_ARMED, PARTITION_STATUS_ARMED_IMMEDIATE]

    def __init__(
        self,
        coordinator: LaresDataUpdateCoordinator,
        device_info: dict,
        partition_descriptions: dict,
        scenario_descriptions: dict,
        options: dict,
    ) -> None:
        """Initialize a the switch."""
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._partition_descriptions = partition_descriptions
        self._scenario_descriptions = scenario_descriptions
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
    def supported_features(self) -> AlarmControlPanelEntityFeature:
        """Return the list of supported features."""
        supported_features = AlarmControlPanelEntityFeature(0)

        if self._options[CONF_SCENARIO_AWAY] != "":
            supported_features |= AlarmControlPanelEntityFeature.ARM_AWAY

        if self._options[CONF_SCENARIO_HOME] != "":
            supported_features |= AlarmControlPanelEntityFeature.ARM_HOME

        if self._options[CONF_SCENARIO_NIGHT] != "":
            supported_features |= AlarmControlPanelEntityFeature.ARM_NIGHT

        return supported_features

    @property
    def state(self) -> StateType:
        """Return the state of this panel."""
        if self.__has_partition_with_status(PARTITION_STATUS_ARMING):
            return AlarmControlPanelState.ARMING

        if self.__is_armed(CONF_PARTITION_AWAY):
            return AlarmControlPanelState.ARMED_AWAY

        if self.__is_armed(CONF_PARTITION_HOME):
            return AlarmControlPanelState.ARMED_HOME

        if self.__is_armed(CONF_PARTITION_NIGHT):
            return AlarmControlPanelState.ARMED_NIGHT

        # If any of the not mapped partitions is armed, show custom as fallback
        if self.__has_partition_with_status(self.ARMED_STATUS):
            return AlarmControlPanelState.ARMED_CUSTOM_BYPASS

        return AlarmControlPanelState.DISARMED

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.__command(CONF_SCENARIO_HOME, code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.__command(CONF_SCENARIO_AWAY, code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.__command(CONF_SCENARIO_NIGHT, code)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self.__command(CONF_SCENARIO_DISARM, code)

    def __has_partition_with_status(self, status_list: list[str]) -> bool:
        """Return if any partitions is arming."""
        partitions = enumerate(self._coordinator.data[DATA_PARTITIONS])
        in_state = [
            idx for idx, partition in partitions if partition["status"] in status_list
        ]

        _LOGGER.debug("%s in status %s", in_state, status_list)

        return len(in_state) > 0

    def __is_armed(self, key: str) -> bool:
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

    async def __command(self, key: str, code: str | None = None) -> None:
        """Send arm home command."""
        scenario_name = self._options[key]

        if scenario_name is None:
            _LOGGER.warning("Skipping command, no definition for %s", key)
            return

        descriptions = enumerate(self._scenario_descriptions)
        match_gen = (idx for idx, name in descriptions if name == scenario_name)
        matches = list(match_gen)

        if len(matches) != 1:
            _LOGGER.error("No match for %s (%s found)", key, len(matches))
            return

        scenario = matches[0]
        _LOGGER.debug("Activating scenario %s", scenario)

        await self._coordinator.client.activate_scenario(scenario, code)
