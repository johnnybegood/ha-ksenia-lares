"""Options flow: PIN preservation and the configurable polling interval."""
from datetime import timedelta

from homeassistant.data_entry_flow import FlowResultType, InvalidData
import pytest

from custom_components.ksenia_lares.const import DOMAIN, DATA_COORDINATOR

PIN = "739182"  # Synthetic credential, matches the entry fixture.


async def _save_options(hass, entry, submitted):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    return await hass.config_entries.options.async_configure(result["flow_id"], submitted)


@pytest.mark.parametrize("pin", [None, ""], ids=["omitted", "blank"])
async def test_pin_kept_when_not_supplied(hass, entry, panel, pin):
    submitted = {k: v for k, v in entry.options.items() if k != "pin"}
    submitted["scan_interval"] = 30
    if pin is not None:
        submitted["pin"] = pin
    result = await _save_options(hass, entry, submitted)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options["pin"] == PIN
    assert entry.options["scan_interval"] == 30


async def test_pin_replaced_when_supplied(hass, entry, panel):
    await _save_options(hass, entry, dict(entry.options, pin="246810"))
    assert entry.options["pin"] == "246810"


async def test_no_pin_stays_unset(hass, entry, panel):
    options = {k: v for k, v in entry.options.items() if k != "pin"}
    hass.config_entries.async_update_entry(entry, options=options)
    await _save_options(hass, entry, options)
    assert "pin" not in entry.options


async def test_scan_interval_default_and_reload(hass, entry, panel):
    # Entries created before this option existed keep the 10 s default.
    options = {k: v for k, v in entry.options.items() if k != "scan_interval"}
    hass.config_entries.async_update_entry(entry, options=options)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    assert coordinator.update_interval == timedelta(seconds=10)

    await _save_options(hass, entry, dict(options, scan_interval=45))
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    assert coordinator.update_interval == timedelta(seconds=45)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize("interval", [4, 301])
async def test_scan_interval_out_of_range(hass, entry, panel, interval):
    with pytest.raises(InvalidData):
        await _save_options(hass, entry, dict(entry.options, scan_interval=interval))
    assert entry.options["scan_interval"] == 10
