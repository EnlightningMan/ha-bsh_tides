"""Coordinator for BSH Tides for Germany."""

from datetime import timedelta
import logging

import dateutil.parser

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .bsh_api import BshApi
from .const import TideEvent
from .exceptions import BshApiError

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=60)


class BshTidesCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, bshnr: str):
        self.api = BshApi(bshnr)
        self.bshnr = bshnr
        self._parsed_forecast_data = None

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
            self._parse_forecast_data(data)
            return data
        except BshApiError as err:
            _LOGGER.warning("BSH API error while updating data: %s", err)
            raise UpdateFailed(f"BSH API error: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during update: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

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
        """Return the pre-parsed forecast data."""
        return self._parsed_forecast_data

    def _parse_forecast_data(self, data: dict):
        """Parse the data from the API once for usage.

        The hwnw data contains actual forecast for the next high and low tide including expected value, deviation from mean,
        and a code for the event (HW / NW)
        Note: The hwnw data is not avaialble for all stations.
        Those who do not have it, need to use curve_forecast instead.
        """
        if "hwnw_forecast" in data:
            forecast = data.get("hwnw_forecast", {}).get("data", [])
            for item in forecast:
                item["forecast"] = self.parse_forecast_value(item["forecast"])
            self._parsed_forecast_data = forecast
        else:
            _LOGGER.warning(
                "No hwnw_forecast data available for station %s, using curve_forecast instead",
                self.bshnr,
            )
            self._parsed_forecast_data = self._find_curve_extrema(data)

    def parse_forecast_value(self, forecast: str) -> float | None:
        """Parse a forecast string (e.g. "+/-0,0 m", "-0,1 m", "+0,2 m") into a float value."""

        if isinstance(forecast, (int, float)):
            return forecast
        try:
            return round(
                float(
                    forecast.replace(",", ".")
                    .replace("+/-", "")
                    .replace("+", "")
                    .replace(" m", "")
                )
                * 100.0
            )
        except Exception as e:
            _LOGGER.debug("Failed to parse forecast value: %s", e)
            return None

    def _find_curve_extrema(self, data: list[dict]) -> list[dict]:
        """Find significant local minima (NW) and maxima (HW) in curve_forecast.

        We only consider extrema that are at least 45 minutes apart to avoid noise.
        The returned list contains dictionaries with the following keys:
        - "timestamp": The timestamp of the extremum.
        - "value": The value of the extremum.
        - "event": The type of event (TideEvent.HIGH or TideEvent.LOW).
        - "forecast": The forecast value for the extremum, relative diff to MHW or MNW.

        It returns the same data format as hwnw_forecast.
        """
        extrema = []
        min_gap = timedelta(minutes=45)
        last_extremum_time = None
        last_extremum_value = None
        last_extremum_event = None
        curve = data.get("curve_forecast", {}).get("data", [])

        for i in range(1, len(curve) - 1):
            prev = curve[i - 1]
            curr = curve[i]
            nxt = curve[i + 1]

            # curveforecast will only be set for future values, which is what we are looking for anyway.
            val = curr.get("curveforecast") or None
            prev_val = prev.get("curveforecast") or None
            next_val = nxt.get("curveforecast") or None

            if val is None or prev_val is None or next_val is None:
                continue

            is_max = prev_val < val >= next_val
            is_min = prev_val > val <= next_val

            if not (is_max or is_min):
                continue

            ts = dateutil.parser.parse(curr["timestamp"])

            is_in_fluctuation_period = last_extremum_time and abs(ts - last_extremum_time) < min_gap

            if is_in_fluctuation_period:
                # in the fluctuation_period, we check if we move further into the same direction (this skips small fluctuations in the other direction)
                # we select the new reading, iff it is a stronger extremum in the same direction
                if last_extremum_event == TideEvent.HIGH.value and val < last_extremum_value:
                    continue
                if last_extremum_event == TideEvent.LOW.value and val > last_extremum_value:
                    continue 

            if is_max:
                event = TideEvent.HIGH.value
                forecast = val - data.get("MHW", {})
            else:
                event = TideEvent.LOW.value
                forecast = val - data.get("MNW", {})

            new_event = (
                {
                    "timestamp": curr["timestamp"],
                    "value": val,
                    "event": event,
                    "forecast": forecast,
                }
            )

            if is_in_fluctuation_period:
                extrema[-1] = new_event
            else:
                extrema.append(new_event)

            last_extremum_time = ts
            last_extremum_value = val
            last_extremum_event = event

        return extrema
