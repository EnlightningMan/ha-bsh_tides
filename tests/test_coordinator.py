import pytest
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


@pytest.mark.asyncio
async def test_coordinator_update_fails_on_api_error(monkeypatch, dummy_hass):
    """Test that coordinator raises UpdateFailed on API error."""

    async def failing_fetch_data(self):
        raise BshCannotConnect("Could not connect to BSH API")

    monkeypatch.setattr(
        "custom_components.bsh_tides.bsh_api.BshApi.async_fetch_data",
        failing_fetch_data,
    )

    coordinator = BshTidesCoordinator(dummy_hass, bshnr="999X")

    with pytest.raises(UpdateFailed) as exc:
        await coordinator._async_update_data()

    assert "Could not connect to BSH API" in str(exc.value)
