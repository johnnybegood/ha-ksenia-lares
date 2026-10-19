"""The host field accepts a bare address or a full URL (e.g. HTTPS reverse proxy)."""
from unittest.mock import AsyncMock, MagicMock, patch

from lxml import etree
import pytest

from custom_components.ksenia_lares.base import LaresBase

GENERAL_INFO = (
    "<generalInfo><productName>Lares 4.0 48IP</productName><info1>test</info1>"
    "<productHighRevision>1</productHighRevision><productLowRevision>2</productLowRevision>"
    "<productBuildRevision>3</productBuildRevision></generalInfo>"
)
CASES = [
    ("192.0.2.10", "http://192.0.2.10:4202", "192.0.2.10", 4202),
    ("http://192.0.2.10:8080", "http://192.0.2.10:8080", "192.0.2.10", 8080),
    ("https://lares.example.com", "https://lares.example.com", "lares.example.com", 4202),
    ("https://lares.example.com:8443", "https://lares.example.com:8443", "lares.example.com", 8443),
]


def _client(host):
    return LaresBase({"host": host, "port": 4202, "username": "test", "password": "test"})


@pytest.mark.parametrize(("host", "base_url", "ip", "port"), CASES)
async def test_request_url(host, base_url, ip, port):
    session = MagicMock()
    session.get.return_value.__aenter__.return_value.read = AsyncMock(return_value=b"<cmd/>")
    with patch("custom_components.ksenia_lares.base.aiohttp.ClientSession") as session_class:
        session_class.return_value.__aenter__.return_value = session
        assert (await _client(host).get("info/generalInfo.xml")).tag == "cmd"
    session.get.assert_called_once_with(url=f"{base_url}/xml/info/generalInfo.xml")


@pytest.mark.parametrize(("host", "base_url", "ip", "port"), CASES)
async def test_device_identity(host, base_url, ip, port):
    client = _client(host)
    client.get = AsyncMock(return_value=etree.fromstring(GENERAL_INFO))
    with patch("custom_components.ksenia_lares.base.get_mac_address", return_value=None) as get_mac:
        info = await client.device_info()
    get_mac.assert_called_with(ip=ip)
    assert info["identifiers"] == {("ksenia_lares", f"{ip}:{port}")}
    assert info["configuration_url"] == base_url
