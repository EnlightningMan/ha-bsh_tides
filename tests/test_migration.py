"""Tests for config-entry migration to the gdi.bsh.de OGC API (v1 -> v2)."""

import pytest

import custom_components.bsh_tides.legacy_migration as migration
from custom_components.bsh_tides import async_migrate_entry
from custom_components.bsh_tides.legacy_migration import _seo_id_from_unique_id
from custom_components.bsh_tides.bsh_api import BshApi
from custom_components.bsh_tides.const import DOMAIN


# --- helpers / fakes ------------------------------------------------------- #


class _Entity:
    def __init__(self, unique_id):
        self.unique_id = unique_id


class _Device:
    def __init__(self, identifiers):
        self.id = "dev-1"
        self.identifiers = identifiers


class _DeviceRegistry:
    def __init__(self, device=None):
        self._device = device
        self.updated = []  # list of (device_id, new_identifiers)

    def async_get_device(self, identifiers):
        if self._device and self._device.identifiers == identifiers:
            return self._device
        return None

    def async_update_device(self, device_id, new_identifiers):
        self.updated.append((device_id, new_identifiers))


class _ConfigEntries:
    def __init__(self):
        self.updates = []

    def async_update_entry(self, entry, data=None, version=None):
        self.updates.append((data, version))
        if data is not None:
            entry.data = data
        if version is not None:
            entry.version = version


class _Hass:
    def __init__(self):
        self.config_entries = _ConfigEntries()


class _Entry:
    def __init__(self, bshnr, title, version=1, entry_id="entry-1"):
        self.version = version
        self.data = {"bshnr": bshnr}
        self.title = title
        self.entry_id = entry_id


@pytest.fixture
def patch_registries(monkeypatch):
    """Patch entity/device registry access; returns a configurator."""

    state = {"entities": [], "dev_reg": _DeviceRegistry()}

    monkeypatch.setattr(migration.er, "async_get", lambda hass: object())
    monkeypatch.setattr(
        migration.er,
        "async_entries_for_config_entry",
        lambda reg, entry_id: state["entities"],
    )
    monkeypatch.setattr(migration.dr, "async_get", lambda hass: state["dev_reg"])

    return state


def _no_network(monkeypatch):
    """Make any attempt to hit the live station list fail loudly."""

    async def _boom():
        raise AssertionError("network must not be used for this path")

    monkeypatch.setattr(BshApi, "fetch_station_list", staticmethod(_boom))


# --- _seo_id_from_unique_id ------------------------------------------------ #


@pytest.mark.parametrize(
    "unique_id,expected",
    [
        ("bsh_norderney_riffgat_next_high_tide_time", "norderney_riffgat"),
        ("bsh_hamburg_st-pauli_mean_high_water_level", "hamburg_st-pauli"),
        ("bsh_bremerhaven_alter_leuchtturm_forecast_type", "bremerhaven_alter_leuchtturm"),
        ("bsh_flensburg_station_area", "flensburg"),
        ("bsh_flensburg_next_tide_event", "flensburg"),
        ("garbage", None),
        ("bsh_flensburg_unknown_suffix", None),
        (None, None),
    ],
)
def test_seo_id_from_unique_id(unique_id, expected):
    assert _seo_id_from_unique_id(unique_id) == expected


# --- async_migrate_entry --------------------------------------------------- #


@pytest.mark.asyncio
async def test_already_v2_is_noop(patch_registries):
    hass = _Hass()
    entry = _Entry("norderney_riffgat", "Norderney, Riffgat", version=2)

    assert await async_migrate_entry(hass, entry) is True
    assert hass.config_entries.updates == []  # nothing changed


@pytest.mark.asyncio
async def test_migrate_via_entity_registry_offline(patch_registries, monkeypatch):
    """Slug recovered from existing entities; no network, rename-proof."""
    _no_network(monkeypatch)
    patch_registries["entities"] = [
        _Entity("bsh_norderney_riffgat_next_high_tide_time")
    ]
    hass = _Hass()
    # Title intentionally does NOT match (simulates a renamed entry).
    entry = _Entry("111P", "My Renamed Station")

    assert await async_migrate_entry(hass, entry) is True
    assert entry.version == 2
    assert entry.data["bshnr"] == "norderney_riffgat"


@pytest.mark.asyncio
async def test_migrate_via_static_map_offline(patch_registries, monkeypatch):
    """No entities, but the old bshnr is in the static table; no network."""
    _no_network(monkeypatch)
    patch_registries["entities"] = []
    # Device exists under the old identifier -> must be re-pointed.
    patch_registries["dev_reg"] = _DeviceRegistry(_Device({(DOMAIN, "111P")}))
    hass = _Hass()
    entry = _Entry("111P", "Norderney, Riffgat")

    assert await async_migrate_entry(hass, entry) is True
    assert entry.data["bshnr"] == "norderney_riffgat"
    assert entry.version == 2
    # device identifier was migrated in place
    assert patch_registries["dev_reg"].updated == [
        ("dev-1", {(DOMAIN, "norderney_riffgat")})
    ]


@pytest.mark.asyncio
async def test_migrate_via_name_match(patch_registries, monkeypatch):
    """Unknown bshnr + no entities -> fall back to live name matching."""
    patch_registries["entities"] = []

    async def fake_list():
        return [("some_station", "Some Station", "Elbe")]

    monkeypatch.setattr(BshApi, "fetch_station_list", staticmethod(fake_list))

    hass = _Hass()
    entry = _Entry("999Z", "Some Station")

    assert await async_migrate_entry(hass, entry) is True
    assert entry.data["bshnr"] == "some_station"
    assert entry.version == 2


@pytest.mark.asyncio
async def test_migrate_deferred_when_list_unavailable(patch_registries, monkeypatch):
    """Transient network failure on the last-resort path -> retry later."""
    patch_registries["entities"] = []

    async def boom():
        raise RuntimeError("offline")

    monkeypatch.setattr(BshApi, "fetch_station_list", staticmethod(boom))

    hass = _Hass()
    entry = _Entry("999Z", "Unknown Station")

    assert await async_migrate_entry(hass, entry) is False
    assert entry.version == 1  # untouched
    assert hass.config_entries.updates == []


@pytest.mark.asyncio
async def test_migrate_fails_when_unresolvable(patch_registries, monkeypatch):
    """No entity, not in map, no name/slug match -> hard failure."""
    patch_registries["entities"] = []

    async def fake_list():
        return [("other", "Other", "Elbe")]

    monkeypatch.setattr(BshApi, "fetch_station_list", staticmethod(fake_list))

    hass = _Hass()
    entry = _Entry("999Z", "Nonexistent")

    assert await async_migrate_entry(hass, entry) is False
    assert entry.version == 1
    assert hass.config_entries.updates == []
