"""Sensor platform for BSH Tides for Germany."""

from datetime import UTC, datetime
import logging

import dateutil.parser

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    # SensorEntityDescription,
)
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .__init__ import BshTidesConfigEntry
from .const import DOMAIN
from .coordinator import BshTidesCoordinator

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
        BshNextTideTimeSensor(coordinator, "next_tide_time"),
        BshNextTideLevelSensor(coordinator, "next_tide_level"),
        BshNextTideDiffSensor(coordinator, "next_tide_diff"),
        BshNextHighTideTimeSensor(coordinator, "next_high_tide_time"),
        BshNextHighTideLevelSensor(coordinator, "next_high_tide_level"),
        BshNextHighTideDiffSensor(coordinator, "next_high_tide_diff"),
        BshNextLowTideTimeSensor(coordinator, "next_low_tide_time"),
        BshNextLowTideLevelSensor(coordinator, "next_low_tide_level"),
        BshNextLowTideDiffSensor(coordinator, "next_low_tide_diff"),
        BshMeanHighWaterLevelSensor(coordinator, "mean_high_water_level"),
        BshMeanLowWaterLevelSensor(coordinator, "mean_low_water_level"),
        BshForecastCreatedSensor(coordinator, "forecast_created_at"),
        BshStationAreaSensor(coordinator, "station_area"),
    ]

    async_add_entities(entities)


class BshBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
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
        self._attr_translation_key = translation_key
        # The _attr_has_entity_name is decisive for having nicely combined entity names like "sensor.bsh_eider_sperrwerk_aussenpegel_mean_high_water_level"
        # instead of just sensor.mean_high_water_level which would be ambiguous for multiple entities.
        self._attr_has_entity_name = True
        _LOGGER.debug(
            "Initialized sensor with translation_key=%s, seo_id=%s",
            translation_key,
            coordinator.seo_id,
        )

    @property
    def unique_id(self):
        return f"bsh_{self.coordinator.seo_id}_{self._attr_translation_key}"


class BshNextTideTimeSensor(BshBaseSensor):
    """Sensor for the next tide time according to live forecast."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if ts > now:
                _LOGGER.debug("%s: Next tide time is %s", self.unique_id, ts)
                return ts
        return None


class BshNextTideLevelSensor(BshBaseSensor):
    """Sensor for the next tide level in cm according to live forecast."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_icon = "mdi:waves"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if ts > now:
                value = item["value"]
                try:
                    level = round(float(value)) if value not in (None, "") else None
                except (TypeError, ValueError):
                    _LOGGER.warning(
                        "%s: Invalid value for next tide level: %s",
                        self.unique_id,
                        value,
                    )
                    return None
                _LOGGER.debug("%s: Next tide level is %s cm", self.unique_id, level)
                return level
        return None


class BshNextTideDiffSensor(BshBaseSensor):
    """Sensor for relative difference to the mean tide level in m according to live forecast."""

    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_icon = "mdi:arrow-expand-vertical"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if ts > now:
                try:
                    # cleanup values: "+/-0,0 m", "-0,1 m", "+0,2 m"
                    value = float(
                        item["forecast"]
                        .replace(",", ".")
                        .replace("+/-", "")
                        .replace("+", "")
                        .replace(" m", "")
                    )
                    _LOGGER.debug("%s: Next tide diff is %s m", self.unique_id, value)
                    return value
                except Exception as e:
                    _LOGGER.warning(
                        "%s: Failed to parse next tide diff: %s", self.unique_id, e
                    )
                    return None
        return None


class BshNextHighTideTimeSensor(BshBaseSensor):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "HW" and ts > now:
                _LOGGER.debug("%s: Next high tide time is %s", self.unique_id, ts)
                return ts
        return None


class BshNextHighTideDiffSensor(BshBaseSensor):
    """Sensor for relative difference to the mean tide level in m according to live forecast."""

    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_icon = "mdi:arrow-expand-vertical"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "HW" and ts > now:
                try:
                    # cleanup values: "+/-0,0 m", "-0,1 m", "+0,2 m"
                    value = float(
                        item["forecast"]
                        .replace(",", ".")
                        .replace("+/-", "")
                        .replace("+", "")
                        .replace(" m", "")
                    )
                    _LOGGER.debug(
                        "%s: Next high tide diff is %s m", self.unique_id, value
                    )
                    return value
                except Exception as e:
                    _LOGGER.warning(
                        "%s: Failed to parse high tide diff: %s", self.unique_id, e
                    )
                    return None
        return None


class BshNextHighTideLevelSensor(BshBaseSensor):
    """Sensor for the next high tide level in cm according to live forecast."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_icon = "mdi:wave-arrow-up"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "HW" and ts > now:
                value = item["value"]
                try:
                    level = round(float(value)) if value not in (None, "") else None
                except (TypeError, ValueError):
                    _LOGGER.warning(
                        "%s: Invalid value for high tide level: %s",
                        self.unique_id,
                        value,
                    )
                    return None
                _LOGGER.debug(
                    "%s: Next high tide level is %s cm", self.unique_id, level
                )
                return level
        return None


class BshNextLowTideTimeSensor(BshBaseSensor):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "NW" and ts > now:
                _LOGGER.debug("%s: Next low tide time is %s", self.unique_id, ts)
                return ts
        return None


class BshNextLowTideDiffSensor(BshBaseSensor):
    """Sensor for relative difference to the mean tide level in m according to live forecast."""

    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_icon = "mdi:arrow-expand-vertical"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "NW" and ts > now:
                try:
                    # cleanup values: "+/-0,0 m", "-0,1 m", "+0,2 m"
                    value = float(
                        item["forecast"]
                        .replace(",", ".")
                        .replace("+/-", "")
                        .replace("+", "")
                        .replace(" m", "")
                    )
                    _LOGGER.debug(
                        "%s: Next low tide diff is %s m", self.unique_id, value
                    )
                    return value
                except Exception as e:
                    _LOGGER.warning(
                        "%s: Failed to parse low tide diff: %s", self.unique_id, e
                    )
                    return None
        return None


class BshNextLowTideLevelSensor(BshBaseSensor):
    """Sensor for the next low tide level in cm according to live forecast."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_icon = "mdi:wave-arrow-down"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if item["event"] == "NW" and ts > now:
                value = item["value"]
                try:
                    level = round(float(value)) if value not in (None, "") else None
                except (TypeError, ValueError):
                    _LOGGER.warning(
                        "%s: Invalid value for low tide level: %s",
                        self.unique_id,
                        value,
                    )
                    return None
                _LOGGER.debug("%s: Next low tide level is %s cm", self.unique_id, level)
                return level
        return None


class BshMeanHighWaterLevelSensor(BshBaseSensor):
    """Mean High Water Level in cm for the current station."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_icon = "mdi:waves"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        value = self.coordinator.data.get("MHW")
        try:
            level = round(float(value)) if value not in (None, "") else None
        except (TypeError, ValueError):
            _LOGGER.warning(
                "%s: Invalid value for mean high water level: %s", self.unique_id, value
            )
            return None
        _LOGGER.debug("%s: Next mean high water level is %s cm", self.unique_id, level)
        return level


class BshMeanLowWaterLevelSensor(BshBaseSensor):
    """Mean Low Water Level in cm for the current station."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_icon = "mdi:waves"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        value = self.coordinator.data.get("MNW")
        try:
            level = round(float(value)) if value not in (None, "") else None
        except (TypeError, ValueError):
            _LOGGER.warning(
                "%s: Invalid value for mean low water level: %s", self.unique_id, value
            )
            return None
        _LOGGER.debug("%s: Next mean low water level is %s cm", self.unique_id, level)
        return level


class BshForecastCreatedSensor(BshBaseSensor):
    """Forecast Created At in UTC for the current station."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        val = self.coordinator.data.get("creation_forecast")
        value = dateutil.parser.parse(val) if val else None
        _LOGGER.debug("%s: Forecast was created at %s", self.unique_id, value)
        return value


class BshStationAreaSensor(BshBaseSensor):
    """Contains the area of the station, e.g. Elbe for St. Pauli."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:map-marker"

    def __init__(self, coordinator: BshTidesCoordinator, translation_key: str):
        super().__init__(coordinator, translation_key)

    @property
    def native_value(self):
        value = self.coordinator.data.get("area")
        _LOGGER.debug("%s: Station area is %s", self.unique_id, value)
        return value
