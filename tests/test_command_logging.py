"""PINs reach the panel but never the integration's command log."""
import logging
from unittest.mock import AsyncMock

from lxml import etree
import pytest

from custom_components.ksenia_lares.base import LaresBase


@pytest.mark.parametrize("status", ["cmdSent", "cmdError"])
@pytest.mark.parametrize(
    ("method", "arguments", "command", "parameters"),
    [
        ("activate_scenario", (2,), "setMacro", "&macroId=2"),
        ("bypass_zone", (0, True), "setByPassZone", "&zoneId=1&zoneValue=1"),
        ("bypass_zone", (0, False), "setByPassZone", "&zoneId=1&zoneValue=0"),
    ],
)
async def test_pin_not_logged(caplog, status, method, arguments, command, parameters):
    client = LaresBase({"host": "panel.invalid", "port": 4202, "username": "test", "password": "test"})
    pin = "739182"  # Synthetic credential.
    client.get = AsyncMock(return_value=etree.fromstring(f"<cmd>{status}</cmd>"))
    args = (arguments[0], pin, *arguments[1:])
    with caplog.at_level(logging.DEBUG, logger="custom_components.ksenia_lares.base"):
        result = await getattr(client, method)(*args)
    assert result is (status == "cmdSent")
    client.get.assert_awaited_once_with(
        f"cmd/cmdOk.xml?cmd={command}&pin={pin}"
        f"&redirectPage=/xml/cmd/cmdError.xml{parameters}"
    )
    assert f"Sending command {command}" in caplog.text
    assert pin not in caplog.text
    assert "pin=" not in caplog.text
    assert "cmd/cmdOk.xml" not in caplog.text
