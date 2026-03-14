"""Tests for the Custom Zone sensor entity."""

from __future__ import annotations

import json

import pytest
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, STATE_UNAVAILABLE
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.custom_zone.const import (
    CONF_COORDINATES,
    CONF_NAME,
    CONF_TRACKERS,
    CONF_ZONE_TYPE,
    DOMAIN,
    ZONE_TYPE_POLYGON,
)
from custom_components.custom_zone.sensor import CustomZoneSensor

SQUARE_POLYGON = [[0, 0], [0, 1], [1, 1], [1, 0]]


class MockState:
    """Minimal state object for direct sensor unit tests."""

    def __init__(self, state: str, **attributes) -> None:
        self.state = state
        self.attributes = attributes


async def _setup_entry(hass, name: str, trackers: list[str]) -> MockConfigEntry:
    """Create and set up a test config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=name.lower(),
        data={
            CONF_NAME: name,
            CONF_TRACKERS: trackers,
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            CONF_COORDINATES: json.dumps(SQUARE_POLYGON),
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def test_point_in_polygon_and_distance_helpers() -> None:
    """The geometry helpers should handle inside, outside, and edge cases."""
    sensor = CustomZoneSensor("entry-id", "Driveway", ["person.alice"], SQUARE_POLYGON)

    assert sensor._point_in_polygon(0.5, 0.5) is True
    assert sensor._point_in_polygon(1.5, 0.5) is False
    assert sensor._point_in_polygon(0.0, 0.5) is True
    assert sensor._distance_to_polygon_meters(0.0, 0.5) == pytest.approx(0.0)


def test_tracker_status_attributes_are_updated_for_unusable_locations() -> None:
    """Direct sensor updates should keep tracker status attributes in sync."""
    sensor = CustomZoneSensor("entry-id", "Driveway", ["person.alice"], SQUARE_POLYGON)

    sensor._handle_tracker_state_update(
        "person.alice",
        MockState("home", latitude=0.5, longitude=0.5),
        fire_update=False,
    )
    sensor._update_state_and_attributes()
    assert sensor.available is True
    assert sensor.native_value == "1 in zone"

    sensor._handle_tracker_state_update("person.alice", MockState(STATE_UNAVAILABLE), fire_update=False)
    sensor._update_state_and_attributes()
    assert sensor.available is False
    assert sensor._attr_extra_state_attributes["trackers_unavailable"] == ["person.alice"]
    assert sensor._attr_extra_state_attributes["person_alice_status"] == "unavailable"

    sensor._handle_tracker_state_update(
        "person.alice",
        MockState("home", latitude="bad", longitude=0.5),
        fire_update=False,
    )
    sensor._update_state_and_attributes()
    assert sensor._attr_extra_state_attributes["person_alice_status"] == "invalid_coordinates"
    assert sensor._attr_extra_state_attributes["person_alice_in_zone"] is None


async def test_tracker_unavailable_does_not_report_false_exit(hass) -> None:
    """Unavailable trackers should make the sensor unavailable, not out of zone."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
        },
    )
    await _setup_entry(hass, "Driveway", ["person.alice"])

    state = hass.states.get("sensor.customzone_alice_driveway")
    assert state is not None
    assert state.state == "1 in zone"

    hass.states.async_set("person.alice", STATE_UNAVAILABLE)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.customzone_alice_driveway")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


async def test_invalid_coordinates_clear_stale_in_zone_state(hass) -> None:
    """Malformed coordinates should clear the previous in-zone result."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
        },
    )
    await _setup_entry(hass, "Garden", ["person.alice"])

    state = hass.states.get("sensor.customzone_alice_garden")
    assert state is not None
    assert state.state == "1 in zone"

    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: "bad",
            ATTR_LONGITUDE: 0.5,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.customzone_alice_garden")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


async def test_per_tracker_attributes_are_namespaced_by_full_entity_id(hass) -> None:
    """Trackers with matching object IDs should not overwrite each other."""
    hass.states.async_set(
        "person.john_smith",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
        },
    )
    hass.states.async_set(
        "device_tracker.john_smith",
        "home",
        {
            ATTR_LATITUDE: 2.0,
            ATTR_LONGITUDE: 2.0,
        },
    )
    await _setup_entry(hass, "Driveway", ["person.john_smith", "device_tracker.john_smith"])

    state = hass.states.get("sensor.customzone_driveway")
    assert state is not None
    assert state.state == "1 in zone"
    assert state.attributes["person_john_smith_in_zone"] is True
    assert state.attributes["device_tracker_john_smith_in_zone"] is False
    assert state.attributes["person_john_smith_status"] == "tracked"
    assert state.attributes["device_tracker_john_smith_status"] == "tracked"
