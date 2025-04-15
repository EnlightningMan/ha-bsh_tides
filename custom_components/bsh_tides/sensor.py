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
from .const import DOMAIN, TideEvent
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
        BshTideEventTimeSensor(coordinator),
        BshTideEventTimeSensor(coordinator, TideEvent.HIGH),
        BshTideEventTimeSensor(coordinator, TideEvent.LOW),
        BshNextTideEventSensor(coordinator),
        BshTideLevelSensor(coordinator),
        BshTideLevelSensor(coordinator, TideEvent.HIGH),
        BshTideLevelSensor(coordinator, TideEvent.LOW),
        BshTideDiffSensor(coordinator),
        BshTideDiffSensor(coordinator, TideEvent.HIGH),
        BshTideDiffSensor(coordinator, TideEvent.LOW),
        BshMeanWaterLevelSensor(coordinator, TideEvent.HIGH),
        BshMeanWaterLevelSensor(coordinator, TideEvent.LOW),
        BshForecastCreatedSensor(coordinator),
        BshStationAreaSensor(coordinator),
    ]

    async_add_entities(entities)


class BshBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor class for BSH Tides integration.

    This class provides common functionality and attributes for all BSH Tides sensors.
    """

    def __init__(self, coordinator: BshTidesCoordinator):
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.bshnr)},
            "name": f"BSH {coordinator.station_name}",
            "manufacturer": "BSH",
            "entry_type": "service",
        }
        self._attr_attribution = coordinator.data.get(
            "copyright_note",
            "© BSH – Bundesamt für Seeschifffahrt und Hydrographie",
        )

        # The _attr_has_entity_name is decisive for having nicely combined entity names like "sensor.bsh_eider_sperrwerk_aussenpegel_mean_high_water_level"
        # instead of just sensor.mean_high_water_level which would be ambiguous for multiple entities.
        self._attr_has_entity_name = True
        _LOGGER.debug("Initialized sensor with seo_id=%s", coordinator.seo_id)

    @property
    def unique_id(self):
        return f"bsh_{self.coordinator.seo_id}_{self._attr_translation_key}"

    @staticmethod
    def get_event_prefix(event: TideEvent = None) -> str:
        if event == TideEvent.HIGH:
            return "high_"
        if event == TideEvent.LOW:
            return "low_"
        return ""


class BshTideEventTimeSensor(BshBaseSensor):
    """Sensor for tide event time for the next/high/low event."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock"

    def __init__(self, coordinator: BshTidesCoordinator, event: TideEvent = None):
        super().__init__(coordinator)
        prefix = self.get_event_prefix(event)
        self._attr_translation_key = f"next_{prefix}tide_time"
        self._event = event

    @property
    def native_value(self) -> datetime | None:
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if ts > now and (
                self._event is None or item.get("event") == self._event.value
            ):
                _LOGGER.debug(
                    "%s: Tide time (%s) is %s", self.unique_id, self._event, ts
                )
                return ts
        return None


class BshTideLevelSensor(BshBaseSensor):
    """Sensor for the tide level (cm) for the next/high/low event."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_icon = "mdi:waves"

    def __init__(self, coordinator: BshTidesCoordinator, event: TideEvent = None):
        super().__init__(coordinator)
        prefix = self.get_event_prefix(event)
        self._attr_translation_key = f"next_{prefix}tide_level"
        self._event = event

    @property
    def native_value(self) -> int | None:
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if ts > now and (
                self._event is None or item.get("event") == self._event.value
            ):
                value = item.get("value")
                try:
                    level = round(float(value)) if value not in (None, "") else None
                    _LOGGER.debug(
                        "%s: Tide level (%s) is %s cm",
                        self.unique_id,
                        self._event,
                        level,
                    )
                    return level
                except (TypeError, ValueError):
                    _LOGGER.debug(
                        "%s: Invalid tide level (%s): %s",
                        self.unique_id,
                        self._event,
                        value,
                    )
                    return None
        return None


class BshTideDiffSensor(BshBaseSensor):
    """Sensor for the tide difference (cm) to mean water level for the next/high/low event."""

    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_icon = "mdi:arrow-expand-vertical"

    def __init__(self, coordinator: BshTidesCoordinator, event: TideEvent = None):
        prefix = self.get_event_prefix(event)
        self._attr_translation_key = f"next_{prefix}tide_diff"
        super().__init__(coordinator)
        self._event = event

    @property
    def native_value(self) -> int | None:
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if (
                self._event is None or item.get("event") == self._event.value
            ) and ts > now:
                try:
                    value = round(
                        float(
                            item["forecast"]
                            .replace(",", ".")
                            .replace("+/-", "")
                            .replace("+", "")
                            .replace(" m", "")
                        )
                        * 100.0
                    )
                    _LOGGER.debug(
                        "%s: Tide diff (%s) is %s m", self.unique_id, self._event, value
                    )
                    return value
                except Exception as e:
                    _LOGGER.debug(
                        "%s: Failed to parse tide diff: %s", self.unique_id, e
                    )
                    return None
        return None


class BshNextTideEventSensor(BshBaseSensor):
    """Sensor for the next tide event (specifies: 'high_tide' or 'low_tide')."""

    _attr_icon = "mdi:arrow-split-horizontal"
    _attr_translation_key = "next_tide_event"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["high_tide", "low_tide"]

    def __init__(self, coordinator: BshTidesCoordinator):
        super().__init__(coordinator)

    @property
    def native_value(self) -> str | None:
        now = datetime.now(UTC)
        for item in self.coordinator.forecast_data:
            ts = dateutil.parser.parse(item["timestamp"])
            if ts > now:
                event = item.get("event")
                if event == TideEvent.HIGH.value:
                    return "high_tide"
                if event == TideEvent.LOW.value:
                    return "low_tide"
        return None


class BshMeanWaterLevelSensor(BshBaseSensor):
    """Sensor for mean high or low water level (cm)."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_icon = "mdi:waves"

    def __init__(self, coordinator: BshTidesCoordinator, event: TideEvent):
        super().__init__(coordinator)
        self._event = event
        self._data_key = "MHW" if event == TideEvent.HIGH else "MNW"
        prefix = self.get_event_prefix(event)
        self._attr_translation_key = f"mean_{prefix}water_level"

    @property
    def native_value(self) -> int | None:
        value = self.coordinator.data.get(self._data_key)
        try:
            level = round(float(value)) if value not in (None, "") else None
        except (TypeError, ValueError):
            _LOGGER.debug(
                "%s: Invalid value for %s: %s",
                self.unique_id,
                self._attr_translation_key,
                value,
            )
            return None
        _LOGGER.debug(
            "%s: %s is %s cm", self.unique_id, self._attr_translation_key, level
        )
        return level


class BshForecastCreatedSensor(BshBaseSensor):
    """Forecast Created At in UTC for the current station."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock"
    _attr_translation_key = "forecast_created_at"

    def __init__(self, coordinator: BshTidesCoordinator):
        super().__init__(coordinator)

    @property
    def native_value(self) -> datetime | None:
        val = self.coordinator.data.get("creation_forecast")
        value = dateutil.parser.parse(val) if val else None
        _LOGGER.debug("%s: Forecast was created at %s", self.unique_id, value)
        return value


class BshStationAreaSensor(BshBaseSensor):
    """Contains the area of the station, e.g. Elbe for St. Pauli."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:map-marker"
    _attr_translation_key = "station_area"

    def __init__(self, coordinator: BshTidesCoordinator):
        super().__init__(coordinator)

    @property
    def native_value(self) -> str | None:
        value = self.coordinator.data.get("area")
        _LOGGER.debug("%s: Station area is %s", self.unique_id, value)
        return value
