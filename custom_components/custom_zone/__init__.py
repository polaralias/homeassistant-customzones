"""The Custom Zone integration."""

from __future__ import annotations

import json
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

from .const import CONF_COORDINATES, CONF_NAME, DOMAIN

PLATFORMS: list[str] = ["sensor"]
_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Upgrade legacy polygons without replacing the entry or its sensor."""
    if entry.version > 2:
        return False
    if entry.version == 2:
        return True

    from .config_flow import _PolygonFlowMixin  # noqa: PLC0415
    from .sensor import _parse_polygon_coords  # noqa: PLC0415

    data = dict(entry.data)
    try:
        raw = data[CONF_COORDINATES]
        coordinates = _parse_polygon_coords(json.loads(raw) if isinstance(raw, str) else raw)
        error = _PolygonFlowMixin()._validate_polygon(coordinates)
        if error:
            raise ValueError(error)
        data[CONF_COORDINATES] = coordinates
        hass.config_entries.async_update_entry(entry, data=data, version=2, unique_id=slugify(data[CONF_NAME]))
    except (KeyError, TypeError, ValueError):
        _LOGGER.error("Custom Zone migration failed: repair the saved polygon before retrying")
        return False
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Custom Zone from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        pass

    return unload_ok
