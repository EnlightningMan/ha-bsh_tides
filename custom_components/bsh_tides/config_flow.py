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

# Required input is the "Pegel-Nr." / "bshnr" from https://wasserstand-nordsee.bsh.de/
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            "bshnr"
        ): str,  # BshNr is the BSH number for the tide station. E.g. DE__714P for Schulau
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    # Check for bshnr being valid by contacting BSH endpoint
    try:
        api = BshApi(data["bshnr"])
        data = await api.async_fetch_data()  # result is returned for valid bshnr
    except Exception as e:
        _LOGGER.error(
            "Exception trying to connect BSH API for bshnr %s: %s", data["bshnr"], e
        )
        raise CannotConnect

    # TODO
    # Erfolgreiche Validierung, gib die zu speichernden Daten zurück
    return {"bshnr": data["bshnr"], "title": data["station_name"]}


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BSH Tides for Germany."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
