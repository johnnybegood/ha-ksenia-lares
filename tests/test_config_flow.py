"""Exercise the real HA flow manager, not isolated flow methods."""
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.ksenia_lares.const import DOMAIN


async def test_options_open_without_exposing_pin(hass, entry, panel):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    defaults = result["data_schema"]({})
    assert defaults["scenario_away"] == "Away"
    assert defaults["partition_away"] == ["Test partition"]
    assert "pin" not in defaults
    assert entry.options["pin"] == "739182"


async def test_options_save(hass, entry, panel):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    submitted = dict(entry.options, scenario_away="Home")
    result = await hass.config_entries.options.async_configure(result["flow_id"], submitted)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options == submitted


async def test_user_setup(hass, panel):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    data = {"host": "panel.invalid", "port": 4202, "username": "test", "password": "test"}
    with patch("custom_components.ksenia_lares.async_setup_entry", new=AsyncMock(return_value=True)):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
        await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == data
    assert result["result"].unique_id == "test-panel"


@pytest.mark.parametrize(("response", "error"), [(None, "invalid_auth"), (RuntimeError("synthetic failure"), "unknown")])
async def test_user_failure(hass, panel, response, error):
    if isinstance(response, Exception):
        panel.info.side_effect = response
    else:
        panel.info.return_value = response
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": "panel.invalid", "port": 4202, "username": "test", "password": "test"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": error}
