"""TEMPORARY config-entry migration: old BSH ``bshnr`` keys -> station slugs.

In May 2026 the BSH retired the undocumented ``wasserstand-nordsee.bsh.de``
endpoint (which addressed stations by ``bshnr``, e.g. ``111P``) in favour of
the official gdi.bsh.de OGC API (which uses slugs, e.g. ``norderney_riffgat``).
Config entries created by integration versions < 0.1.0 still store the old
``bshnr`` under the ``data["bshnr"]`` key, so they must be migrated to the slug.

This whole package exists only to carry users across that one-time switch and
is intentionally isolated from the runtime code so it can be deleted cleanly.

--------------------------------------------------------------------------------
REMOVAL — safe to delete this entire ``legacy_migration`` package once no
installs run config entries below schema version 2 anymore. Practically: from
~mid-2027 (about a year after the 0.1.0 release that introduced it), enough
update cycles will have passed that every active install has migrated.

To remove:
  * delete the ``legacy_migration/`` folder, and
  * drop the ``from .legacy_migration import async_migrate_entry`` re-export in
    ``custom_components/bsh_tides/__init__.py``.
Home Assistant only calls ``async_migrate_entry`` for entries whose version is
below the config-flow ``VERSION`` (2); with none left, the hook is dead code.
--------------------------------------------------------------------------------
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from ..bsh_api import BshApi
from ..const import DOMAIN
from .station_map import LEGACY_BSHNR_TO_SLUG

_LOGGER = logging.getLogger(__name__)

# Entity unique_ids are "bsh_{seo_id}_{translation_key}". To recover the seo_id
# (which equals the new station slug) we strip the "bsh_" prefix and a known
# translation-key suffix. Listed longest-first so we never strip a shorter key
# that happens to be a tail of a longer one. Keep in sync with sensor.py.
_UNIQUE_ID_SUFFIXES: tuple[str, ...] = tuple(
    sorted(
        (
            "next_tide_time",
            "next_high_tide_time",
            "next_low_tide_time",
            "next_tide_level",
            "next_high_tide_level",
            "next_low_tide_level",
            "next_tide_diff",
            "next_high_tide_diff",
            "next_low_tide_diff",
            "next_tide_event",
            "mean_high_water_level",
            "mean_low_water_level",
            "forecast_created_at",
            "station_area",
            "forecast_type",
        ),
        key=len,
        reverse=True,
    )
)


def _seo_id_from_unique_id(unique_id: str | None) -> str | None:
    """Extract the seo_id (== new slug) from an entity unique_id.

    "bsh_hamburg_st-pauli_next_high_tide_time" -> "hamburg_st-pauli".
    """
    if not unique_id or not unique_id.startswith("bsh_"):
        return None
    body = unique_id[len("bsh_") :]
    for suffix in _UNIQUE_ID_SUFFIXES:
        if body.endswith("_" + suffix):
            return body[: -(len(suffix) + 1)]
    return None


def _slug_from_entity_registry(hass: HomeAssistant, entry_id: str) -> str | None:
    """Recover the station slug from this entry's existing entities.

    Offline and rename-proof: the entity unique_ids were derived from the old
    seo_id, which is identical to the new slug.
    """
    ent_reg = er.async_get(hass)
    for ent in er.async_entries_for_config_entry(ent_reg, entry_id):
        seo_id = _seo_id_from_unique_id(ent.unique_id)
        if seo_id:
            return seo_id
    return None


def _migrate_device_identifier(hass: HomeAssistant, old_key: str, slug: str) -> None:
    """Re-point the existing device from the old bshnr to the new slug.

    The device identifier is (DOMAIN, bshnr); after migration the coordinator
    reports (DOMAIN, slug). Updating the identifier in place keeps the user's
    device-level customisations (area, name) and avoids leaving an orphan.
    """
    if old_key == slug:
        return
    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get_device(identifiers={(DOMAIN, old_key)})
    if device is None:
        return
    dev_reg.async_update_device(device.id, new_identifiers={(DOMAIN, slug)})
    _LOGGER.debug("Re-pointed device %s identifier %s -> %s", device.id, old_key, slug)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to the new gdi.bsh.de OGC API.

    v1 stored the old BSH "bshnr" (e.g. "111P"). The new API addresses stations
    by slug (e.g. "norderney_riffgat") and does not expose the old bshnr, so we
    resolve the slug deterministically, preferring rename-proof/offline sources:

      1. the seo_id encoded in this entry's existing entity unique_ids,
      2. a static bshnr -> slug table of every station the old API served,
      3. matching the entry title against the live station list (last resort).

    The slug equals the old seo_id, so entity unique_ids are preserved and the
    user's history/automations survive untouched.
    """
    if entry.version > 1:
        return True

    old_key = entry.data.get("bshnr")

    # 1) Rename-proof + offline: derive slug from existing entities.
    slug = _slug_from_entity_registry(hass, entry.entry_id)

    # 2) Rename-proof + offline: static lookup of the retired bshnr.
    if slug is None:
        slug = LEGACY_BSHNR_TO_SLUG.get(old_key)

    # 3) Last resort: match the entry title against the live station list. This
    #    needs the network, so failures here are treated as transient (retry).
    if slug is None:
        try:
            stations = await BshApi.fetch_station_list()
        except Exception as err:  # noqa: BLE001 - transient: let HA retry later
            _LOGGER.warning(
                "BSH migration deferred (station list unavailable): %s", err
            )
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

    _migrate_device_identifier(hass, old_key, slug)
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, "bshnr": slug}, version=2
    )
    _LOGGER.info("Migrated BSH station '%s' -> slug '%s'", old_key, slug)

    return True
