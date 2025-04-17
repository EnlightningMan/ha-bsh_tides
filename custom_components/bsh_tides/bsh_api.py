import aiohttp
import logging

from .exceptions import BshApiError, BshCannotConnect, BshInvalidStation

_LOGGER = logging.getLogger(__name__)


class BshApi:
    """Class for interacting with the BSH Tides API."""

    # Contains the list of available stations
    MAP_URL = "https://wasserstand-nordsee.bsh.de/data/map.json"

    def __init__(self, bshnr: str):
        self.bshnr = bshnr
        self.api_url = f"https://wasserstand-nordsee.bsh.de/data/DE__{bshnr}.json"

    async def async_fetch_data(self):
        """Fetch tide data for a given station."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, ssl=False) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if "station_name" not in data or "gauges" in data:
                        raise BshInvalidStation(f"Invalid station data: {data}")
                    return data
        except aiohttp.ClientError as e:
            _LOGGER.debug("aiohttp.ClientError: %s", e)
            raise BshCannotConnect("Could not connect to BSH API") from e
        except ValueError as e:
            _LOGGER.debug("Invalid JSON in station data: %s", e)
            raise BshApiError("Invalid JSON in response") from e

    @staticmethod
    async def fetch_station_list() -> list[tuple[str, str, str]]:
        """Fetch all available stations with (bshnr, station_name, area) for config_flow."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(BshApi.MAP_URL, ssl=False) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if "gauges" not in data:
                        raise BshInvalidStation("Missing 'gauges' in station list")
                    return [
                        (entry["bshnr"], entry["station_name"], entry["area"])
                        for entry in data["gauges"]
                    ]
        except aiohttp.ClientError as e:
            _LOGGER.debug("aiohttp.ClientError while fetching station list: %s", e)
            raise BshCannotConnect("Could not connect to BSH station list API") from e
        except (ValueError, KeyError) as e:
            _LOGGER.debug("Invalid station list data: %s", e)
            raise BshApiError("Invalid data in station list response") from e
