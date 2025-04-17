import pytest
from homeassistant.config_entries import ConfigEntryNotReady
from custom_components.bsh_tides.sensor import async_setup_entry
from custom_components.bsh_tides.coordinator import BshTidesCoordinator
from custom_components.bsh_tides.bsh_api import BshApi
from custom_components.bsh_tides.const import DOMAIN

@pytest.mark.asyncio
async def test_async_setup_entry_with_real_coordinator(monkeypatch):
    """Test async_setup_entry raises ConfigEntryNotReady on real API error."""

    # Dummy ConfigEntry with entry_id
    class DummyConfigEntry:
        entry_id = "dummy_id"
        data = {"bshnr": "123X"}  # fake ID

    # Dummy hass with .data structure
    class DummyHass:
        def __init__(self):
            self.data = {DOMAIN: {}}

    dummy_hass = DummyHass()

    # Patch API call inside the coordinator
    async def failing_fetch_data(self):
        raise Exception("Simulated fetch_data failure")

    monkeypatch.setattr(BshApi, "async_fetch_data", failing_fetch_data)

    # Inject coordinator with failing fetch
    coordinator = BshTidesCoordinator(dummy_hass, bshnr="123X")
    dummy_hass.data[DOMAIN]["dummy_id"] = coordinator

    # Dummy entity registration
    async def dummy_add_entities(entities):
        pass

    with pytest.raises(ConfigEntryNotReady) as exc:
        await async_setup_entry(dummy_hass, DummyConfigEntry(), dummy_add_entities)

    assert "Simulated fetch_data failure" in str(exc.value)
