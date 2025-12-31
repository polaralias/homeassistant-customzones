"""Config flow for Custom Zone integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_DEVICE, CONF_COORDINATES, CONF_ZONE_TYPE, ZONE_TYPE_POLYGON

_LOGGER = logging.getLogger(__name__)

class CustomZoneConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Custom Zone."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate coordinates
                coords_str = user_input[CONF_COORDINATES]
                try:
                    coords = json.loads(coords_str)
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON format")

                if not isinstance(coords, list):
                    raise ValueError("Coordinates must be a list")

                if len(coords) < 3:
                     raise ValueError("Polygon must have at least 3 points")

                for point in coords:
                    if not isinstance(point, list) or len(point) != 2:
                        raise ValueError("Each point must be a list of [lat, lon]")
                    # Check if they are numbers
                    float(point[0])
                    float(point[1])

                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
            except ValueError:
                errors[CONF_COORDINATES] = "invalid_format"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): selector.TextSelector(),
                    vol.Required(CONF_DEVICE): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="device_tracker")
                    ),
                    vol.Required(CONF_ZONE_TYPE, default=ZONE_TYPE_POLYGON): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[ZONE_TYPE_POLYGON],
                            mode=selector.SelectSelectorMode.DROPDOWN
                        )
                    ),
                    vol.Required(CONF_COORDINATES): selector.TextSelector(
                        selector.TextSelectorConfig(multiline=True)
                    ),
                }
            ),
            errors=errors,
        )
