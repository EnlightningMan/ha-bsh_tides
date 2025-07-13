import pytest
from unittest.mock import AsyncMock, MagicMock
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.bsh_tides.coordinator import BshTidesCoordinator
from custom_components.bsh_tides.exceptions import BshCannotConnect


@pytest.fixture
def dummy_hass():
    """Dummy Home Assistant instance."""
    class DummyHass:
        def __init__(self):
            self.data = {}
            self.bus = None
            self.config = None

    return DummyHass()

@pytest.fixture
def mock_bsh_api():
    """Mock the BSH API."""
    # Mocking the API class, especially the async_fetch_data method
    mock_api = MagicMock()
    
    return mock_api


@pytest.fixture
def dummy_coordinator(dummy_hass, mock_bsh_api):
    """Create a dummy BshTidesCoordinator."""
    coordinator = BshTidesCoordinator(hass=dummy_hass, bshnr="999X")
    coordinator.api = mock_bsh_api  # Assign the mocked BshApi to the coordinator
    return coordinator


# --- Tests --- #

@pytest.mark.asyncio
async def test_coordinator_update_fails_on_api_error(mock_bsh_api, dummy_coordinator):
    """Test that coordinator raises UpdateFailed on API error."""

    # Simulate that async_fetch_data will raise an error
    mock_bsh_api.async_fetch_data = AsyncMock(side_effect=BshCannotConnect("Could not connect to BSH API"))

    with pytest.raises(UpdateFailed) as exc:
        await dummy_coordinator._async_update_data()

    # Check if the correct error message is raised
    assert "Could not connect to BSH API" in str(exc.value)

@pytest.mark.asyncio
async def test_coordinator_parses_forecast_data(mock_bsh_api, dummy_coordinator):
    """Test that forecast data is parsed only once."""

    # Mock the API data to simulate forecast data
    mock_bsh_api.async_fetch_data = AsyncMock(return_value={
        "station_name": "Dummy Station",
        "seo_id": "dummy_station",
        "hwnw_forecast": {
            "data": [
                {"timestamp": "2025-07-13T12:00:00", "forecast": "+/-0,0 m"},
                {"timestamp": "2025-07-13T14:00:00", "forecast": "-0,1 m"},
                {"timestamp": "2025-07-13T16:00:00", "forecast": "+0,3 m"},
            ]
        }
    })

    # Perform the update once
    dummy_coordinator.data = await dummy_coordinator._async_update_data()

    # Check that parsed data is stored correctly
    assert dummy_coordinator._parsed_forecast_data is not None
    assert len(dummy_coordinator._parsed_forecast_data) == 3  # Should have 3 parsed items
    assert dummy_coordinator.station_name == "Dummy Station"
    assert dummy_coordinator.seo_id == "dummy_station"
    assert dummy_coordinator.forecast_data[0]["forecast"] == 0
    assert dummy_coordinator.forecast_data[1]["forecast"] == -10
    assert dummy_coordinator.forecast_data[2]["forecast"] == 30

@pytest.mark.asyncio
async def test_coordinator_parses_curve_forecast(mock_bsh_api, dummy_coordinator):
    """Test that forecast data is parsed only once."""

    # Mock the API data to simulate forecast data
    mock_bsh_api.async_fetch_data = AsyncMock(return_value={
        "station_name": "Dummy Station",
        "seo_id": "dummy_station",
        "bshnr": "999X",
        "MHW": 744,
        "MNW": 430,
        "curve_forecast": {
            "data": [
                {
                    "timestamp": "2025-07-13 14:30:00+02:00",
                    "astro": 475,
                    "curveforecast": 415,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 14:40:00+02:00",
                    "astro": 471,
                    "curveforecast": 408,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 14:50:00+02:00",
                    "astro": 466,
                    "curveforecast": 400,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 15:00:00+02:00",
                    "astro": 461,
                    "curveforecast": 400,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 15:10:00+02:00",
                    "astro": 457,
                    "curveforecast": 403,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 15:20:00+02:00",
                    "astro": 453,
                    "curveforecast": 398,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 15:30:00+02:00",
                    "astro": 448,
                    "curveforecast": 395,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 15:33:00+02:00",
                    "astro": 448,
                    "curveforecast": 398,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 15:40:00+02:00",
                    "astro": 453,
                    "curveforecast": 415,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 15:50:00+02:00",
                    "astro": 476,
                    "curveforecast": 439,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 20:30:00+02:00",
                    "astro": 770,
                    "curveforecast": 780,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 20:40:00+02:00",
                    "astro": 770,
                    "curveforecast": 770,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 20:50:00+02:00",
                    "astro": 770,
                    "curveforecast": 784,
                    "measurement": None
                },
                {
                    "timestamp": "2025-07-13 20:51:00+02:00",
                    "astro": 770,
                    "curveforecast": 770,
                    "measurement": None
                },
            ]
        }
    })

    # Perform the update once
    dummy_coordinator.data = await dummy_coordinator._async_update_data()

    # Check that parsed data is stored correctly
    assert dummy_coordinator._parsed_forecast_data is not None
    assert len(dummy_coordinator._parsed_forecast_data) == 2  # Should have 1 parsed item
    assert dummy_coordinator.station_name == "Dummy Station"
    assert dummy_coordinator.seo_id == "dummy_station"
    # check the low tide event
    assert dummy_coordinator.forecast_data[0]["timestamp"] == "2025-07-13 15:30:00+02:00"
    assert dummy_coordinator.forecast_data[0]["forecast"] == -35
    # check the high tide event
    assert dummy_coordinator.forecast_data[1]["timestamp"] == "2025-07-13 20:50:00+02:00"
    assert dummy_coordinator.forecast_data[1]["forecast"] == 40
