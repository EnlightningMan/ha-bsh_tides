"""The BSH Tides for Germany integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import BshTidesCoordinator
from .bsh_api import BshApi

_LOGGER = logging.getLogger(__name__)

# BSH Api Response gets put into a sensor
_PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to the new gdi.bsh.de OGC API.

    v1 stored the old BSH "bshnr" (e.g. "111P"). The new API addresses stations
    by slug (e.g. "norderney_riffgat"). The new API does not expose the old
    bshnr, so we map by station name (the entry title) against the new station
    list. The slug equals the existing seo_id, so entity unique_ids are kept and
    the user's history/automations survive the migration untouched.
    """
    if entry.version == 1:
        old_key = entry.data.get("bshnr")
        try:
            stations = await BshApi.fetch_station_list()
        except Exception as err:  # noqa: BLE001 - transient: let HA retry later
            _LOGGER.warning("BSH migration deferred (station list unavailable): %s", err)
            return False

        title = (entry.title or "").strip().casefold()
        slug = next(
            (sid for sid, name, _ in stations if name.strip().casefold() == title),
            None,
        )
        if slug is None:
            # Maybe the stored key already is a valid slug.
            slug = next((sid for sid, _, _ in stations if sid == old_key), None)
        if slug is None:
            _LOGGER.error(
                "Could not migrate BSH station '%s' (title '%s') to the new API. "
                "Please remove and re-add the integration.",
                old_key,
                entry.title,
            )
            return False

        hass.config_entries.async_update_entry(
            entry, data={**entry.data, "bshnr": slug}, version=2
        )
        _LOGGER.info("Migrated BSH station '%s' -> slug '%s'", old_key, slug)

    return True


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
