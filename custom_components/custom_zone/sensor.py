"""Sensor platform for Custom Zone."""
from __future__ import annotations

import logging
import math
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_GPS_ACCURACY,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    CONF_COORDINATES,
    CONF_NAME,
    CONF_TRACKERS,
    COORD_TOLERANCE,
    DOMAIN,
    MIN_POLYGON_POINTS,
)

_LOGGER = logging.getLogger(__name__)

TRACKER_STATUS_INVALID_COORDINATES = "invalid_coordinates"
TRACKER_STATUS_NO_COORDINATES = "no_coordinates"
TRACKER_STATUS_TRACKED = "tracked"
TRACKER_STATUS_UNAVAILABLE = "unavailable"

TRACKER_CLASSIFICATION_COUNTED_IN_ZONE = "counted_in_zone"
TRACKER_CLASSIFICATION_COUNTED_OUT_OF_ZONE = "counted_out_of_zone"
TRACKER_CLASSIFICATION_UNUSABLE = "unusable"

DIAGNOSTIC_CONFIDENCE_DATA_INVALID = "confidence_data_invalid"
DIAGNOSTIC_CONFIDENCE_DATA_MISSING = "confidence_data_missing"
DIAGNOSTIC_CONFIDENCE_FAILURE = "confidence_failure"
DIAGNOSTIC_STALE_LOCATION = "stale_location"
DIAGNOSTIC_TRACKER_UNAVAILABLE = "tracker_unavailable"

CONFIDENCE_SAFETY_MARGIN_FACTOR = 0.75
STALE_LOCATION_THRESHOLD = timedelta(minutes=5)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Custom Zone sensor."""
    name = entry.data[CONF_NAME]
    trackers = entry.data.get(CONF_TRACKERS) or entry.data.get("device")
    if not trackers:
        _LOGGER.error("No trackers configured for Custom Zone %s", name)
        return

    if isinstance(trackers, str):
        trackers = [trackers]

    try:
        coords = _parse_polygon_coords(entry.data[CONF_COORDINATES])
    except (TypeError, ValueError) as err:
        _LOGGER.error("Invalid polygon data for Custom Zone %s: %s", name, err)
        return

    if len(coords) < MIN_POLYGON_POINTS:
        _LOGGER.error("Custom Zone %s has fewer than %s polygon points", name, MIN_POLYGON_POINTS)
        return

    _LOGGER.debug("Setting up Custom Zone: %s for trackers %s", name, trackers)
    async_add_entities([CustomZoneSensor(entry.entry_id, name, trackers, coords)], True)


def _parse_polygon_coords(raw_coords: Any) -> list[list[float]]:
    """Return polygon coordinates from structured stored data."""
    if not isinstance(raw_coords, list):
        raise TypeError("Polygon coordinates must be a list")

    normalized_coords: list[list[float]] = []
    for point in raw_coords:
        if not isinstance(point, list | tuple) or len(point) != 2:
            raise ValueError("Polygon points must be two-item coordinate pairs")

        try:
            latitude = float(point[0])
            longitude = float(point[1])
        except (TypeError, ValueError) as err:
            raise ValueError("Polygon points must contain numeric coordinates") from err

        if not -90 <= latitude <= 90:
            raise ValueError("Polygon latitude must be between -90 and 90")
        if not -180 <= longitude <= 180:
            raise ValueError("Polygon longitude must be between -180 and 180")

        normalized_coords.append([latitude, longitude])

    return normalized_coords


class CustomZoneSensor(SensorEntity):
    """Representation of a Custom Zone sensor."""

    def __init__(
        self,
        entry_id: str,
        name: str,
        tracker_entity_ids: list[str],
        polygon_coords: list[list[float]],
    ) -> None:
        """Initialize the sensor."""
        self._attr_name = name
        self._attr_should_poll = False
        self._attr_unique_id = entry_id
        self._tracker_entity_ids = list(tracker_entity_ids)
        self._polygon = polygon_coords
        self._trackers_inside: set[str] = set()
        self._is_available = False

        zone_slug = slugify(name)
        self.entity_id = f"sensor.customzone_{zone_slug}"

        self._tracker_data: dict[str, dict[str, Any]] = {
            entity_id: {
                "lat": None,
                "lon": None,
                "accuracy": None,
                "in_zone": None,
                "distance": None,
                "status": TRACKER_STATUS_UNAVAILABLE,
                "classification": TRACKER_CLASSIFICATION_UNUSABLE,
                "diagnostic_reason": DIAGNOSTIC_TRACKER_UNAVAILABLE,
                "counted_in_zone": None,
                "trusted_distance_m": None,
                "gps_accuracy_m": None,
            }
            for entity_id in self._tracker_entity_ids
        }

        self._attr_extra_state_attributes = {
            "trackers": self._tracker_entity_ids,
            "polygon": polygon_coords,
            "trackers_in_zone": [],
            "trackers_out_of_zone": [],
            "trackers_unusable": self._tracker_entity_ids.copy(),
            "count_in_zone": 0,
            "count_out_of_zone": 0,
            "count_unusable": len(self._tracker_entity_ids),
            "trackers_detail": {},
        }
        self._attr_icon = "mdi:map-marker-polygon"
        self._update_state_and_attributes()

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture to use in the frontend."""
        return f"/api/brand_icon/{DOMAIN}/icon.png"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if not self._is_available:
            return None

        count = len(self._trackers_inside)
        return f"{count} in zone"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._is_available

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug(
            "Custom Zone %s added to hass, tracking %s",
            self._attr_name,
            self._tracker_entity_ids,
        )
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                self._tracker_entity_ids,
                self._async_tracker_changed,
            )
        )
        for entity_id in self._tracker_entity_ids:
            current_state = self.hass.states.get(entity_id)
            if current_state is not None:
                self._handle_tracker_state_update(entity_id, current_state, fire_update=False)

        self._update_state_and_attributes()

    @callback
    def _async_tracker_changed(self, event) -> None:
        """Handle tracker state changes."""
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        self._handle_tracker_state_update(entity_id, new_state)

    def _mark_tracker_unusable(
        self,
        entity_id: str,
        *,
        status: str,
        diagnostic_reason: str,
        gps_accuracy_m: float | None = None,
    ) -> None:
        """Store an unusable tracker state with its diagnostic reason."""
        self._trackers_inside.discard(entity_id)
        self._tracker_data[entity_id].update(
            {
                "lat": None,
                "lon": None,
                "accuracy": gps_accuracy_m,
                "in_zone": None,
                "distance": None,
                "status": status,
                "classification": TRACKER_CLASSIFICATION_UNUSABLE,
                "diagnostic_reason": diagnostic_reason,
                "counted_in_zone": None,
                "trusted_distance_m": None,
                "gps_accuracy_m": gps_accuracy_m,
            }
        )

    def _handle_tracker_state_update(
        self,
        entity_id: str,
        new_state: Any,
        fire_update: bool = True,
    ) -> None:
        """Handle tracker state updates."""
        if entity_id not in self._tracker_data:
            return

        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            _LOGGER.debug("Tracker %s is unavailable or unknown", entity_id)
            self._mark_tracker_unusable(
                entity_id,
                status=TRACKER_STATUS_UNAVAILABLE,
                diagnostic_reason=DIAGNOSTIC_TRACKER_UNAVAILABLE,
            )
            if fire_update:
                self._update_state_and_attributes()
                self.async_write_ha_state()
            return

        lat = new_state.attributes.get(ATTR_LATITUDE)
        lon = new_state.attributes.get(ATTR_LONGITUDE)
        accuracy = new_state.attributes.get(ATTR_GPS_ACCURACY)

        if lat is None or lon is None:
            _LOGGER.debug("Tracker %s has no coordinates", entity_id)
            self._mark_tracker_unusable(
                entity_id,
                status=TRACKER_STATUS_NO_COORDINATES,
                diagnostic_reason=DIAGNOSTIC_CONFIDENCE_DATA_MISSING,
            )
            if fire_update:
                self._update_state_and_attributes()
                self.async_write_ha_state()
            return

        try:
            latitude = float(lat)
            longitude = float(lon)
        except (TypeError, ValueError):
            _LOGGER.warning("Invalid coordinates for tracker %s", entity_id)
            self._mark_tracker_unusable(
                entity_id,
                status=TRACKER_STATUS_INVALID_COORDINATES,
                diagnostic_reason=DIAGNOSTIC_CONFIDENCE_DATA_INVALID,
            )
            if fire_update:
                self._update_state_and_attributes()
                self.async_write_ha_state()
            return

        if self._is_stale(new_state):
            stale_accuracy_m, _ = self._parse_accuracy_meters(accuracy)
            self._mark_tracker_unusable(
                entity_id,
                status=DIAGNOSTIC_STALE_LOCATION,
                diagnostic_reason=DIAGNOSTIC_STALE_LOCATION,
                gps_accuracy_m=stale_accuracy_m,
            )
            if fire_update:
                self._update_state_and_attributes()
                self.async_write_ha_state()
            return

        accuracy_m, accuracy_reason = self._parse_accuracy_meters(accuracy)
        if accuracy_reason is not None:
            self._mark_tracker_unusable(
                entity_id,
                status=accuracy_reason,
                diagnostic_reason=accuracy_reason,
            )
            if fire_update:
                self._update_state_and_attributes()
                self.async_write_ha_state()
            return

        is_inside = self._point_in_polygon(latitude, longitude)
        boundary_distance_m = self._distance_to_polygon_meters(latitude, longitude)
        trusted_distance_m = round(boundary_distance_m, 2) if boundary_distance_m is not None else None
        confidence_limit_m = boundary_distance_m * CONFIDENCE_SAFETY_MARGIN_FACTOR

        if accuracy_m is None or boundary_distance_m is None or accuracy_m > confidence_limit_m:
            self._mark_tracker_unusable(
                entity_id,
                status=DIAGNOSTIC_CONFIDENCE_FAILURE,
                diagnostic_reason=DIAGNOSTIC_CONFIDENCE_FAILURE,
                gps_accuracy_m=accuracy_m,
            )
            if fire_update:
                self._update_state_and_attributes()
                self.async_write_ha_state()
            return

        classification = (
            TRACKER_CLASSIFICATION_COUNTED_IN_ZONE
            if is_inside
            else TRACKER_CLASSIFICATION_COUNTED_OUT_OF_ZONE
        )

        self._tracker_data[entity_id].update(
            {
                "lat": latitude,
                "lon": longitude,
                "accuracy": accuracy_m,
                "in_zone": is_inside,
                "distance": trusted_distance_m,
                "status": TRACKER_STATUS_TRACKED,
                "classification": classification,
                "diagnostic_reason": None,
                "counted_in_zone": is_inside,
                "trusted_distance_m": trusted_distance_m,
                "gps_accuracy_m": accuracy_m,
            }
        )

        if is_inside:
            self._trackers_inside.add(entity_id)
        else:
            self._trackers_inside.discard(entity_id)

        if fire_update:
            self._update_state_and_attributes()
            self.async_write_ha_state()

    def _update_state_and_attributes(self) -> None:
        """Update the sensor attributes based on current tracker data."""
        in_zone = sorted(
            entity_id
            for entity_id, data in self._tracker_data.items()
            if data["classification"] == TRACKER_CLASSIFICATION_COUNTED_IN_ZONE
        )
        out_zone = sorted(
            entity_id
            for entity_id, data in self._tracker_data.items()
            if data["classification"] == TRACKER_CLASSIFICATION_COUNTED_OUT_OF_ZONE
        )
        unavailable = sorted(
            entity_id
            for entity_id, data in self._tracker_data.items()
            if data["classification"] == TRACKER_CLASSIFICATION_UNUSABLE
        )

        self._trackers_inside = set(in_zone)
        self._is_available = True
        trackers_detail = {
            entity_id: {
                "classification": data["classification"],
                "diagnostic_reason": data["diagnostic_reason"],
                "counted_in_zone": data["counted_in_zone"],
                "trusted_distance_m": data["trusted_distance_m"],
                "gps_accuracy_m": data["gps_accuracy_m"],
            }
            for entity_id, data in self._tracker_data.items()
        }

        self._attr_extra_state_attributes.update(
            {
                "trackers_in_zone": in_zone,
                "trackers_out_of_zone": out_zone,
                "trackers_unusable": unavailable,
                "count_in_zone": len(in_zone),
                "count_out_of_zone": len(out_zone),
                "count_unusable": len(unavailable),
                "trackers_detail": trackers_detail,
            }
        )

    def _point_in_polygon(self, lat, lon):
        """Check if point (lat, lon) is inside the polygon."""
        # Ray casting expects x=longitude, y=latitude. Polygon points are stored as [lat, lon].
        x = lon
        y = lat
        poly = self._polygon
        n = len(poly)

        for i in range(n):
            p1 = poly[i]
            p2 = poly[(i + 1) % n]
            p1x, p1y = p1[1], p1[0]
            p2x, p2y = p2[1], p2[0]

            # Vertex check
            if abs(p1x - x) < COORD_TOLERANCE and abs(p1y - y) < COORD_TOLERANCE:
                return True

            # Boundary check
            if x >= min(p1x, p2x) - COORD_TOLERANCE and x <= max(p1x, p2x) + COORD_TOLERANCE and \
               y >= min(p1y, p2y) - COORD_TOLERANCE and y <= max(p1y, p2y) + COORD_TOLERANCE:
                 # Collinear check
                 cross = (y - p1y) * (p2x - p1x) - (p2y - p1y) * (x - p1x)
                 if abs(cross) < COORD_TOLERANCE:
                     return True

        inside = False
        p1x, p1y = poly[-1][1], poly[-1][0]
        for i in range(n):
            p2x, p2y = poly[i][1], poly[i][0]

            # Ray casting algorithm
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xints:
                                inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def _parse_accuracy_meters(self, accuracy):
        """Return parsed accuracy meters and a diagnostic reason when unusable."""
        if accuracy is None:
            return None, DIAGNOSTIC_CONFIDENCE_DATA_MISSING
        try:
            accuracy_m = float(accuracy)
        except (TypeError, ValueError):
            return None, DIAGNOSTIC_CONFIDENCE_DATA_INVALID
        if accuracy_m <= 0:
            return None, DIAGNOSTIC_CONFIDENCE_DATA_INVALID
        return accuracy_m, None

    def _is_stale(self, state: Any) -> bool:
        """Return True when the tracker location is older than the staleness threshold."""
        last_updated = getattr(state, "last_updated", None)
        if last_updated is None:
            return False

        now = dt_util.utcnow()
        return now - last_updated > STALE_LOCATION_THRESHOLD

    def _distance_to_polygon_meters(self, lat, lon):
        """Return minimum distance in meters from point to polygon boundary."""
        # Approximate degrees to meters at the current latitude.
        lat_rad = math.radians(lat)
        meters_per_deg_lat = 111_320.0
        meters_per_deg_lon = meters_per_deg_lat * math.cos(lat_rad)

        def to_xy(p_lat, p_lon):
            return (
                (p_lon - lon) * meters_per_deg_lon,
                (p_lat - lat) * meters_per_deg_lat,
            )

        min_distance = None
        n = len(self._polygon)
        for i in range(n):
            p1_lat, p1_lon = self._polygon[i]
            p2_lat, p2_lon = self._polygon[(i + 1) % n]
            x1, y1 = to_xy(p1_lat, p1_lon)
            x2, y2 = to_xy(p2_lat, p2_lon)
            dx = x2 - x1
            dy = y2 - y1
            if dx == 0 and dy == 0:
                distance = math.hypot(x1, y1)
            else:
                t = (-(x1 * dx) - (y1 * dy)) / (dx * dx + dy * dy)
                t = max(0.0, min(1.0, t))
                proj_x = x1 + t * dx
                proj_y = y1 + t * dy
                distance = math.hypot(proj_x, proj_y)
            if min_distance is None or distance < min_distance:
                min_distance = distance

        return min_distance if min_distance is not None else 0.0
