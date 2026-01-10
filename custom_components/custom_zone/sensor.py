"""Sensor platform for Custom Zone."""
from __future__ import annotations

import json
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, STATE_UNAVAILABLE, STATE_UNKNOWN, ATTR_GPS_ACCURACY
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import slugify

from .const import DOMAIN, CONF_DEVICE, CONF_NAME, CONF_COORDINATES

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

        # Requirement: "binary_sensor.customzone_james_work"
        # Since we are in the sensor platform, the domain will be 'sensor'.
        # However, we can construct the object_id to match the requirement.
        # entity_id format: <domain>.<object_id>
        # We want object_id to be: customzone_{person}_{zone}

        person_slug = slugify(device_entity_id.split(".")[-1])
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

    @callback
    def _async_device_changed(self, event) -> None:
        """Handle device state changes."""
        new_state = event.data.get("new_state")
        was_available = self._is_available

        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            _LOGGER.debug("Device %s is unavailable or unknown", self._device_entity_id)
            if self._is_available:
                self._is_available = False
                self.async_write_ha_state()
            return

        lat = new_state.attributes.get(ATTR_LATITUDE)
        lon = new_state.attributes.get(ATTR_LONGITUDE)

        # NOTE: We explicitly check and log accuracy for debugging, but we DO NOT use it in calculation.
        # The user requested to use exact coordinates "rather than paying attention to the range of coordinates".
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

            # Update attributes with triggering coordinates
            self._attr_extra_state_attributes.update({
                "triggering_latitude": str(self._current_lat),
                "triggering_longitude": str(self._current_lon),
            })

            # Using exact coordinates as requested, ignoring accuracy.
            is_inside = self._point_in_polygon(lat, lon)

            if is_inside:
                _LOGGER.debug("Inside the Poly Zone")
            else:
                _LOGGER.debug("Outside the Poly Zone")

            if self._is_inside != is_inside:
                self._is_inside = is_inside
                _LOGGER.info(
                    "State changed to %s. Triggering coordinates: lat=%s, lon=%s",
                    self.state, lat, lon
                )
                self.async_write_ha_state()
            elif not was_available or coords_changed:
                # Write state if:
                # 1. We were unavailable and now available
                # 2. Coordinates changed (so attributes update)
                self.async_write_ha_state()

        except ValueError:
            _LOGGER.error("Invalid coordinates for device %s", self._device_entity_id)

    def _point_in_polygon(self, x, y):
        """Check if point (x, y) is inside the polygon."""
        # x = latitude, y = longitude
        poly = self._polygon
        n = len(poly)

        for i in range(n):
            p1 = poly[i]
            p2 = poly[(i + 1) % n]

            # Vertex check
            if abs(p1[0] - x) < 0.000001 and abs(p1[1] - y) < 0.000001:
                return True

            # Boundary check
            p1x, p1y = p1
            p2x, p2y = p2
            if x >= min(p1x, p2x) - 0.000001 and x <= max(p1x, p2x) + 0.000001 and \
               y >= min(p1y, p2y) - 0.000001 and y <= max(p1y, p2y) + 0.000001:
                 # Collinear check
                 cross = (y - p1y) * (p2x - p1x) - (p2y - p1y) * (x - p1x)
                 if abs(cross) < 0.000001:
                     return True

        inside = False
        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]

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
