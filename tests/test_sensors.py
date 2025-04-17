import pytest
from datetime import datetime, timedelta, UTC

from custom_components.bsh_tides.const import TideEvent
from custom_components.bsh_tides.sensor import (
    BshForecastCreatedSensor,
    BshMeanWaterLevelSensor,
    BshNextTideEventSensor,
    BshStationAreaSensor,
    BshTideDiffSensor,
    BshTideLevelSensor,    
    BshTideEventTimeSensor,
)

# --- Fixtures --- #

@pytest.fixture
def dummy_forecast():
    return [
        {
            "timestamp": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "value": 165.3,
            "forecast": "+0,3 m",
            "event": "HW",
        },
        {
            "timestamp": (datetime.now(UTC) + timedelta(hours=8)).isoformat(),
            "value": 13,
            "forecast": "+/-0,0 m",
            "event": "NW",
        }
    ]

@pytest.fixture
def dummy_coordinator(dummy_forecast):
    class DummyCoordinator:
        def __init__(self):
            self.bshnr = "123P"
            self.seo_id = "dummy_station"
            self.station_name = "Dummy Station"
            self.data = {
                "station_name": self.station_name,
                "area": "dummy_area",
                "seo_id": self.seo_id,
                "MHW": 180,
                "MNW": 90,
                "creation_forecast": datetime.now(UTC).isoformat(),
            }
            self.forecast_data = dummy_forecast
    return DummyCoordinator()

# --- Tests: BshNextTideTimeSensor --- #

def test_next_tide_time_sensor_value(dummy_coordinator):
    sensor = BshTideEventTimeSensor(dummy_coordinator)
    value = sensor.native_value
    assert isinstance(value, datetime)
    assert value > datetime.now(UTC)

def test_next_tide_time_sensor_meta(dummy_coordinator):
    sensor = BshTideEventTimeSensor(dummy_coordinator)
    assert sensor.unique_id == "bsh_dummy_station_next_tide_time"
    assert sensor.translation_key == "next_tide_time"

# --- Tests: BshTideLevelSensor --- #

def test_next_tide_level_sensor_value(dummy_coordinator):
    sensor = BshTideLevelSensor(dummy_coordinator)
    value = sensor.native_value
    assert isinstance(value, int)
    assert value == 165

def test_next_tide_level_sensor_meta(dummy_coordinator):
    sensor = BshTideLevelSensor(dummy_coordinator)
    assert sensor.unique_id == "bsh_dummy_station_next_tide_level"
    assert sensor.translation_key == "next_tide_level"

def test_next_tide_level_sensor_invalid_value(dummy_coordinator):
    dummy_coordinator.forecast_data[0]["value"] = ""
    sensor = BshTideLevelSensor(dummy_coordinator)
    assert sensor.native_value is None


# --- Tests: BshTideLevelSensor for low tide --- #

def test_next_low_tide_level_sensor_value(dummy_coordinator):
    sensor = BshTideLevelSensor(dummy_coordinator, TideEvent.LOW)
    value = sensor.native_value
    assert isinstance(value, int)
    assert value == 13

def test_next_low_tide_level_sensor_meta(dummy_coordinator):
    sensor = BshTideLevelSensor(dummy_coordinator, TideEvent.LOW)
    assert sensor.unique_id == "bsh_dummy_station_next_low_tide_level"
    assert sensor.translation_key == "next_low_tide_level"

def test_next_low_tide_level_sensor_invalid_value(dummy_coordinator):   
    dummy_coordinator.forecast_data[1]["value"] = "lala"
    sensor = BshTideLevelSensor(dummy_coordinator, TideEvent.LOW)
    assert sensor.native_value is None

def test_next_low_tide_level_sensor_invalid_event(dummy_coordinator):
    dummy_coordinator.forecast_data[1]["event"] = "HW"
    sensor = BshTideLevelSensor(dummy_coordinator, TideEvent.LOW)
    assert sensor.native_value is None


# --- Tests: BshTideLevelSensor for high tide --- #

def test_next_high_tide_level_sensor_value(dummy_coordinator):
    sensor = BshTideLevelSensor(dummy_coordinator, TideEvent.HIGH)
    value = sensor.native_value
    assert isinstance(value, int)
    assert value == 165

def test_next_high_tide_level_sensor_meta(dummy_coordinator):
    sensor = BshTideLevelSensor(dummy_coordinator, TideEvent.HIGH)
    assert sensor.unique_id == "bsh_dummy_station_next_high_tide_level"
    assert sensor.translation_key == "next_high_tide_level"

def test_next_high_tide_level_sensor_invalid_value(dummy_coordinator):   
    dummy_coordinator.forecast_data[0]["value"] = "lala"
    sensor = BshTideLevelSensor(dummy_coordinator, TideEvent.HIGH)
    assert sensor.native_value is None

def test_next_high_tide_level_sensor_invalid_event(dummy_coordinator):
    dummy_coordinator.forecast_data[0]["event"] = "NW"
    sensor = BshTideLevelSensor(dummy_coordinator, TideEvent.HIGH)
    assert sensor.native_value is None

# --- Tests: BshTideDiffSensor --- #

def test_next_tide_diff_sensor_value(dummy_coordinator):
    sensor = BshTideDiffSensor(dummy_coordinator)
    value = sensor.native_value
    assert isinstance(value, int)
    assert value == 30

def test_low_tide_diff_sensor_value(dummy_coordinator):
    sensor = BshTideDiffSensor(dummy_coordinator, TideEvent.LOW)
    value = sensor.native_value
    assert isinstance(value, int)
    assert value == 0

def test_tide_diff_sensor_invalid_forecast(dummy_coordinator):
    dummy_coordinator.forecast_data[0]["forecast"] = "not a number"
    sensor = BshTideDiffSensor(dummy_coordinator, TideEvent.HIGH)
    assert sensor.native_value is None

# --- Tests: BshMeanWaterLevelSensor --- #

def test_mean_high_water_level_sensor_keys(dummy_coordinator):
    sensor = BshMeanWaterLevelSensor(dummy_coordinator, TideEvent.HIGH)
    assert sensor.unique_id == "bsh_dummy_station_mean_high_water_level"
    assert sensor.translation_key == "mean_high_water_level"

def test_mean_high_water_level_sensor_value(dummy_coordinator):
    sensor = BshMeanWaterLevelSensor(dummy_coordinator, TideEvent.HIGH)
    value = sensor.native_value
    assert isinstance(value, int)
    assert value == 180

def test_mean_low_water_level_sensor_keys(dummy_coordinator):
    sensor = BshMeanWaterLevelSensor(dummy_coordinator, TideEvent.LOW)
    assert sensor.unique_id == "bsh_dummy_station_mean_low_water_level"
    assert sensor.translation_key == "mean_low_water_level"

def test_mean_low_water_level_sensor_value(dummy_coordinator):
    sensor = BshMeanWaterLevelSensor(dummy_coordinator, TideEvent.LOW)
    value = sensor.native_value
    assert isinstance(value, int)
    assert value == 90

# --- Tests: BshForecastCreatedSensor --- #

def test_forecast_created_sensor_keys(dummy_coordinator):
    sensor = BshForecastCreatedSensor(dummy_coordinator)
    assert sensor.unique_id == "bsh_dummy_station_forecast_created_at"
    assert sensor.translation_key == "forecast_created_at"

def test_forecast_created_sensor_value(dummy_coordinator):
    sensor = BshForecastCreatedSensor(dummy_coordinator)
    value = sensor.native_value
    assert isinstance(value, datetime)
    assert value < datetime.now(UTC) + timedelta(minutes=1)

# --- Tests: BshStationAreaSensor --- #

def test_station_area_sensor_keys(dummy_coordinator):
    sensor = BshStationAreaSensor(dummy_coordinator)
    assert sensor.unique_id == "bsh_dummy_station_station_area"
    assert sensor.translation_key == "station_area"

def test_station_area_sensor_value(dummy_coordinator):
    sensor = BshStationAreaSensor(dummy_coordinator)
    value = sensor.native_value
    assert isinstance(value, str)
    assert value == "dummy_area"

# --- Tests: BshNextTideEventSensor --- #

def test_next_tide_event_sensor_value(dummy_coordinator):
    sensor = BshNextTideEventSensor(dummy_coordinator)
    assert sensor.native_value == "high_tide"

def test_next_tide_event_sensor_value_low(dummy_coordinator):
    sensor = BshNextTideEventSensor(dummy_coordinator)
    dummy_coordinator.forecast_data[0]["event"] = "NW"
    assert sensor.native_value == "low_tide"    

def test_next_tide_event_sensor_unique_id(dummy_coordinator):
    sensor = BshNextTideEventSensor(dummy_coordinator)
    assert sensor.unique_id == "bsh_dummy_station_next_tide_event"

def test_next_tide_event_sensor_translation_key(dummy_coordinator):
    sensor = BshNextTideEventSensor(dummy_coordinator)
    assert sensor.translation_key == "next_tide_event"