"""Home Assistant fixtures; all panel I/O is mocked."""
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ksenia_lares.base import LaresBase
from custom_components.ksenia_lares.const import DOMAIN


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Allow HA to discover the repository's integration."""


@pytest.fixture
def panel():
    """Synthetic data, not a claim of model-specific protocol compatibility."""
    client = AsyncMock(spec=LaresBase)
    client.info.return_value = {"name": "Test Lares", "id": "test-panel"}
    client.device_info.return_value = {
        "identifiers": {(DOMAIN, "test-panel")},
        "name": "Test Lares",
        "manufacturer": "KSENIA",
    }
    client.zone_descriptions.return_value = ["Test zone"]
    client.partition_descriptions.return_value = ["Test partition"]
    client.scenario_descriptions.return_value = ["Disarm", "Away", "Home"]
    client.zones.return_value = [{"status": "NORMAL", "bypass": "UN_BYPASS"}]
    client.partitions.return_value = [{"status": "DISARMED"}]
    client.output_descriptions.return_value = ["Test output"]
    client.outputs.return_value = [
        {"status": "OFF", "type": "DIGITAL", "value": "0", "noPin": False, "remoteControl": True}
    ]
    with (
        patch("custom_components.ksenia_lares.LaresBase", return_value=client),
        patch("custom_components.ksenia_lares.config_flow.LaresBase", return_value=client),
    ):
        yield client


@pytest.fixture
def entry(hass):
    config_entry = MockConfigEntry(
        domain=DOMAIN, version=2, title="Test Lares", unique_id="test-panel",
        data={"host": "panel.invalid", "port": 4202, "username": "test", "password": "test"},
        options={
            "pin": "739182",
            "scenario_disarm": "Disarm",
            "scenario_away": "Away",
            "partition_away": ["Test partition"],
            "scenario_home": "", "partition_home": [],
            "scenario_night": "", "partition_night": [],
        },
    )
    config_entry.add_to_hass(hass)
    return config_entry
