"""Config flow for Ksenia Lares Alarm integration."""
import logging
from typing import Any

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.exceptions import HomeAssistantError
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
    FlowResult,
)
from homeassistant.core import callback, HomeAssistant

from .base import LaresBase
from .const import (
    DOMAIN,
    CONF_PARTITION_AWAY,
    CONF_PARTITION_HOME,
    CONF_PARTITION_NIGHT,
    CONF_SCENARIO_HOME,
    CONF_SCENARIO_AWAY,
    CONF_SCENARIO_NIGHT,
    CONF_SCENARIO_DISARM,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


async def validate_input(hass: HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    client = LaresBase(data)

    info = await client.info()

    if info is None:
        raise InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": info["name"], "id": info["id"]}


class LaresConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ksenia Lares Alarm."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Return the options flow."""
        return LaresOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Abort in case the host was already configured before.
            await self.async_set_unique_id(str(info["id"]))
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class LaresOptionsFlowHandler(OptionsFlow):
    """Handle a options flow for Ksenia Lares Alarm."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.client = LaresBase(config_entry.data)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        partitions = await self.client.partition_descriptions()
        select_partitions = {v: v for v in list(filter(None, partitions)) if v != ""}

        scenarios = await self.client.scenario_descriptions()
        scenarios_with_empty = [""] + scenarios

        options = {
            vol.Required(
                CONF_SCENARIO_DISARM,
                default=self.config_entry.options.get(CONF_SCENARIO_DISARM, ""),
            ): vol.In(scenarios),
            vol.Required(
                CONF_PARTITION_AWAY,
                default=self.config_entry.options.get(CONF_PARTITION_AWAY, []),
            ): cv.multi_select(select_partitions),
            vol.Required(
                CONF_SCENARIO_AWAY,
                default=self.config_entry.options.get(CONF_SCENARIO_AWAY, ""),
            ): vol.In(scenarios),
            vol.Optional(
                CONF_PARTITION_HOME,
                default=self.config_entry.options.get(CONF_PARTITION_HOME, []),
            ): cv.multi_select(select_partitions),
            vol.Optional(
                CONF_SCENARIO_HOME,
                default=self.config_entry.options.get(CONF_SCENARIO_HOME, ""),
            ): vol.In(scenarios_with_empty),
            vol.Optional(
                CONF_PARTITION_NIGHT,
                default=self.config_entry.options.get(CONF_PARTITION_NIGHT, []),
            ): cv.multi_select(select_partitions),
            vol.Optional(
                CONF_SCENARIO_NIGHT,
                default=self.config_entry.options.get(CONF_SCENARIO_NIGHT, ""),
            ): vol.In(scenarios_with_empty),
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
