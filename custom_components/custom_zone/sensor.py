"""Sensor platform for Custom Zone."""
from __future__ import annotations

import json
import logging
import math

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, STATE_UNAVAILABLE, STATE_UNKNOWN, ATTR_GPS_ACCURACY
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify

from .const import DOMAIN, CONF_DEVICE, CONF_NAME, CONF_COORDINATES, COORD_TOLERANCE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Custom Zone sensor."""
    name = entry.data[CONF_NAME]
    device = entry.data[CONF_DEVICE]
    coords = json.loads(entry.data[CONF_COORDINATES])

    _LOGGER.debug("Setting up Custom Zone: %s for device %s", name, device)
    async_add_entities([CustomZoneSensor(name, device, coords)], True)


class CustomZoneSensor(SensorEntity):
    """Representation of a Custom Zone sensor."""

    def __init__(self, name, device_entity_id, polygon_coords):
        """Initialize the sensor."""
        self._attr_name = name
        self._device_entity_id = device_entity_id
        self._polygon = polygon_coords
        self._is_inside = False
        self._is_available = True

        # Requirement: "sensor.customzone_james_work"
        # Since we are in the sensor platform, the domain will be 'sensor'.
        # However, we can construct the object_id to match the requirement.
        # entity_id format: <domain>.<object_id>
        # We want object_id to be: customzone_{person}_{zone}
        
        # Extract the device identifier from the device_entity_id
        # For device_tracker.james -> "james"
        device_parts = device_entity_id.split(".")
        device_identifier = device_parts[-1] if len(device_parts) > 1 else device_entity_id
        person_slug = slugify(device_identifier)
        zone_slug = slugify(name)
        self.entity_id = f"sensor.customzone_{person_slug}_{zone_slug}"

        self._attr_unique_id = f"{name}_{device_entity_id}_custom_zone"
        self._current_lat = None
        self._current_lon = None
        self._attr_extra_state_attributes = {
            "device": device_entity_id,
            "polygon": polygon_coords,
            "triggering_latitude": self._current_lat,
            "triggering_longitude": self._current_lon,
            "gps_accuracy": None,
            "boundary_distance_m": None,
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return "In zone" if self._is_inside else "Not in zone"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._is_available

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        _LOGGER.debug("Custom Zone %s added to hass, tracking %s", self._attr_name, self._device_entity_id)
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._device_entity_id], self._async_device_changed
            )
        )
        current_state = self.hass.states.get(self._device_entity_id)
        if current_state is not None:
            self._handle_state_update(current_state)

    @callback
    def _async_device_changed(self, event) -> None:
        """Handle device state changes."""
        new_state = event.data.get("new_state")
        self._handle_state_update(new_state)

    def _handle_state_update(self, new_state) -> None:
        """Handle device state updates."""
        was_available = self._is_available

        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            _LOGGER.debug("Device %s is unavailable or unknown", self._device_entity_id)
            if self._is_available:
                self._is_available = False
                self.async_write_ha_state()
            return

        lat = new_state.attributes.get(ATTR_LATITUDE)
        lon = new_state.attributes.get(ATTR_LONGITUDE)

        accuracy = new_state.attributes.get(ATTR_GPS_ACCURACY)

        if lat is None or lon is None:
            _LOGGER.debug("Device %s has no coordinates", self._device_entity_id)
            if self._is_available:
                self._is_available = False
                self.async_write_ha_state()
            return

        # Restore availability if we have valid coordinates
        self._is_available = True

        _LOGGER.debug("Device %s at %s, %s (Accuracy: %s). Checking zone %s",
                      self._device_entity_id, lat, lon, accuracy, self._attr_name)

        try:
            lat = float(lat)
            lon = float(lon)

            # Check if coordinates changed
            coords_changed = self._current_lat != lat or self._current_lon != lon
            self._current_lat = lat
            self._current_lon = lon

            is_inside = self._point_in_polygon(lat, lon)
            accuracy_m = self._parse_accuracy_meters(accuracy)
            boundary_distance_m = self._distance_to_polygon_meters(lat, lon)

            # Update attributes with triggering coordinates
            self._attr_extra_state_attributes.update({
                "triggering_latitude": self._current_lat,
                "triggering_longitude": self._current_lon,
                "gps_accuracy": accuracy_m,
                "boundary_distance_m": round(boundary_distance_m, 2) if boundary_distance_m is not None else None,
            })

            if is_inside:
                _LOGGER.debug("Inside the Poly Zone: %s", self._attr_name)
            else:
                _LOGGER.debug("Outside the Poly Zone: %s", self._attr_name)

            if self._is_inside != is_inside:
                self._is_inside = is_inside
                _LOGGER.info(
                    "State changed to %s for %s. Triggered by coordinates: lat=%s, lon=%s (Accuracy: %sm, Boundary: %sm)",
                    self.native_value, self._attr_name, lat, lon, accuracy_m, boundary_distance_m
                )
                self.async_write_ha_state()
            elif not was_available or coords_changed:
                # Write state if:
                # 1. We were unavailable and now available
                # 2. Coordinates changed (so attributes update)
                self.async_write_ha_state()

        except ValueError:
            _LOGGER.error("Invalid coordinates for device %s", self._device_entity_id)

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
        """Return accuracy in meters if valid."""
        if accuracy is None:
            return None
        try:
            accuracy_m = float(accuracy)
        except (TypeError, ValueError):
            return None
        if accuracy_m <= 0:
            return None
        return accuracy_m

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
