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
        _LOGGER.debug("Initialized BshTidesCoordinator for bshnr %s", bshnr)

    async def _async_update_data(self):
        try:
            data = await self.api.async_fetch_data()
            _LOGGER.debug(
                "Fetched data for %s: station=%s, creation_forecast=%s",
                self.bshnr,
                data.get("station_name"),
                data.get("creation_forecast"),
            )
            return data
        except Exception as err:
            _LOGGER.error("Error updating data for %s: %s", self.bshnr, err)
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
