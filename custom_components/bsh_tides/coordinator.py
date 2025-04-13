"""Coordinator for BSH Tides for Germany."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .bsh_api import BshApi

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=60)


class BshTidesCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, bshnr: str):
        self.api = BshApi(bshnr)
        self.bshnr = bshnr

        super().__init__(
            hass,
            _LOGGER,
            name=f"BSH Tides ({bshnr})",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        try:
            return await self.api.async_fetch_data()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")

    @property
    def station_name(self) -> str:
        """Returns the name of the station, eg. 'Hamburg, St. Pauli, Elbe'."""
        return self.data.get("station_name", self.bshnr)

    @property
    def seo_id(self) -> str:
        """Returns a short SEO form of the station name, eg. 'hamburg_st-pauli'."""
        return self.data.get("seo_id", self.bshnr)

    @property
    def forecast_data(self) -> list[dict]:
        """Accessor shortcut to the forecast data."""
        return self.data.get("hwnw_forecast", {}).get("data", [])
