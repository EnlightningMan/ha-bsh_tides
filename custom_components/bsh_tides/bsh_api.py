import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class BshApi:
    """Class for interacting with the BSH Tides API."""

    # Contains the list of available stations
    MAP_URL = "https://wasserstand-nordsee.bsh.de/data/map.json"

    def __init__(self, bshnr: str):
        self.bshnr = bshnr
        self.api_url = f"https://wasserstand-nordsee.bsh.de/data/DE__{bshnr}.json"

    async def async_fetch_data(self):
        """Asynchronously fetch tide data from the BSH API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url) as response:
                    response.raise_for_status()  # Raise an error for bad status codes
                    return await response.json()
        except aiohttp.ClientError as e:
            _LOGGER.error("Error fetching BSH tide data: %s", e)
            raise Exception(f"Error fetching BSH tide data: {e}")

    @staticmethod
    async def fetch_station_list() -> list[tuple[str, str, str]]:
        """Fetch all available stations with (bshnr, station_name, area) for config_flow."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(BshApi.MAP_URL) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return [
                        (entry["bshnr"], entry["station_name"], entry["area"])
                        for entry in data["gauges"]
                    ]
        except Exception as e:
            _LOGGER.error("Error fetching station list from BSH: %s", e)
            return []
