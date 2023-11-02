"""Base component for Lares"""
import logging
from typing import Any

import aiohttp
from getmac import get_mac_address
from lxml import etree
from lxml.etree import Element

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, format_mac

from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


class LaresBase:
    """The implementation of the Lares base class."""

    def __init__(self, data: dict) -> None:
        username = data["username"]
        password = data["password"]
        host = data["host"]
        port = data["port"]

        self._auth = aiohttp.BasicAuth(username, password)
        self._ip = host
        self._port = port
        self._host = f"http://{host}:{self._port}"
        self._model = None
        self._zone_descriptions = None
        self._partition_descriptions = None
        self._scenario_descriptions = None

    async def info(self) -> dict | None:
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

    async def device_info(self) -> dict | None:
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
            "configuration_url": self._host
        }

        mac = device_info["mac"]

        if mac is not None:
            info["connections"] = {(CONNECTION_NETWORK_MAC, format_mac(mac))}

        return info

    async def zone_descriptions(self):
        """Get available zones"""
        model = await self.get_model()
        if self._zone_descriptions is None:
            self._zone_descriptions = await self.get_descriptions(
                f"zones/zonesDescription{model}.xml", "/zonesDescription/zone"
            )

        return self._zone_descriptions

    async def zones(self):
        """Get available zones"""
        model = await self.get_model()
        response = await self.get(f"zones/zonesStatus{model}.xml")

        if response is None:
            return None

        zones = response.xpath("/zonesStatus/zone")

        return [
            {
                "status": zone.find("status").text,
                "bypass": zone.find("bypass").text,
            }
            for zone in zones
        ]

    async def partition_descriptions(self):
        """Get available partitions"""
        model = await self.get_model()

        if self._partition_descriptions is None:
            self._partition_descriptions = await self.get_descriptions(
                f"partitions/partitionsDescription{model}.xml",
                "/partitionsDescription/partition",
            )

        return self._partition_descriptions

    async def partitions(self):
        """Get status of partitions"""
        model = await self.get_model()
        response = await self.get(f"partitions/partitionsStatus{model}.xml")

        if response is None:
            return None

        partitions = response.xpath("/partitionsStatus/partition")

        return [
            {
                "status": partition.text,
            }
            for partition in partitions
        ]

    async def scenarios(self):
        """Get status of scenarios"""
        response = await self.get("scenarios/scenariosOptions.xml")

        if response is None:
            return None

        scenarios = response.xpath("/scenariosOptions/scenario")

        return [
            {
                "id": idx,
                "enabled": scenario.find("abil").text == "TRUE",
                "noPin": scenario.find("nopin").text == "TRUE",
            }
            for idx, scenario in enumerate(scenarios)
        ]

    async def scenario_descriptions(self):
        """Get descriptions of scenarios"""
        if self._scenario_descriptions is None:
            self._scenario_descriptions = await self.get_descriptions(
                "scenarios/scenariosDescription.xml", "/scenariosDescription/scenario"
            )

        return self._scenario_descriptions

    async def activate_scenario(self, scenario: int, code: str) -> bool:
        """Activate the given scenarios, requires the alarm code"""
        params = {
            "macroId": scenario
        }

        return await self.send_command("setMacro", code, params)

    async def bypass_zone(self, zone: int, code: str, bypass: bool) -> bool:
        """Activate the given scenarios, requires the alarm code"""
        params = {
            "zoneId": zone + 1, #Lares uses index starting with 1
            "zoneValue": 1 if bypass else 0
        }

        return await self.send_command("setByPassZone", code, params)

    async def get_descriptions(self, path: str, element: str) -> dict | None:
        """Get descriptions"""
        response = await self.get(path)

        if response is None:
            return None

        content = response.xpath(element)
        return [item.text for item in content]

    async def get_model(self) -> str:
        """Get model information"""
        if self._model is None:
            info = await self.info()
            if info["name"].endswith("128IP"):
                self._model = "128IP"
            elif info["name"].endswith("48IP"):
                self._model = "48IP"
            else:
                self._model = "16IP"

        return self._model

    async def send_command(self, command: str, code: str, params: dict[str, int]) -> bool:
        """Send Command"""
        urlparam = "".join(f'&{k}={v}' for k,v in params.items())
        path = f"cmd/cmdOk.xml?cmd={command}&pin={code}&redirectPage=/xml/cmd/cmdError.xml{urlparam}"

        _LOGGER.debug("Sending command %s", path)

        response = await self.get(path)
        cmd = response.xpath("/cmd")

        if cmd is None or cmd[0].text != "cmdSent":
            _LOGGER.error("Command send failed: %s", response)
            return False

        return True

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
            _LOGGER.debug("Host %s: Unknown exception occurred", self._host)
        return None
