"""Config flow for the BSH Tides for Germany integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant

from .bsh_api import BshApi
from .const import DOMAIN
from .exceptions import BshCannotConnect, BshInvalidStation

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user selected an existing station."""
    _LOGGER.debug("Validating BSH station input: %s", data["bshnr"])
    api = BshApi(data["bshnr"])
    forecast_data = await api.async_fetch_data()
    _LOGGER.debug(
        "Validation successful for station: %s", forecast_data["station_name"]
    )
    return {"bshnr": data["bshnr"], "title": forecast_data["station_name"]}


class BshTidesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BSH Tides for Germany."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select the area (e.g. Elbe or Weser) so the 2nd step can filter the available stations."""
        _LOGGER.debug("Starting config flow: step_user")
        errors: dict[str, str] = {}

        if user_input is not None:
            self.area = user_input["area"]
            _LOGGER.debug("User selected area: %s", self.area)
            return await self.async_step_station()

        # Fetch the list of available stations from the BSH API
        try:
            self.station_map = await BshApi.fetch_station_list()
        except BshCannotConnect:
            _LOGGER.exception("Cannot connect to BSH API to fetch station list")
            errors["base"] = BshCannotConnect.code
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Required("area"): str}),
                errors=errors,
            )

        areas = sorted({area for _, _, area in self.station_map})
        _LOGGER.debug("Available areas: %s", areas)
        schema = vol.Schema({vol.Required("area"): vol.In(areas)})

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Use the area as a filter, then select the Gauge station in a drop down with key=bshnr and value=station_name."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(
                    self.hass, {"bshnr": user_input["Gauge Station"]}
                )
            except BshCannotConnect:
                _LOGGER.exception("Cannot connect to BSH API")
                errors["base"] = BshCannotConnect.code
            except BshInvalidStation:
                _LOGGER.exception("Invalid station data received")
                errors["base"] = BshInvalidStation.code
            except Exception:
                _LOGGER.exception("Unexpected exception during station validation")
                errors["base"] = "unknown"
            else:
                _LOGGER.info("Creating entry for station: %s", info["title"])
                return self.async_create_entry(
                    title=info["title"], data={"bshnr": user_input["Gauge Station"]}
                )

        # Create (bshnr: name) mapping for the dropdown. From the station map containung (bshnr, name, area) tuples
        # and filter for previously selected area
        options = {
            bshnr: name
            for bshnr, name, area in sorted(
                self.station_map,
                key=lambda item: item[1],  # sort by station_name
            )
            if area == self.area
        }
        _LOGGER.debug(
            "Station options for area %s: %s", self.area, list(options.values())
        )

        schema = vol.Schema({vol.Required("Gauge Station"): vol.In(options)})
        return self.async_show_form(
            step_id="station", data_schema=schema, errors=errors
        )
