"""Load real platforms and check cleanup and options-triggered reload."""
from datetime import timedelta

from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.ksenia_lares.const import DOMAIN, DATA_COORDINATOR


async def test_setup_unload_stops_polling(hass, entry, panel):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert {entity.domain for entity in entities} == {"sensor", "binary_sensor", "switch", "alarm_control_panel"}
    assert len(entities) == 5
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    panel.zones.reset_mock()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15))
    await hass.async_block_till_done()
    assert panel.zones.await_count > 0
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.entry_id not in hass.data[DOMAIN]
    assert not coordinator._listeners
    panel.zones.reset_mock()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=60))
    await hass.async_block_till_done()
    panel.zones.assert_not_awaited()
    assert all(hass.states.get(entity.entity_id).state == "unavailable" for entity in entities)


async def test_options_reload_without_duplicate_entities(hass, entry, panel):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    old = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    registry = er.async_get(hass)
    before = {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    initial = await hass.config_entries.options.async_init(entry.entry_id)
    submitted = dict(entry.options, scenario_away="Home")
    await hass.config_entries.options.async_configure(initial["flow_id"], submitted)
    await hass.async_block_till_done()
    new = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    assert new is not old
    assert not old._listeners
    assert entry.options == submitted
    after = {e.entity_id for e in er.async_entries_for_config_entry(registry, entry.entry_id)}
    assert before == after
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
