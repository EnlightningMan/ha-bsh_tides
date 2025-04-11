"""Sensor platform for BSH Tides for Germany."""

from datetime import UTC, datetime, timedelta
import logging

import dateutil.parser

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    # SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import UpdateFailed

from .__init__ import BshTidesConfigEntry
from .bsh_api import BshApi

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)  # Daten alle 1 Stunde aktualisieren


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BshTidesConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the sensor platform for BSH Tides."""

    # Get Api Object for bshnr configured in entity
    api = entry.runtime_data["api"]

    # Create the BshTideSensor entity and add it to Home Assistant
    async_add_entities([BshTidesSensor(api)], update_before_add=True)


class BshTidesSensor(SensorEntity):
    """Representation of a BSH Tides Sensor."""

    _attr_should_poll = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    # _attr_friendly_name will be initialized to the "title" set in config_flow.py
    _attr_icon = "mdi:wave"
    _attr_unit_of_measurement = "cm"
    # _attr_translation_key = "bsh_tides"
    _attr_entity_registry_enabled_default = True
    _attr_entity_registry_visible_default = True

    # TODO attribution, friendly_name, icon, unit_of_measurement
    # _attr_friendly_name = "BSH Tides"
    # _attr_icon = "mdi:water"
    # _attr_unit_of_measurement = "cm"
    # _attr_translation_key = "bsh_tides"
    # _attr_entity_registry_enabled_default = True
    # _attr_entity_registry_visible_default = True
    # _attr_entity_category = EntityCategory.DIAGNOSTIC
    # _attr_extra_state_attributes = {
    #     "bshnr": self._api.bshnr,
    #     "last_updated": self._state,
    # }

    def __init__(self, api: BshApi) -> None:
        """Initialize the sensor."""
        self._api = api
        self._name = f"BSH Tides for {api.bshnr}"
        self._state = None
        self._attr_unique_id = api.bshnr

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    async def async_update(self):
        """Fetch new state data for the sensor."""
        # TODO
        _LOGGER.debug("async_update called")
        try:
            # API Aufruf, um Gezeitendaten zu holen
            # Example JSON: https://wasserstand-nordsee.bsh.de/data/DE__714P.json
            data = await self._api.async_fetch_data()
            # Aktuelles Datum und Uhrzeit
            now = datetime.now(UTC)

            next_tide = None
            next_high = None
            next_low = None

            for item in data["hwnw_forecast"]["data"]:
                timestamp = dateutil.parser.parse(item["timestamp"])
                if timestamp > now:
                    if not next_tide:
                        next_tide = item
                    if item["event"] == "HW" and not next_high:
                        next_high = item
                    if item["event"] == "NW" and not next_low:
                        next_low = item
                    if next_high and next_low:
                        break

            if next_tide:
                self._attr_extra_state_attributes = {
                    "bshnr": self._api.bshnr,
                    "station_url": data["station_url"],
                    "station_name": data["station_name"],
                    "station_area": data["area"],
                    "mean_high_water": data["MHW"],
                    "mean_low_water": data["MNW"],
                    "forecasted_at": data["creation_forecast"],
                    "next_tide_timestamp": next_tide["timestamp"],
                    "next_tide_event": next_tide["event"],
                    "next_tide_water_level": next_tide["value"],
                    "next_tide_diff_to_mean": next_tide["forecast"],
                    "next_high_tide_timestamp": next_high["timestamp"],
                    "next_high_tide_event": next_high["event"],
                    "next_high_tide_water_level": next_high["value"],
                    "next_high_tide_diff_to_mean": next_high["forecast"],
                    "next_low_tide_timestamp": next_low["timestamp"],
                    "next_low_tide_event": next_low["event"],
                    "next_low_tide_water_level": next_low["value"],
                    "next_low_tide_diff_to_mean": next_low["forecast"],
                }

                self._state = next_tide["timestamp"]
                self._attr_attribution = data.get(
                    "copyright_note",
                    "© BSH – Bundesamt für Seeschifffahrt und Hydrographie",
                )
            else:
                _LOGGER.error(
                    f"No upcoming tide events found for bshnr {self._api.bshnr}."
                )
                raise UpdateFailed(
                    f("No upcoming tide events found for bshnr %s.", self._api.bshnr)
                )
        except Exception as e:
            _LOGGER.error(f"Error while fetching tide data: {e}")
            raise UpdateFailed(f"Error fetching tide data: {e}")
