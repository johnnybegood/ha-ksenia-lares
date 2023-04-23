"""The Ksenia Lares data update coordinator."""
from datetime import timedelta
import logging
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base import LaresBase
from .const import DEFAULT_TIMEOUT, DATA_PARTITIONS, DATA_ZONES

SCAN_INTERVAL = timedelta(seconds=10)
_LOGGER = logging.getLogger(__name__)


class LaresDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinate for data updates from Ksenia Lares."""

    def __init__(self, hass: HomeAssistant, client: LaresBase) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="Ksenia Lares",
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch data from Ksenia Lares client."""
        async with async_timeout.timeout(DEFAULT_TIMEOUT):
            zones = await self.client.zones()
            partitions = await self.client.paritions()

            return {DATA_ZONES: zones, DATA_PARTITIONS: partitions}
