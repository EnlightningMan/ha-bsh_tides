"""The BSH Tides for Germany integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .bsh_api import BshApi

# BSH Api Response gets put into a sensor
_PLATFORMS: list[Platform] = [Platform.SENSOR]

# Create ConfigEntry type alias with API object
type BshTidesConfigEntry = ConfigEntry[BshApi]


async def async_setup_entry(hass: HomeAssistant, entry: BshTidesConfigEntry) -> bool:
    """Set up BSH Tides for Germany from a config entry."""

    # Create API instance for correct BSHNR (validates connection)
    api = BshApi(entry.data["bshnr"])

    # runtime_data contains the entity specific config as long as the entity exists.
    # The bsh endpoint is config specific, so it makes sense to keep in the runtime data.
    entry.runtime_data = {"api": api}

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: BshTidesConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
