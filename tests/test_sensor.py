"""Tests for the Custom Zone sensor entity."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from homeassistant.const import ATTR_GPS_ACCURACY, ATTR_LATITUDE, ATTR_LONGITUDE, STATE_UNAVAILABLE
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

    def __init__(self, state: str, last_updated: datetime | None = None, **attributes) -> None:
        self.state = state
        self.attributes = attributes
        self.last_updated = last_updated


async def _setup_entry(hass, name: str, trackers: list[str]) -> MockConfigEntry:
    """Create and set up a test config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=name.lower(),
        data={
            CONF_NAME: name,
            CONF_TRACKERS: trackers,
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            CONF_COORDINATES: SQUARE_POLYGON,
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


def test_point_in_concave_polygon_respects_the_notch() -> None:
    """Concave polygons should exclude points inside the notch cutout."""
    concave_polygon = [[0, 0], [0, 3], [3, 3], [3, 2], [1, 2], [1, 0]]
    sensor = CustomZoneSensor("entry-id", "Concave", ["person.alice"], concave_polygon)

    assert sensor._point_in_polygon(0.5, 0.5) is True
    assert sensor._point_in_polygon(2.0, 2.5) is True
    assert sensor._point_in_polygon(2.0, 1.5) is False


def test_polygon_winding_order_does_not_change_inclusion() -> None:
    """Clockwise and counter-clockwise polygons should behave the same."""
    clockwise = [[0, 0], [1, 0], [1, 1], [0, 1]]
    counter_clockwise = list(reversed(clockwise))

    clockwise_sensor = CustomZoneSensor("entry-id", "Clockwise", ["person.alice"], clockwise)
    counter_clockwise_sensor = CustomZoneSensor(
        "entry-id",
        "CounterClockwise",
        ["person.alice"],
        counter_clockwise,
    )

    assert clockwise_sensor._point_in_polygon(0.5, 0.5) is True
    assert counter_clockwise_sensor._point_in_polygon(0.5, 0.5) is True
    assert clockwise_sensor._point_in_polygon(1.5, 0.5) is False
    assert counter_clockwise_sensor._point_in_polygon(1.5, 0.5) is False


def test_vertices_and_diagonal_boundaries_count_as_inside() -> None:
    """Exact vertices and diagonal edges should be treated as inside."""
    triangle = [[0, 0], [2, 0], [1, 1]]
    sensor = CustomZoneSensor("entry-id", "Triangle", ["person.alice"], triangle)

    assert sensor._point_in_polygon(0.0, 0.0) is True
    assert sensor._point_in_polygon(0.5, 0.5) is True
    assert sensor._distance_to_polygon_meters(0.5, 0.5) == pytest.approx(0.0)


def test_points_near_an_edge_but_outside_are_not_included() -> None:
    """Points just outside the polygon should stay outside."""
    sensor = CustomZoneSensor("entry-id", "Driveway", ["person.alice"], SQUARE_POLYGON)

    assert sensor._point_in_polygon(-0.01, 0.5) is False
    assert sensor._point_in_polygon(0.5, 1.01) is False


def test_very_small_polygons_still_evaluate_membership() -> None:
    """Very small valid polygons should still work geometrically."""
    tiny_triangle = [[0.0, 0.0], [0.0, 0.0001], [0.0001, 0.0]]
    sensor = CustomZoneSensor("entry-id", "Tiny", ["person.alice"], tiny_triangle)

    assert sensor._point_in_polygon(0.00002, 0.00002) is True
    assert sensor._point_in_polygon(0.0002, 0.0002) is False


def test_polygon_evaluation_works_at_high_latitude() -> None:
    """High-latitude polygons should still evaluate basic membership correctly."""
    arctic_square = [[60.0, 10.0], [60.0, 10.1], [60.1, 10.1], [60.1, 10.0]]
    sensor = CustomZoneSensor("entry-id", "Arctic", ["person.alice"], arctic_square)

    assert sensor._point_in_polygon(60.05, 10.05) is True
    assert sensor._point_in_polygon(60.2, 10.2) is False


def test_polygon_can_cross_longitude_sign_change() -> None:
    """Polygons spanning west/east longitude sign changes should still behave locally."""
    meridian_square = [[51.0, -0.1], [51.0, 0.1], [51.1, 0.1], [51.1, -0.1]]
    sensor = CustomZoneSensor("entry-id", "Meridian", ["person.alice"], meridian_square)

    assert sensor._point_in_polygon(51.05, 0.0) is True
    assert sensor._point_in_polygon(51.2, 0.2) is False


def test_distance_to_square_center_matches_equator_scale() -> None:
    """Distance at the center of a one-degree equatorial square should match the nearest edge."""
    sensor = CustomZoneSensor("entry-id", "Equator", ["person.alice"], SQUARE_POLYGON)

    assert sensor._distance_to_polygon_meters(0.5, 0.5) == pytest.approx(55_660, rel=0.01)


def test_distance_reflects_longitude_scaling_at_high_latitude() -> None:
    """Longitude distance should shrink with latitude in the local approximation."""
    arctic_square = [[60.0, 10.0], [60.0, 10.1], [60.1, 10.1], [60.1, 10.0]]
    sensor = CustomZoneSensor("entry-id", "Arctic", ["person.alice"], arctic_square)

    assert sensor._distance_to_polygon_meters(60.05, 10.05) == pytest.approx(2_783, rel=0.02)


def test_distance_for_outside_point_uses_nearest_boundary() -> None:
    """Outside points should report the nearest boundary distance, not zero."""
    sensor = CustomZoneSensor("entry-id", "Driveway", ["person.alice"], SQUARE_POLYGON)

    assert sensor._distance_to_polygon_meters(1.25, 0.5) == pytest.approx(27_830, rel=0.01)


def test_single_tracker_zone_uses_zone_based_entity_id() -> None:
    """Zone identity should not encode tracker membership."""
    sensor = CustomZoneSensor("entry-id", "Driveway", ["person.alice"], SQUARE_POLYGON)

    assert sensor.entity_id == "sensor.customzone_driveway"


def test_tracker_status_attributes_are_updated_for_unusable_locations() -> None:
    """Direct sensor updates should publish nested-only tracker detail."""
    sensor = CustomZoneSensor("entry-id", "Driveway", ["person.alice"], SQUARE_POLYGON)

    sensor._handle_tracker_state_update(
        "person.alice",
        MockState("home", latitude=0.5, longitude=0.5, gps_accuracy=5),
        fire_update=False,
    )
    sensor._update_state_and_attributes()
    assert sensor.available is True
    assert sensor.native_value == "1 in zone"

    sensor._handle_tracker_state_update("person.alice", MockState(STATE_UNAVAILABLE), fire_update=False)
    sensor._update_state_and_attributes()
    assert sensor.available is True
    assert sensor.native_value == "0 in zone"
    assert sensor._attr_extra_state_attributes["trackers_unusable"] == ["person.alice"]
    detail = sensor._attr_extra_state_attributes["trackers_detail"]["person.alice"]
    assert detail["diagnostic_reason"] == "tracker_unavailable"
    assert "person_alice_status" not in sensor._attr_extra_state_attributes

    sensor._handle_tracker_state_update(
        "person.alice",
        MockState("home", latitude="bad", longitude=0.5),
        fire_update=False,
    )
    sensor._update_state_and_attributes()
    assert sensor.native_value == "0 in zone"
    detail = sensor._attr_extra_state_attributes["trackers_detail"]["person.alice"]
    assert detail["diagnostic_reason"] == "confidence_data_invalid"
    assert "person_alice_in_zone" not in sensor._attr_extra_state_attributes


async def test_tracker_unavailable_stays_visible_without_collapsing_aggregate_state(hass) -> None:
    """Unavailable trackers should degrade the tracker, not the aggregate sensor."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    await _setup_entry(hass, "Driveway", ["person.alice"])

    state = hass.states.get("sensor.customzone_driveway")
    assert state is not None
    assert state.state == "1 in zone"

    hass.states.async_set("person.alice", STATE_UNAVAILABLE)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.customzone_driveway")
    assert state is not None
    assert state.state == "0 in zone"
    assert state.attributes["trackers_unusable"] == ["person.alice"]
    assert state.attributes["count_unusable"] == 1
    detail = state.attributes["trackers_detail"]["person.alice"]
    assert detail["diagnostic_reason"] == "tracker_unavailable"
    assert "person_alice_status" not in state.attributes


async def test_invalid_coordinates_clear_stale_in_zone_state(hass) -> None:
    """Malformed coordinates should clear the previous in-zone result."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    await _setup_entry(hass, "Garden", ["person.alice"])

    state = hass.states.get("sensor.customzone_garden")
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

    state = hass.states.get("sensor.customzone_garden")
    assert state is not None
    assert state.state == "0 in zone"
    assert state.attributes["trackers_unusable"] == ["person.alice"]
    detail = state.attributes["trackers_detail"]["person.alice"]
    assert detail["diagnostic_reason"] == "confidence_data_invalid"


async def test_trackers_detail_is_keyed_by_full_entity_id(hass) -> None:
    """Trackers with matching object IDs should not overwrite each other."""
    hass.states.async_set(
        "person.john_smith",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    hass.states.async_set(
        "device_tracker.john_smith",
        "home",
        {
            ATTR_LATITUDE: 2.0,
            ATTR_LONGITUDE: 2.0,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    await _setup_entry(hass, "Driveway", ["person.john_smith", "device_tracker.john_smith"])

    state = hass.states.get("sensor.customzone_driveway")
    assert state is not None
    assert state.state == "1 in zone"
    detail = state.attributes["trackers_detail"]
    assert detail["person.john_smith"]["classification"] == "counted_in_zone"
    assert detail["device_tracker.john_smith"]["classification"] == "counted_out_of_zone"
    assert "person_john_smith_in_zone" not in state.attributes


async def test_sensor_starts_with_all_trackers_unusable_when_no_states_exist(hass) -> None:
    """A zone should still load when trackers have no current Home Assistant state."""
    await _setup_entry(hass, "Offline Zone", ["person.alice", "person.bob"])

    state = hass.states.get("sensor.customzone_offline_zone")
    assert state is not None
    assert state.state == "0 in zone"
    assert state.attributes["count_in_zone"] == 0
    assert state.attributes["count_out_of_zone"] == 0
    assert state.attributes["count_unusable"] == 2
    assert state.attributes["trackers_unusable"] == ["person.alice", "person.bob"]


async def test_mixed_tracker_quality_preserves_partial_aggregate_truth(hass) -> None:
    """One usable tracker should still count even when another tracker is unusable."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    hass.states.async_set("person.bob", STATE_UNAVAILABLE)
    await _setup_entry(hass, "Mixed Zone", ["person.alice", "person.bob"])

    state = hass.states.get("sensor.customzone_mixed_zone")
    assert state is not None
    assert state.state == "1 in zone"
    assert state.attributes["count_in_zone"] == 1
    assert state.attributes["count_out_of_zone"] == 0
    assert state.attributes["count_unusable"] == 1
    assert state.attributes["trackers_in_zone"] == ["person.alice"]
    assert state.attributes["trackers_unusable"] == ["person.bob"]
    detail = state.attributes["trackers_detail"]
    assert detail["person.alice"]["classification"] == "counted_in_zone"
    assert detail["person.bob"]["diagnostic_reason"] == "tracker_unavailable"


async def test_two_trackers_inside_are_both_counted(hass) -> None:
    """Multiple usable trackers inside the polygon should both count."""
    for entity_id, latitude, longitude in (
        ("person.alice", 0.25, 0.25),
        ("person.bob", 0.75, 0.75),
    ):
        hass.states.async_set(
            entity_id,
            "home",
            {
                ATTR_LATITUDE: latitude,
                ATTR_LONGITUDE: longitude,
                ATTR_GPS_ACCURACY: 5,
            },
        )

    await _setup_entry(hass, "Inside Zone", ["person.alice", "person.bob"])

    state = hass.states.get("sensor.customzone_inside_zone")
    assert state is not None
    assert state.state == "2 in zone"
    assert state.attributes["count_in_zone"] == 2
    assert state.attributes["count_out_of_zone"] == 0
    assert state.attributes["count_unusable"] == 0
    assert state.attributes["trackers_in_zone"] == ["person.alice", "person.bob"]


async def test_all_outside_trackers_are_counted_outside(hass) -> None:
    """Usable trackers outside the polygon should be counted explicitly."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 2.0,
            ATTR_LONGITUDE: 2.0,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    hass.states.async_set(
        "person.bob",
        "home",
        {
            ATTR_LATITUDE: 3.0,
            ATTR_LONGITUDE: 3.0,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    await _setup_entry(hass, "Outside Zone", ["person.alice", "person.bob"])

    state = hass.states.get("sensor.customzone_outside_zone")
    assert state is not None
    assert state.state == "0 in zone"
    assert state.attributes["count_in_zone"] == 0
    assert state.attributes["count_out_of_zone"] == 2
    assert state.attributes["count_unusable"] == 0
    assert state.attributes["trackers_out_of_zone"] == ["person.alice", "person.bob"]


async def test_all_unavailable_trackers_keep_numeric_state(hass) -> None:
    """All trackers can be unusable without making the aggregate sensor unavailable."""
    hass.states.async_set("person.alice", STATE_UNAVAILABLE)
    hass.states.async_set("person.bob", STATE_UNAVAILABLE)
    await _setup_entry(hass, "Unavailable Zone", ["person.alice", "person.bob"])

    state = hass.states.get("sensor.customzone_unavailable_zone")
    assert state is not None
    assert state.state == "0 in zone"
    assert state.attributes["count_in_zone"] == 0
    assert state.attributes["count_out_of_zone"] == 0
    assert state.attributes["count_unusable"] == 2
    assert state.attributes["trackers_unusable"] == ["person.alice", "person.bob"]


async def test_low_confidence_inside_fix_is_not_counted_in_zone(hass) -> None:
    """Low-confidence fixes should be unusable even when geometry says inside."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.01,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 900,
        },
    )
    await _setup_entry(hass, "Driveway", ["person.alice"])

    state = hass.states.get("sensor.customzone_driveway")
    assert state is not None
    assert state.state == "0 in zone"
    assert state.attributes["count_in_zone"] == 0
    assert state.attributes["count_out_of_zone"] == 0
    assert state.attributes["count_unusable"] == 1
    assert state.attributes["trackers_in_zone"] == []
    assert state.attributes["trackers_out_of_zone"] == []
    assert state.attributes["trackers_unusable"] == ["person.alice"]

    detail = state.attributes["trackers_detail"]["person.alice"]
    assert detail["classification"] == "unusable"
    assert detail["diagnostic_reason"] == "confidence_failure"
    assert detail["counted_in_zone"] is None
    assert detail["gps_accuracy_m"] == pytest.approx(900.0)
    assert detail["trusted_distance_m"] is None


def test_missing_accuracy_marks_tracker_unusable() -> None:
    """A fix without usable accuracy data should not be counted."""
    sensor = CustomZoneSensor("entry-id", "Driveway", ["person.alice"], SQUARE_POLYGON)

    sensor._handle_tracker_state_update(
        "person.alice",
        MockState("home", latitude=0.5, longitude=0.5),
        fire_update=False,
    )
    sensor._update_state_and_attributes()

    assert sensor.native_value == "0 in zone"
    detail = sensor._attr_extra_state_attributes["trackers_detail"]["person.alice"]
    assert detail["classification"] == "unusable"
    assert detail["diagnostic_reason"] == "confidence_data_missing"
    assert detail["gps_accuracy_m"] is None
    assert detail["trusted_distance_m"] is None


def test_stale_location_marks_tracker_unusable() -> None:
    """An old tracker fix should be excluded from counting."""
    sensor = CustomZoneSensor("entry-id", "Driveway", ["person.alice"], SQUARE_POLYGON)
    stale_time = datetime.now(UTC) - timedelta(minutes=6)

    sensor._handle_tracker_state_update(
        "person.alice",
        MockState("home", last_updated=stale_time, latitude=0.5, longitude=0.5, gps_accuracy=5),
        fire_update=False,
    )
    sensor._update_state_and_attributes()

    assert sensor.native_value == "0 in zone"
    detail = sensor._attr_extra_state_attributes["trackers_detail"]["person.alice"]
    assert detail["classification"] == "unusable"
    assert detail["diagnostic_reason"] == "stale_location"
    assert detail["gps_accuracy_m"] == pytest.approx(5.0)


async def test_tracker_transition_from_outside_to_inside_updates_counts(hass) -> None:
    """State changes should move a tracker between outside and inside counts."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 2.0,
            ATTR_LONGITUDE: 2.0,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    await _setup_entry(hass, "Transition Zone", ["person.alice"])

    state = hass.states.get("sensor.customzone_transition_zone")
    assert state is not None
    assert state.state == "0 in zone"
    assert state.attributes["count_out_of_zone"] == 1

    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.customzone_transition_zone")
    assert state is not None
    assert state.state == "1 in zone"
    assert state.attributes["count_in_zone"] == 1
    assert state.attributes["count_out_of_zone"] == 0


async def test_tracker_transition_to_missing_coordinates_marks_it_unusable(hass) -> None:
    """Removing coordinates should move a tracker out of the counted sets."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    await _setup_entry(hass, "Missing Coordinate Zone", ["person.alice"])

    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.customzone_missing_coordinate_zone")
    assert state is not None
    assert state.state == "0 in zone"
    assert state.attributes["count_in_zone"] == 0
    assert state.attributes["count_out_of_zone"] == 0
    assert state.attributes["count_unusable"] == 1
    detail = state.attributes["trackers_detail"]["person.alice"]
    assert detail["classification"] == "unusable"
    assert detail["diagnostic_reason"] == "confidence_data_missing"


async def test_tracker_recovery_from_unavailable_restores_counting(hass) -> None:
    """A tracker should become countable again when good data returns."""
    hass.states.async_set("person.alice", STATE_UNAVAILABLE)
    await _setup_entry(hass, "Recovery Zone", ["person.alice"])

    state = hass.states.get("sensor.customzone_recovery_zone")
    assert state is not None
    assert state.state == "0 in zone"
    assert state.attributes["count_unusable"] == 1

    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("sensor.customzone_recovery_zone")
    assert state is not None
    assert state.state == "1 in zone"
    assert state.attributes["count_in_zone"] == 1
    assert state.attributes["count_unusable"] == 0


async def test_documented_aggregate_attributes_are_present(hass) -> None:
    """The public aggregate attribute contract should always be present."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    await _setup_entry(hass, "Attribute Zone", ["person.alice"])

    state = hass.states.get("sensor.customzone_attribute_zone")
    assert state is not None

    for attribute in (
        "count_in_zone",
        "count_out_of_zone",
        "count_unusable",
        "trackers_in_zone",
        "trackers_out_of_zone",
        "trackers_unusable",
        "trackers_detail",
    ):
        assert attribute in state.attributes


async def test_string_coordinate_entries_are_rejected(hass) -> None:
    """Non-structured coordinate storage should fail safely at setup time."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="string-driveway",
        data={
            CONF_NAME: "String Driveway",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            CONF_COORDINATES: "[[0, 0], [0, 1], [1, 1], [1, 0]]",
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.customzone_string_driveway")
    assert state is None


async def test_malformed_structured_coordinate_entries_are_rejected(hass) -> None:
    """Malformed structured polygon data should fail safely at setup time."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="bad-polygon",
        data={
            CONF_NAME: "Bad Polygon",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            CONF_COORDINATES: [[0, 0], [0, 1], ["bad", 1]],
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.customzone_bad_polygon")
    assert state is None


async def test_unload_and_reload_restore_runtime_behavior(hass) -> None:
    """The config entry should unload to unavailable and recover on reload."""
    hass.states.async_set(
        "person.alice",
        "home",
        {
            ATTR_LATITUDE: 0.5,
            ATTR_LONGITUDE: 0.5,
            ATTR_GPS_ACCURACY: 5,
        },
    )
    entry = await _setup_entry(hass, "Reloadable Zone", ["person.alice"])

    assert hass.states.get("sensor.customzone_reloadable_zone") is not None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    unloaded_state = hass.states.get("sensor.customzone_reloadable_zone")
    assert unloaded_state is not None
    assert unloaded_state.state == STATE_UNAVAILABLE

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    reloaded_state = hass.states.get("sensor.customzone_reloadable_zone")
    assert reloaded_state is not None
    assert reloaded_state.state == "1 in zone"
