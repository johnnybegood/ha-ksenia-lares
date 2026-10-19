"""Output switches: optional metadata, availability and command failures."""
import asyncio
from datetime import timedelta
from unittest.mock import patch

from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed
import pytest

from custom_components.ksenia_lares.const import DOMAIN, DATA_COORDINATOR

PIN = "739182"  # Synthetic credential, matches the entry fixture.
OUTPUT = {"status": "OFF", "type": "DIGITAL", "value": "0", "noPin": False, "remoteControl": True}


async def _setup(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _poll(hass):
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15))
    await hass.async_block_till_done()


def _entity_id(hass, domain, unique_id):
    return er.async_get(hass).async_get_entity_id(domain, DOMAIN, unique_id)


def _state(hass, domain, unique_id):
    return hass.states.get(_entity_id(hass, domain, unique_id))


async def _switch(hass, service, unique_id="lares_output_0"):
    await hass.services.async_call(
        "switch", service, {"entity_id": _entity_id(hass, "switch", unique_id)}, blocking=True
    )


@pytest.mark.parametrize(("descriptions", "names"), [
    (None, ["Output 1", "Output 2"]),
    (["Gate"], ["Gate", "Output 2"]),
])
async def test_missing_output_descriptions_keep_bypass(hass, entry, panel, descriptions, names):
    panel.output_descriptions.return_value = descriptions
    panel.outputs.return_value = [OUTPUT, dict(OUTPUT, status="ON")]
    await _setup(hass, entry)
    assert _state(hass, "switch", "lares_bypass_0").state == "off"
    registry = er.async_get(hass)
    for idx, name in enumerate(names):
        entity_id = _entity_id(hass, "switch", f"lares_output_{idx}")
        assert registry.async_get(entity_id).original_name == name
        assert hass.states.get(entity_id).state == ("on" if idx else "off")


async def test_output_unavailable_when_update_fails(hass, entry, panel):
    await _setup(hass, entry)
    assert _state(hass, "switch", "lares_output_0").state == "off"
    panel.zones.side_effect = TimeoutError
    await _poll(hass)
    assert _state(hass, "switch", "lares_output_0").state == "unavailable"


async def _never_answer():
    await asyncio.Event().wait()


@pytest.mark.parametrize("failure", [
    {"return_value": None},
    {"return_value": []},
    {"side_effect": AttributeError("'NoneType' object has no attribute 'text'")},
    {"side_effect": _never_answer},
], ids=["missing", "short", "malformed", "slow"])
async def test_output_failure_does_not_block_zones(hass, entry, panel, failure):
    await _setup(hass, entry)
    assert _state(hass, "binary_sensor", "lares_zones_0").state == "off"
    panel.zones.return_value = [{"status": "ALARM", "bypass": "UN_BYPASS"}]
    for attribute, value in failure.items():
        setattr(panel.outputs, attribute, value)
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    with patch("custom_components.ksenia_lares.coordinator.DEFAULT_TIMEOUT", 0.01):
        await coordinator.async_refresh()  # Awaited, unlike the background poll.
    await hass.async_block_till_done()
    assert _state(hass, "binary_sensor", "lares_zones_0").state == "on"
    assert _state(hass, "switch", "lares_output_0").state == "unavailable"


@pytest.mark.parametrize(("service", "turn_on"), [("turn_on", True), ("turn_off", False)])
async def test_output_command_success(hass, entry, panel, service, turn_on):
    panel.set_output.return_value = True
    await _setup(hass, entry)
    await _switch(hass, service)
    panel.set_output.assert_awaited_once_with(0, PIN, turn_on)


@pytest.mark.parametrize("service", ["turn_on", "turn_off"])
async def test_output_command_rejected(hass, entry, panel, service):
    panel.set_output.return_value = False
    await _setup(hass, entry)
    with pytest.raises(HomeAssistantError) as err:
        await _switch(hass, service)
    assert not isinstance(err.value, ServiceValidationError)
    assert PIN not in str(err.value)


@pytest.mark.parametrize("service", ["turn_on", "turn_off"])
async def test_output_command_requires_pin(hass, entry, panel, service):
    options = {key: value for key, value in entry.options.items() if key != "pin"}
    hass.config_entries.async_update_entry(entry, options=options)
    await _setup(hass, entry)
    with pytest.raises(ServiceValidationError):
        await _switch(hass, service)
    panel.set_output.assert_not_awaited()
