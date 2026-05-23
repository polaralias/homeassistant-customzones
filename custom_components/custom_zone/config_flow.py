"""Config flow for Custom Zone integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CONF_COORDINATES,
    CONF_TRACKERS,
    CONF_ZONE_TYPE,
    DOMAIN,
    MIN_POLYGON_POINTS,
    ZONE_TYPE_POLYGON,
)

CONF_POLYGON_EDIT_MODE = "polygon_edit_mode"
POLYGON_EDIT_MODE_APPEND = "append"
POLYGON_EDIT_MODE_KEEP = "keep"
POLYGON_EDIT_MODE_REMOVE_LAST = "remove_last"
POLYGON_EDIT_MODE_REPLACE = "replace"


class _PolygonFlowMixin:
    """Shared polygon-validation behavior for create and edit flows."""

    _points: list[list[float]]

    def _validate_name(self, name: Any) -> str | None:
        """Return a normalized zone name or None when invalid."""
        if not isinstance(name, str):
            return None

        normalized_name = name.strip()
        if not normalized_name:
            return None

        return normalized_name

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

    def _validate_polygon(self, points: list[list[float]]) -> str | None:
        """Return a base-form error key when the polygon is invalid."""
        unique_points = {(lat, lon) for lat, lon in points}
        if len(unique_points) < MIN_POLYGON_POINTS:
            return "not_enough_points"

        if len(unique_points) != len(points):
            return "repeated_points"

        if self._has_self_intersection(points):
            return "self_intersection"

        return None

    def _has_self_intersection(self, points: list[list[float]]) -> bool:
        """Return True when non-adjacent polygon edges intersect."""
        edge_count = len(points)
        for start_index in range(edge_count):
            first_start = points[start_index]
            first_end = points[(start_index + 1) % edge_count]
            for compare_index in range(start_index + 1, edge_count):
                if compare_index in (start_index, start_index + 1):
                    continue
                if start_index == 0 and compare_index == edge_count - 1:
                    continue

                second_start = points[compare_index]
                second_end = points[(compare_index + 1) % edge_count]
                if self._segments_intersect(first_start, first_end, second_start, second_end):
                    return True

        return False

    def _segments_intersect(
        self,
        first_start: list[float],
        first_end: list[float],
        second_start: list[float],
        second_end: list[float],
    ) -> bool:
        """Return True when two closed line segments intersect."""

        def orientation(point_a: list[float], point_b: list[float], point_c: list[float]) -> int:
            cross = (
                (point_b[1] - point_a[1]) * (point_c[0] - point_b[0])
                - (point_b[0] - point_a[0]) * (point_c[1] - point_b[1])
            )
            if cross == 0:
                return 0
            return 1 if cross > 0 else 2

        def on_segment(point_a: list[float], point_b: list[float], point_c: list[float]) -> bool:
            return (
                min(point_a[0], point_c[0]) <= point_b[0] <= max(point_a[0], point_c[0])
                and min(point_a[1], point_c[1]) <= point_b[1] <= max(point_a[1], point_c[1])
            )

        first = orientation(first_start, first_end, second_start)
        second = orientation(first_start, first_end, second_end)
        third = orientation(second_start, second_end, first_start)
        fourth = orientation(second_start, second_end, first_end)

        if first != second and third != fourth:
            return True

        if first == 0 and on_segment(first_start, second_start, first_end):
            return True
        if second == 0 and on_segment(first_start, second_end, first_end):
            return True
        if third == 0 and on_segment(second_start, first_start, second_end):
            return True
        if fourth == 0 and on_segment(second_start, first_end, second_end):
            return True

        return False

    def _build_point_schema(self) -> vol.Schema:
        """Return the point-entry schema."""
        current_count = len(self._points)
        schema: dict[vol.Marker, object] = {
            vol.Required(CONF_LATITUDE): float,
            vol.Required(CONF_LONGITUDE): float,
        }
        if current_count >= MIN_POLYGON_POINTS - 1:
            schema[vol.Optional("finished", default=False)] = bool
        return vol.Schema(schema)


class CustomZoneConfigFlow(_PolygonFlowMixin, config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Custom Zone."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._data: dict[str, Any] = {}
        self._points: list[list[float]] = []

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> config_entries.OptionsFlow:
        """Return the options flow for this config entry."""
        return CustomZoneOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized_name = self._validate_name(user_input.get(CONF_NAME))
            trackers = user_input.get(CONF_TRACKERS, [])
            if normalized_name is None:
                errors[CONF_NAME] = "empty_name"
            elif not trackers:
                errors[CONF_TRACKERS] = "empty_trackers"
            else:
                user_input = dict(user_input)
                user_input[CONF_NAME] = normalized_name
                await self.async_set_unique_id(slugify(user_input[CONF_NAME]))
                self._abort_if_unique_id_configured()
                self._data = user_input
                self._points = []
                return await self.async_step_point()

        return self.async_show_form(
            step_id="user",
            data_schema=_build_identity_schema(),
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

            if not errors and finished:
                polygon_error = self._validate_polygon(self._points)
                if polygon_error is not None:
                    errors["base"] = polygon_error
                else:
                    self._data[CONF_COORDINATES] = list(self._points)
                    return self.async_create_entry(
                        title=self._data[CONF_NAME],
                        data=self._data,
                    )

        current_count = len(self._points)
        return self.async_show_form(
            step_id="point",
            data_schema=self._build_point_schema(),
            errors=errors,
            description_placeholders={
                "status_msg": f"Point {current_count + 1}",
                "shape_desc": self._get_shape_description(current_count),
            },
        )


class CustomZoneOptionsFlow(_PolygonFlowMixin, config_entries.OptionsFlow):
    """Handle edits for an existing Custom Zone entry."""

    def __init__(self) -> None:
        """Initialize the options flow."""
        self._data: dict[str, Any] = {}
        self._points: list[list[float]] = []

    async def _finish_update(self) -> config_entries.FlowResult:
        """Persist the updated config entry and reload it."""
        updated_data = dict(self._data)
        updated_data.pop(CONF_POLYGON_EDIT_MODE, None)
        updated_data[CONF_COORDINATES] = list(self._points)
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            title=updated_data[CONF_NAME],
            data=updated_data,
        )
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)
        return self.async_create_entry(title="", data={})

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial edit step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized_name = self._validate_name(user_input.get(CONF_NAME))
            trackers = user_input.get(CONF_TRACKERS, [])
            if normalized_name is None:
                errors[CONF_NAME] = "empty_name"
            elif not trackers:
                errors[CONF_TRACKERS] = "empty_trackers"
            elif self._name_conflicts(normalized_name):
                errors[CONF_NAME] = "already_configured"
            else:
                user_input = dict(user_input)
                user_input[CONF_NAME] = normalized_name
                self._data = user_input
                polygon_edit_mode = user_input.get(CONF_POLYGON_EDIT_MODE, POLYGON_EDIT_MODE_REPLACE)

                existing_points = [list(point) for point in self.config_entry.data[CONF_COORDINATES]]
                if polygon_edit_mode == POLYGON_EDIT_MODE_KEEP:
                    self._points = existing_points
                    return await self._finish_update()
                if polygon_edit_mode == POLYGON_EDIT_MODE_APPEND:
                    self._points = existing_points
                    return await self.async_step_point()
                if polygon_edit_mode == POLYGON_EDIT_MODE_REMOVE_LAST:
                    self._points = existing_points[:-1]
                    return await self.async_step_point()

                self._points = []
                return await self.async_step_point()

        return self.async_show_form(
            step_id="init",
            data_schema=_build_identity_schema(
                name_default=self.config_entry.data[CONF_NAME],
                trackers_default=self.config_entry.data[CONF_TRACKERS],
                zone_type_default=self.config_entry.data[CONF_ZONE_TYPE],
                polygon_edit_mode_default=POLYGON_EDIT_MODE_KEEP,
                include_polygon_edit_mode=True,
            ),
            errors=errors,
            description_placeholders={
                "current_name": str(self.config_entry.data[CONF_NAME]),
                "current_tracker_count": str(len(self.config_entry.data[CONF_TRACKERS])),
                "current_point_count": str(len(self.config_entry.data[CONF_COORDINATES])),
            },
        )

    async def async_step_point(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle polygon editing after the chosen edit mode is applied."""
        errors: dict[str, str] = {}

        if user_input is not None:
            finished = user_input.get("finished", False)
            errors, point = self._validate_point(
                user_input.get(CONF_LATITUDE),
                user_input.get(CONF_LONGITUDE),
            )
            if not errors and point is not None:
                self._points.append(point)

            if not errors and finished:
                polygon_error = self._validate_polygon(self._points)
                if polygon_error is not None:
                    errors["base"] = polygon_error
                else:
                    return await self._finish_update()

        current_count = len(self._points)
        return self.async_show_form(
            step_id="point",
            data_schema=self._build_point_schema(),
            errors=errors,
            description_placeholders={
                "status_msg": f"Point {current_count + 1}",
                "shape_desc": self._get_shape_description(current_count),
                "existing_point_count": str(len(self.config_entry.data[CONF_COORDINATES])),
            },
        )

    def _name_conflicts(self, candidate_name: str) -> bool:
        """Return True when another zone already uses this name."""
        candidate_slug = slugify(candidate_name)
        current_slug = slugify(self.config_entry.data[CONF_NAME])
        if candidate_slug == current_slug:
            return False

        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.entry_id == self.config_entry.entry_id:
                continue
            if slugify(entry.data.get(CONF_NAME, "")) == candidate_slug:
                return True

        return False


def _build_identity_schema(
    *,
    name_default: str | None = None,
    trackers_default: list[str] | None = None,
    zone_type_default: str = ZONE_TYPE_POLYGON,
    polygon_edit_mode_default: str = POLYGON_EDIT_MODE_REPLACE,
    include_polygon_edit_mode: bool = False,
) -> vol.Schema:
    """Return the shared identity/trackers schema for create and edit flows."""
    schema: dict[vol.Marker, object] = {
        vol.Required(CONF_NAME, default=name_default): selector.TextSelector(),
        vol.Required(CONF_TRACKERS, default=trackers_default): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain=["device_tracker", "person"],
                multiple=True,
            )
        ),
        vol.Required(CONF_ZONE_TYPE, default=zone_type_default): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[ZONE_TYPE_POLYGON],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }
    if include_polygon_edit_mode:
        schema[vol.Required(
            CONF_POLYGON_EDIT_MODE,
            default=polygon_edit_mode_default,
        )] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(
                        value=POLYGON_EDIT_MODE_KEEP,
                        label="Keep existing polygon",
                    ),
                    selector.SelectOptionDict(
                        value=POLYGON_EDIT_MODE_APPEND,
                        label="Append more points",
                    ),
                    selector.SelectOptionDict(
                        value=POLYGON_EDIT_MODE_REMOVE_LAST,
                        label="Remove last point and continue",
                    ),
                    selector.SelectOptionDict(
                        value=POLYGON_EDIT_MODE_REPLACE,
                        label="Replace all points",
                    ),
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
    return vol.Schema(schema)
