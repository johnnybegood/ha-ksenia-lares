"""The Ksenia Lares Alarm integration."""
import asyncio

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .base import LaresBase
from .coordinator import LaresDataUpdateCoordinator
from .const import DOMAIN, DATA_COORDINATOR, DATA_UPDATE_LISTENER

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.ALARM_CONTROL_PANEL]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Ksenia Lares Alarm from a config entry."""

    client = LaresBase(entry.data)
    coordinator = LaresDataUpdateCoordinator(hass, client)

    # Preload device info
    await client.device_info()

    unsub_options_update_listener = entry.add_update_listener(options_update_listener)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_UPDATE_LISTENER: unsub_options_update_listener,
    }

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    return True


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *(
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            )
        )
    )

    if unload_ok:
        hass.data[DOMAIN][entry.entry_id][DATA_UPDATE_LISTENER]()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""

    if config_entry.version == 1:
        new = {**config_entry.data}
        new["port"] = 4202

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    return True
