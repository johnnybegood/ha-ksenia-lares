"""Base component for Lares"""
import asyncio
import logging
import re

import aiohttp
from aiohttp.http import RESPONSES
from getmac import get_mac_address
from lxml import etree

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, format_mac

from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


class LaresBase:
    """The implementation of the Lares base class."""

    def __init__(self, data: dict):
        username = data["username"]
        password = data["password"]
        host = data["host"]

        self._auth = aiohttp.BasicAuth(username, password)
        self._ip = host
        self._port = 4202
        self._host = f"http://{host}:{self._port}"

    async def info(self):
        """Get general info"""
        response = await self.get("info/generalInfo.xml")

        if response is None:
            return None

        mac = get_mac_address(ip=self._ip)
        unique_id = str(mac)

        if mac is None:
            # Fallback to IP addresses when MAC cannot be determined
            unique_id = f"{self._ip}:{self._port}"

        info = {
            "mac": mac,
            "id": unique_id,
            "name": response.xpath("/generalInfo/productName")[0].text,
            "info": response.xpath("/generalInfo/info1")[0].text,
            "version": response.xpath("/generalInfo/productHighRevision")[0].text,
            "revision": response.xpath("/generalInfo/productLowRevision")[0].text,
            "build": response.xpath("/generalInfo/productBuildRevision")[0].text,
        }

        return info

    async def device_info(self):
        """Get device info"""
        device_info = await self.info()

        if device_info is None:
            return None

        info = {
            "identifiers": {(DOMAIN, device_info["id"])},
            "name": device_info["name"],
            "manufacturer": MANUFACTURER,
            "model": device_info["name"],
            "sw_version": f'{device_info["version"]}.{device_info["revision"]}.{device_info["build"]}',
        }

        mac = device_info["mac"]

        if mac is not None:
            info["connections"] = {(CONNECTION_NETWORK_MAC, format_mac(mac))}

        return info

    async def zoneDescriptions(self):
        """Get available zones"""
        response = await self.get("zones/zonesDescription48IP.xml")

        if response is None:
            return None

        zones = response.xpath("/zonesDescription/zone")

        return [zone.text for zone in zones]

    async def zones(self):
        """Get available zones"""
        response = await self.get("zones/zonesStatus48IP.xml")

        if response is None:
            return None

        zones = response.xpath("/zonesStatus/zone")

        return [
            {
                "status": zone.find("status").text,
                "bypass": zone.find("bypass").text,
                "alarm": zone.find("alarm").text,
            }
            for zone in zones
        ]

    async def get(self, path):
        """Generic send method."""
        url = f"{self._host}/xml/{path}"

        try:
            async with aiohttp.ClientSession(auth=self._auth) as session:
                async with session.get(url=url) as response:
                    xml = await response.read()
                    content = etree.fromstring(xml)
                    return content

        except aiohttp.ClientConnectorError as conn_err:
            _LOGGER.debug("Host %s: Connection error %s", self._host, str(conn_err))
        except:  # pylint: disable=bare-except
            _LOGGER.debug("Host %s: Unknown exception occurred.", self._host)
        return
