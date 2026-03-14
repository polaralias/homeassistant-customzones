"""Tests for the Custom Zone config flow."""

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.custom_zone.const import (
    CONF_COORDINATES,
    CONF_NAME,
    CONF_TRACKERS,
    CONF_ZONE_TYPE,
    DOMAIN,
    ZONE_TYPE_POLYGON,
)


async def test_duplicate_zone_name_is_rejected(hass) -> None:
    """Zone names should be unique across config entries."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="driveway",
        data={
            CONF_NAME: "Driveway",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            CONF_COORDINATES: "[[0, 0], [0, 1], [1, 1]]",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={
            CONF_NAME: "Driveway",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_point_step_validates_coordinate_ranges(hass) -> None:
    """Out-of-range coordinates should be rejected before entry creation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={
            CONF_NAME: "Garden",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_LATITUDE: 91.0,
            CONF_LONGITUDE: 0.0,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result["errors"] == {CONF_LATITUDE: "invalid_latitude"}
