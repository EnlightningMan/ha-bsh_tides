"""Client for the BSH water level forecast OGC API (gdi.bsh.de).

In May 2026 the BSH retired the old, undocumented JSON endpoint at
``wasserstand-nordsee.bsh.de/data/*.json`` and replaced it with an official,
documented OGC API Features service (ldproxy) under ``gdi.bsh.de``. The data is
provided free of charge under CC BY 4.0.

This module talks to the new API and translates each station Feature back into
the flat dict structure that the coordinator/sensors already expect, so the
rest of the integration stays unchanged.

Station "ids" are slugs (e.g. ``norderney_riffgat``). For historical reasons
the slug is still stored under the config key ``bshnr``.
"""

import logging

import aiohttp

from .exceptions import BshApiError, BshCannotConnect, BshInvalidStation

_LOGGER = logging.getLogger(__name__)

API_BASE = (
    "https://gdi.bsh.de/ldproxy/rest/services/WaterLevelForecast"
    "/collections/waterlevelforecastdata/items"
)
# Page size for the station list. The service currently lists ~135 stations;
# we still follow "next" links below to stay correct if that grows.
_LIST_LIMIT = 1000
_MAX_PAGES = 20


def _num(value):
    """Parse a BSH numeric field (often a string like "594") into a number."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


def feature_to_legacy(feature: dict) -> dict:
    """Translate a WaterLevelForecast Feature into the legacy data dict.

    Keys consumed downstream: station_name, seo_id, area, creation_forecast,
    MHW, MNW, copyright_note, and either hwnw_forecast{data[]} (peak forecast)
    or curve_forecast{data[]} (curve fallback).
    """
    if not isinstance(feature, dict) or "properties" not in feature:
        raise BshInvalidStation(f"Unexpected feature payload: {feature!r}")

    props = feature["properties"]

    copyright_note = "© BSH – Bundesamt für Seeschifffahrt und Hydrographie"
    cr = props.get("copyright")
    if isinstance(cr, dict):
        copyright_note = cr.get("de") or cr.get("en") or copyright_note
    elif isinstance(cr, str):
        copyright_note = cr

    data: dict = {
        "station_name": props.get("gauge_label"),
        "seo_id": feature.get("id"),
        "area": props.get("area"),
        "creation_forecast": (
            props.get("forecast_timestamp")
            or props.get("automated_curveforecast_timestamp")
        ),
        "MHW": _num(props.get("mean_high_water")),
        "MNW": _num(props.get("mean_low_water")),
        "copyright_note": copyright_note,
    }

    # Primary path: explicit high/low water peak predictions.
    hwnw = props.get("high_water_low_water")
    if isinstance(hwnw, list) and hwnw:
        forecast = []
        for ev in hwnw:
            value = ev.get("forecast_value")
            if value is None:
                value = ev.get("tidal_prediction_value")
            forecast.append(
                {
                    "timestamp": ev.get("event_timestamp"),
                    "event": ev.get("event"),  # "HW" / "NW"
                    "value": _num(value),
                    # kept as the original "-0,3 m" string; the coordinator
                    # parses it via parse_forecast_value().
                    "forecast": ev.get("forecast_deviation"),
                }
            )
        data["hwnw_forecast"] = {"data": forecast}
    else:
        # Fallback: derive extrema from the model curve. The coordinator's
        # _find_curve_extrema() expects items with "timestamp" + "curveforecast".
        curve = props.get("curve")
        curve_data = []
        if isinstance(curve, list):
            for point in curve:
                curve_data.append(
                    {
                        "timestamp": point.get("timestamp"),
                        "curveforecast": _num(point.get("automated_curve_forecast")),
                    }
                )
        data["curve_forecast"] = {"data": curve_data}

    return data


class BshApi:
    """Class for interacting with the BSH water level forecast API."""

    def __init__(self, station_id: str):
        # Historically called bshnr; now holds the station slug.
        self.bshnr = station_id
        self.station_id = station_id
        self.api_url = f"{API_BASE}/{station_id}?f=json"

    async def async_fetch_data(self) -> dict:
        """Fetch and normalise tide data for a single station."""
        try:
            async with aiohttp.ClientSession() as session:
                # ssl=False kept on purpose: BSH has historically served a
                # certificate chain that fails to validate inside HAOS/Docker.
                async with session.get(self.api_url, ssl=False) as response:
                    response.raise_for_status()
                    feature = await response.json(content_type=None)
        except aiohttp.ClientError as e:
            _LOGGER.debug("aiohttp.ClientError: %s", e)
            raise BshCannotConnect("Could not connect to BSH API") from e
        except ValueError as e:
            _LOGGER.debug("Invalid JSON in station data: %s", e)
            raise BshApiError("Invalid JSON in response") from e

        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise BshInvalidStation(f"Invalid station data: {feature}")

        return feature_to_legacy(feature)

    @staticmethod
    async def fetch_station_list() -> list[tuple[str, str, str]]:
        """Fetch all stations as (slug, station_name, area) for the config flow."""
        # Only request the properties we need for the dropdown to keep the
        # payload small (ldproxy honours `properties`; ignored gracefully if not).
        url = f"{API_BASE}?f=json&limit={_LIST_LIMIT}"
        stations: list[tuple[str, str, str]] = []
        try:
            async with aiohttp.ClientSession() as session:
                for _ in range(_MAX_PAGES):
                    async with session.get(url, ssl=False) as response:
                        response.raise_for_status()
                        payload = await response.json(content_type=None)

                    features = payload.get("features")
                    if not isinstance(features, list):
                        raise BshInvalidStation("Missing 'features' in station list")

                    for feat in features:
                        props = feat.get("properties", {}) or {}
                        slug = feat.get("id")
                        name = props.get("gauge_label")
                        area = props.get("area")
                        if slug and name and area:
                            stations.append((slug, name, area))

                    # Follow OGC API "next" link if the result was paginated.
                    next_url = None
                    for link in payload.get("links", []) or []:
                        if link.get("rel") == "next" and link.get("href"):
                            next_url = link["href"]
                            break
                    if not next_url:
                        break
                    url = next_url
        except aiohttp.ClientError as e:
            _LOGGER.debug("aiohttp.ClientError while fetching station list: %s", e)
            raise BshCannotConnect("Could not connect to BSH station list API") from e
        except (ValueError, KeyError) as e:
            _LOGGER.debug("Invalid station list data: %s", e)
            raise BshApiError("Invalid data in station list response") from e

        if not stations:
            raise BshInvalidStation("Empty station list")
        return stations
