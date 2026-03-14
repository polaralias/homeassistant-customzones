"""Config flow for Custom Zone integration."""
from __future__ import annotations

import json
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CONF_COORDINATES,
    CONF_MAX_TRACKERS,
    CONF_TRACKERS,
    CONF_ZONE_TYPE,
    DOMAIN,
    MAX_POLYGON_POINTS,
    MIN_POLYGON_POINTS,
    ZONE_TYPE_POLYGON,
)


class CustomZoneConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Custom Zone."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._data: dict[str, Any] = {}
        self._points: list[list[float]] = []

    def _get_shape_description(self, point_count: int) -> str:
        """Return a string describing the shape based on number of points."""
        if point_count < MIN_POLYGON_POINTS:
            return "Not a polygon yet"
        if point_count == 3:
            return "Triangle"
        if point_count == 4:
            return "Quadrilateral (e.g. Rectangle)"
        if point_count == 5:
            return "Pentagon"
        if point_count == 6:
            return "Hexagon"
        if point_count == 7:
            return "Heptagon"
        if point_count == 8:
            return "Octagon"
        return f"{point_count}-sided polygon"

    def _validate_point(
        self, latitude: Any, longitude: Any
    ) -> tuple[dict[str, str], list[float] | None]:
        """Validate a polygon point."""
        errors: dict[str, str] = {}

        try:
            lat = float(latitude)
        except (TypeError, ValueError):
            errors[CONF_LATITUDE] = "invalid_latitude"
        else:
            if not -90 <= lat <= 90:
                errors[CONF_LATITUDE] = "invalid_latitude"

        try:
            lon = float(longitude)
        except (TypeError, ValueError):
            errors[CONF_LONGITUDE] = "invalid_longitude"
        else:
            if not -180 <= lon <= 180:
                errors[CONF_LONGITUDE] = "invalid_longitude"

        if errors:
            return errors, None

        return errors, [lat, lon]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            trackers = user_input.get(CONF_TRACKERS, [])
            if len(trackers) > CONF_MAX_TRACKERS:
                errors["base"] = "too_many_trackers"
            elif not trackers:
                errors[CONF_TRACKERS] = "empty_trackers"
            else:
                await self.async_set_unique_id(slugify(user_input[CONF_NAME]))
                self._abort_if_unique_id_configured()
                self._data = user_input
                self._points = []
                return await self.async_step_point()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): selector.TextSelector(),
                    vol.Required(CONF_TRACKERS): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["device_tracker", "person"],
                            multiple=True,
                        )
                    ),
                    vol.Required(
                        CONF_ZONE_TYPE, default=ZONE_TYPE_POLYGON
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[ZONE_TYPE_POLYGON],
                            mode=selector.SelectSelectorMode.DROPDOWN,
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

        if user_input is not None:
            finished = user_input.get("finished", False)
            errors, point = self._validate_point(
                user_input.get(CONF_LATITUDE),
                user_input.get(CONF_LONGITUDE),
            )
            if not errors and point is not None:
                self._points.append(point)

            if not errors:
                if len(self._points) >= MAX_POLYGON_POINTS:
                    finished = True

                if finished:
                    if len(self._points) < MIN_POLYGON_POINTS:
                        errors["base"] = "not_enough_points"
                    else:
                        self._data[CONF_COORDINATES] = json.dumps(self._points)
                        return self.async_create_entry(
                            title=self._data[CONF_NAME],
                            data=self._data,
                        )

        current_count = len(self._points)
        if current_count >= MAX_POLYGON_POINTS:
            self._data[CONF_COORDINATES] = json.dumps(self._points)
            return self.async_create_entry(
                title=self._data[CONF_NAME],
                data=self._data,
            )

        schema: dict[vol.Marker, object] = {
            vol.Required(CONF_LATITUDE): float,
            vol.Required(CONF_LONGITUDE): float,
        }
        if current_count >= MIN_POLYGON_POINTS - 1:
            schema[vol.Optional("finished", default=False)] = bool

        return self.async_show_form(
            step_id="point",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={
                "status_msg": f"Point {current_count + 1}/{MAX_POLYGON_POINTS}",
                "shape_desc": self._get_shape_description(current_count),
            },
        )
