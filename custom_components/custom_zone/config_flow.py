"""Config flow for Custom Zone integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_DEVICE, CONF_COORDINATES, CONF_ZONE_TYPE, ZONE_TYPE_POLYGON

_LOGGER = logging.getLogger(__name__)

class CustomZoneConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Custom Zone."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        super().__init__()
        self._data = {}
        self._points = []

    def _ordinal(self, n):
        """Return ordinal string for integer n."""
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    def _get_shape_description(self, n):
        """Return a string describing the shape based on number of points."""
        if n < 3:
            return "Not a polygon yet"
        if n == 3:
            return "Triangle"
        if n == 4:
            # We could check for rectangle here if we had the points,
            # but for now just count vertices.
            return "Quadrilateral (e.g. Rectangle)"
        if n == 5:
            return "Pentagon"
        if n == 6:
            return "Hexagon"
        if n == 7:
            return "Heptagon"
        if n == 8:
            return "Octagon"
        return f"{n}-sided polygon"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data = user_input
            self._points = []  # Reset points
            return await self.async_step_point()

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
                }
            ),
            errors=errors,
        )

    async def async_step_point(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle adding a point."""
        errors: dict[str, str] = {}

        # Process input from previous submission
        if user_input is not None:
            lat = user_input.get(CONF_LATITUDE)
            lon = user_input.get(CONF_LONGITUDE)
            finished = user_input.get("finished", False)

            # Validate lat/lon just in case
            try:
                point = [float(lat), float(lon)]
                self._points.append(point)
            except (ValueError, TypeError):
                errors["base"] = "invalid_coord"

            if not errors:
                if len(self._points) >= 15:
                    finished = True

                if finished:
                    if len(self._points) < 3:
                        errors["base"] = "not_enough_points"
                        # Start over? Or just show error and keep points?
                        # Showing error will re-show form.
                    else:
                        # Success
                        self._data[CONF_COORDINATES] = json.dumps(self._points)
                        return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)

        # Check if we hit limit after error or normal flow
        # If we have 15 points, we shouldn't ask for a 16th.
        # But the loop above handles adding.
        # If we are here, we are about to ask for point N+1.
        # If N=15, we can't ask for more.

        current_count = len(self._points)
        if current_count >= 15:
             # This case should be handled by the 'finished' logic above unless user manually manipulated requests.
             # Force finish if somehow we are here.
             if current_count >= 3:
                 self._data[CONF_COORDINATES] = json.dumps(self._points)
                 return self.async_create_entry(title=self._data[CONF_NAME], data=self._data)
             else:
                 errors["base"] = "not_enough_points"

        next_point_idx = current_count + 1

        status_msg = f"{current_count} points entered, enter a {self._ordinal(next_point_idx)}"
        shape_desc = self._get_shape_description(current_count) # Shape BEFORE adding this point?
        # Requirement: "explain the resulting shape mapped"
        # If they have 3 points, they have a triangle.
        # If they add a 4th, it becomes a Quad.
        # The prompt says: "2 points entered, enter a 3rd"
        # And "a 4 point rectangle has been created".
        # So maybe we should describe the shape formed by the *currently entered* points.

        schema = {
            vol.Required(CONF_LATITUDE): float,
            vol.Required(CONF_LONGITUDE): float,
        }

        # Only show "Finish" option if we have at least 2 points (so this will be the 3rd)
        # Or maybe allow finishing anytime but error if < 3?
        # Better to only show "Finish" if current_count >= 2.
        # Actually, user might want to stop early? No, min 3.

        if current_count >= 2:
             schema[vol.Optional("finished", default=False)] = bool

        return self.async_show_form(
            step_id="point",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={
                "status_msg": status_msg,
                "shape_desc": shape_desc
            }
        )
