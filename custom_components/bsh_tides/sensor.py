"""Sensor platform for BSH Tides for Germany."""

from datetime import UTC, datetime
import logging

import dateutil.parser

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    # SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .__init__ import BshTidesConfigEntry
from .const import DOMAIN
from .coordinator import BshTidesCoordinator

# from .bsh_api import BshApi

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BshTidesConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    bshnr = entry.data["bshnr"]
    coordinator = BshTidesCoordinator(hass, bshnr)

    await coordinator.async_config_entry_first_refresh()

    entities = [
        BshNextTideTimeSensor(coordinator),
        BshNextTideLevelSensor(coordinator),
        BshNextTideDiffSensor(coordinator),
        BshNextHighTideTimeSensor(coordinator),
        BshNextHighTideLevelSensor(coordinator),
        BshNextHighTideDiffSensor(coordinator),
        BshNextLowTideTimeSensor(coordinator),
        BshNextLowTideLevelSensor(coordinator),
        BshNextLowTideDiffSensor(coordinator),
        BshMeanHighWaterLevelSensor(coordinator),
        BshMeanLowWaterLevelSensor(coordinator),
        BshForecastCreatedSensor(coordinator),
        BshStationAreaSensor(coordinator),
        # BshStationUrlSensor(coordinator),
    ]

    async_add_entities(entities)


class BshBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: BshTidesCoordinator):
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.bshnr)},
            "name": f"BSH Station {coordinator.station_name}",
            "manufacturer": "BSH",
            "entry_type": "service",
        }
        self._attr_attribution = coordinator.data.get(
            "copyright_note",
            "© BSH – Bundesamt für Seeschifffahrt und Hydrographie",
        )


class BshNextTideTimeSensor(BshBaseSensor):
    _attr_name = "Next Tide Time"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_next_tide_time"

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if ts > now:
                return ts
        return None


class BshNextTideLevelSensor(BshBaseSensor):
    """Sensor for the next tide level in cm according to live forecast."""

    _attr_name = "Next Tide Level"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = "cm"

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_next_tide_level"

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if ts > now:
                return round(item["value"]) if item["value"] is not None else None
        return None


class BshNextTideDiffSensor(BshBaseSensor):
    """Sensor for relative difference to the mean tide level in m according to live forecast."""

    _attr_name = "Next Tide Diff to Mean"
    _attr_native_unit_of_measurement = "m"

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_next_tide_diff"

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if ts > now:
                try:
                    # cleanup values: "+/-0,0 m", "-0,1 m", "+0,2 m"
                    return float(
                        item["forecast"]
                        .replace(",", ".")
                        .replace("+", "")
                        .replace("+/-", "")
                        .replace(" m", "")
                    )
                except Exception:
                    return None
        return None


class BshNextHighTideTimeSensor(BshBaseSensor):
    _attr_name = "Next High Tide"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_next_high_tide_time"

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "HW" and ts > now:
                return ts
        return None


class BshNextHighTideDiffSensor(BshBaseSensor):
    """Sensor for relative difference to the mean tide level in m according to live forecast."""

    _attr_name = "Next High Tide Diff to Mean"
    _attr_native_unit_of_measurement = "m"

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_next_high_tide_diff"

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "HW" and ts > now:
                try:
                    # cleanup values: "+/-0,0 m", "-0,1 m", "+0,2 m"
                    return float(
                        item["forecast"]
                        .replace(",", ".")
                        .replace("+", "")
                        .replace("+/-", "")
                        .replace(" m", "")
                    )
                except Exception:
                    return None
        return None


class BshNextHighTideLevelSensor(BshBaseSensor):
    """Sensor for the next high tide level in cm according to live forecast."""

    _attr_name = "Next High Tide Level"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = "cm"

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_next_high_tide_level"

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "HW" and ts > now:
                return round(item["value"]) if item["value"] is not None else None
        return None


class BshNextLowTideTimeSensor(BshBaseSensor):
    _attr_name = "Next Low Tide"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_next_low_tide_time"

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "NW" and ts > now:
                return ts
        return None


class BshNextLowTideDiffSensor(BshBaseSensor):
    """Sensor for relative difference to the mean tide level in m according to live forecast."""

    _attr_name = "Next Low Tide Diff to Mean"
    _attr_native_unit_of_measurement = "m"

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_next_low_tide_diff"

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "NW" and ts > now:
                try:
                    # cleanup values: "+/-0,0 m", "-0,1 m", "+0,2 m"
                    return float(
                        item["forecast"]
                        .replace(",", ".")
                        .replace("+", "")
                        .replace("+/-", "")
                        .replace(" m", "")
                    )
                except Exception:
                    return None
        return None


class BshNextLowTideLevelSensor(BshBaseSensor):
    """Sensor for the next low tide level in cm according to live forecast."""

    _attr_name = "Next Low Tide Level"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = "cm"

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_next_low_tide_level"

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "NW" and ts > now:
                return round(item["value"]) if item["value"] is not None else None
        return None


class BshMeanHighWaterLevelSensor(BshBaseSensor):
    """Mean High Water Level in cm for the current station."""

    _attr_name = "Mean High Water Level"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = "cm"

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_mean_high_water_level"

    @property
    def native_value(self):
        value = self.coordinator.data.get("MHW")
        return round(value) if value is not None else None


class BshMeanLowWaterLevelSensor(BshBaseSensor):
    """Mean Low Water Level in cm for the current station."""

    _attr_name = "Mean Low Water Level"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = "cm"

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_mean_low_water_level"

    @property
    def native_value(self):
        value = self.coordinator.data.get("MNW")
        return round(value) if value is not None else None


class BshForecastCreatedSensor(BshBaseSensor):
    """Forecast Created At in UTC for the current station."""

    _attr_name = "Forecast Created At"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_forecast_created_at"

    @property
    def native_value(self):
        val = self.coordinator.data.get("creation_forecast")
        return dateutil.parser.parse(val) if val else None


class BshStationAreaSensor(BshBaseSensor):
    """Contains the area of the station, e.g. Elbe for St. Pauli."""

    _attr_name = "Station Area"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def unique_id(self):
        return f"{self.coordinator.seo_id}_station_area"

    @property
    def native_value(self):
        return self.coordinator.data.get("area")


# class BshStationUrlSensor(BshBaseSensor):
#     """Link to extended data for the station provided by https://www.pegelonline.wsv.de/."""

#     _attr_name = "Station URL"
#     _attr_entity_category = EntityCategory.DIAGNOSTIC

#     @property
#     def unique_id(self):
#         return f"{self.coordinator.seo_id}_station_url"

#     @property
#     def native_value(self):
#         return self.coordinator.data.get("station_url")

# # Get Api Object for bshnr configured in entity
# api = entry.runtime_data["api"]

# # Create the BshTideSensor entity and add it to Home Assistant
# async_add_entities([BshTidesSensor(api)], update_before_add=True)


# class BshTidesSensor(SensorEntity):
#     """Representation of a BSH Tides Sensor."""

#     _attr_should_poll = True
#     _attr_device_class = SensorDeviceClass.TIMESTAMP

#     # _attr_friendly_name will be initialized to the "title" set in config_flow.py
#     _attr_icon = "mdi:wave"
#     _attr_unit_of_measurement = "cm"
#     # _attr_translation_key = "bsh_tides"
#     _attr_entity_registry_enabled_default = True
#     _attr_entity_registry_visible_default = True

#     # TODO attribution, friendly_name, icon, unit_of_measurement
#     # _attr_friendly_name = "BSH Tides"
#     # _attr_icon = "mdi:water"
#     # _attr_unit_of_measurement = "cm"
#     # _attr_translation_key = "bsh_tides"
#     # _attr_entity_registry_enabled_default = True
#     # _attr_entity_registry_visible_default = True
#     # _attr_entity_category = EntityCategory.DIAGNOSTIC
#     # _attr_extra_state_attributes = {
#     #     "bshnr": self._api.bshnr,
#     #     "last_updated": self._state,
#     # }

#     def __init__(self, api: BshApi) -> None:
#         """Initialize the sensor."""
#         self._api = api
#         self._name = f"BSH Tides for {api.bshnr}"
#         self._state = None
#         self._attr_unique_id = api.bshnr

#     @property
#     def name(self):
#         """Return the name of the sensor."""
#         return self._name

#     @property
#     def state(self):
#         """Return the state of the sensor."""
#         return self._state

#     async def async_update(self):
#         """Fetch new state data for the sensor."""
#         # TODO
#         _LOGGER.debug("async_update called")
#         try:
#             # API Aufruf, um Gezeitendaten zu holen
#             # Example JSON: https://wasserstand-nordsee.bsh.de/data/DE__714P.json
#             data = await self._api.async_fetch_data()
#             # Aktuelles Datum und Uhrzeit
#             now = datetime.now(UTC)

#             next_tide = None
#             next_high = None
#             next_low = None

#             for item in data["hwnw_forecast"]["data"]:
#                 timestamp = dateutil.parser.parse(item["timestamp"])
#                 if timestamp > now:
#                     if not next_tide:
#                         next_tide = item
#                     if item["event"] == "HW" and not next_high:
#                         next_high = item
#                     if item["event"] == "NW" and not next_low:
#                         next_low = item
#                     if next_high and next_low:
#                         break

#             if next_tide:
#                 self._attr_extra_state_attributes = {
#                     "bshnr": self._api.bshnr,
# "station_url": data["station_url"],
# "station_name": data["station_name"],
# "station_area": data["area"],
# "mean_high_water": data["MHW"],
# "mean_low_water": data["MNW"],
# "forecasted_at": data["creation_forecast"],
#                     "next_tide_timestamp": next_tide["timestamp"],
#                     "next_tide_event": next_tide["event"],
#                     "next_tide_water_level": next_tide["value"],
#                     "next_tide_diff_to_mean": next_tide["forecast"],
#                     "next_high_tide_timestamp": next_high["timestamp"],
#                     "next_high_tide_event": next_high["event"],
#                     "next_high_tide_water_level": next_high["value"],
#                     "next_high_tide_diff_to_mean": next_high["forecast"],
#                     "next_low_tide_timestamp": next_low["timestamp"],
#                     "next_low_tide_event": next_low["event"],
#                     "next_low_tide_water_level": next_low["value"],
#                     "next_low_tide_diff_to_mean": next_low["forecast"],
#                 }

#                 self._state = next_tide["timestamp"]
#                 self._attr_attribution = data.get(
#                     "copyright_note",
#                     "© BSH – Bundesamt für Seeschifffahrt und Hydrographie",
#                 )
#             else:
#                 _LOGGER.error(
#                     f"No upcoming tide events found for bshnr {self._api.bshnr}."
#                 )
#                 raise UpdateFailed(
#                     f("No upcoming tide events found for bshnr %s.", self._api.bshnr)
#                 )
#         except Exception as e:
#             _LOGGER.error(f"Error while fetching tide data: {e}")
#             raise UpdateFailed(f"Error fetching tide data: {e}")
