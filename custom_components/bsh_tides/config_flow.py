"""Config flow for the BSH Tides for Germany integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .bsh_api import BshApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)



async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user selected an existing station."""

    # Check for bshnr being valid by contacting BSH endpoint
    try:
        api = BshApi(data["bshnr"])
        data = await api.async_fetch_data()  # result is returned for valid bshnr
    except Exception as e:
        _LOGGER.error(
            "Exception trying to connect BSH API for bshnr %s: %s", data["bshnr"], e
        )
        raise CannotConnect

    # Method returns the values that are being stored for the integration
    return {"bshnr": data["bshnr"], "title": data["station_name"]}


class BshTidesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BSH Tides for Germany."""

    VERSION = 1

    async def async_step_user(        
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """The initial step of the config flow is to select the area (e.g. Elbe or Weser) so the 2nd step can filter the available stations."""

        if user_input is not None:
            self.area = user_input["area"]
            return await self.async_step_station()

        self.station_map = await BshApi.fetch_station_list()
        areas = sorted(set(area for _, _, area in self.station_map))
        schema = vol.Schema({vol.Required("area"): vol.In(areas)})

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """The area is used as filter, now select the Gauge station in a drop down with key=bshnr and value=station_name."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(
                    self.hass, {"bshnr": user_input["Gauge Station"]}
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"], data={"bshnr": user_input["Gauge Station"]}
                )

        # Create (bshnr: name) mapping for the dropdown. From the station map containung (bshnr, name, area) tuples
        # and filter for previously selected area
        options = {
            bshnr: name for bshnr, name, area in self.station_map if area == self.area
        }

        schema = vol.Schema({vol.Required("Gauge Station"): vol.In(options)})
        return self.async_show_form(
            step_id="station", data_schema=schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
