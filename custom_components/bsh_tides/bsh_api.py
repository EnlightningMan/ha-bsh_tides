import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class BshApi:
    """Class for interacting with the BSH Tides API."""

    def __init__(self, bshnr: str):
        self.bshnr = bshnr
        self.api_url = f"https://wasserstand-nordsee.bsh.de/data/{bshnr}.json"

    async def async_fetch_data(self):
        """Asynchronously fetch tide data from the BSH API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url) as response:
                    response.raise_for_status()  # Raise an error for bad status codes
                    return await response.json()
        except aiohttp.ClientError as e:
            # Handle errors (log them or raise an exception)
            _LOGGER.error("Error fetching BSH tide data: %s", e)
            raise Exception(f"Error fetching BSH tide data: {e}")
