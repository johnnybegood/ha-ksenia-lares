"""The Ksenia Lares data update coordinator."""
from datetime import timedelta
import logging
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base import LaresBase
from .const import DEFAULT_TIMEOUT, DATA_PARTITIONS, DATA_ZONES, DATA_OUTPUTS, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class LaresDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinate for data updates from Ksenia Lares."""

    def __init__(self, hass: HomeAssistant, client: LaresBase, scan_interval: int = DEFAULT_SCAN_INTERVAL) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ksenia Lares",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch data from Ksenia Lares client."""
        async with async_timeout.timeout(DEFAULT_TIMEOUT):
            zones = await self.client.zones()
            partitions = await self.client.partitions()

        return {
            DATA_ZONES: zones,
            DATA_PARTITIONS: partitions,
            DATA_OUTPUTS: await self._async_fetch_outputs(),
        }

    async def _async_fetch_outputs(self) -> list | None:
        """Fetch outputs separately, so a failure cannot block alarm updates.

        Returns None when outputs are slow or malformed; the output switches
        then become unavailable while zones and partitions keep updating.
        """
        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                return await self.client.outputs()
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug("Failed to update outputs: %s", type(err).__name__)
            return None
