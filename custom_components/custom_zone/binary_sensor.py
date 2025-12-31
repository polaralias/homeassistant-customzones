"""Binary sensor platform for Custom Zone."""
from __future__ import annotations

import json
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, CONF_DEVICE, CONF_NAME, CONF_COORDINATES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Custom Zone binary sensor."""
    name = entry.data[CONF_NAME]
    device = entry.data[CONF_DEVICE]
    coords = json.loads(entry.data[CONF_COORDINATES])

    _LOGGER.debug("Setting up Custom Zone: %s for device %s", name, device)
    async_add_entities([CustomZoneBinarySensor(name, device, coords)], True)


class CustomZoneBinarySensor(BinarySensorEntity):
    """Representation of a Custom Zone binary sensor."""

    def __init__(self, name, device_entity_id, polygon_coords):
        """Initialize the binary sensor."""
        self._attr_name = name
        self._device_entity_id = device_entity_id
        self._polygon = polygon_coords
        self._attr_is_on = False
        self._attr_unique_id = f"{name}_{device_entity_id}_custom_zone"
        self._attr_extra_state_attributes = {
            "device": device_entity_id,
            "polygon": polygon_coords
        }

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
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            _LOGGER.debug("Device %s is unavailable or unknown", self._device_entity_id)
            self._attr_is_on = False
            self.async_write_ha_state()
            return

        lat = new_state.attributes.get(ATTR_LATITUDE)
        lon = new_state.attributes.get(ATTR_LONGITUDE)

        if lat is None or lon is None:
            _LOGGER.debug("Device %s has no coordinates", self._device_entity_id)
            self._attr_is_on = False
            self.async_write_ha_state()
            return

        _LOGGER.debug("Device %s at %s, %s. Checking zone %s", self._device_entity_id, lat, lon, self._attr_name)

        try:
            lat = float(lat)
            lon = float(lon)
            is_inside = self._point_in_polygon(lat, lon)

            if is_inside:
                _LOGGER.debug("Inside the Poly Zone")
            else:
                _LOGGER.debug("Outside the Poly Zone")

            if self._attr_is_on != is_inside:
                self._attr_is_on = is_inside
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
