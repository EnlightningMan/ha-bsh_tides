"""The BSH Tides for Germany integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import BshTidesCoordinator

# TEMPORARY: one-time v1 (bshnr) -> v2 (slug) migration for the 2026-05 API
# switch. Home Assistant picks up ``async_migrate_entry`` from this module via
# the re-export below. Both the import and the ``legacy_migration`` package can
# be deleted once no pre-v2 config entries remain (see that package's docstring).
from .legacy_migration import async_migrate_entry

_LOGGER = logging.getLogger(__name__)

# Re-exported so Home Assistant discovers the migration hook on this module.
__all__ = ["async_migrate_entry", "async_setup_entry", "async_unload_entry"]

# BSH Api Response gets put into a sensor
_PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BSH Tides for Germany from a config entry."""

    bshnr = entry.data["bshnr"]
    coordinator = BshTidesCoordinator(hass, bshnr)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("Initial data fetch failed: %s", err)
        raise ConfigEntryNotReady(f"BSH Tides update failed: {err}") from err

    # Register coordinator in hass.data[DOMAIN][entry.entry_id]
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
