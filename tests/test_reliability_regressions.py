"""Regression cases from the November reliability review."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.custom_zone import async_migrate_entry
from custom_components.custom_zone.config_flow import CustomZoneConfigFlow
from custom_components.custom_zone.sensor import CustomZoneSensor

SQUARE = [[0, 0], [0, 1], [1, 1], [1, 0]]


def state(*, latitude=0.5, longitude=0.5, gps_accuracy=5):
    """A fresh synthetic location, never a live tracker."""
    return SimpleNamespace(
        state="home",
        attributes={"latitude": latitude, "longitude": longitude, "gps_accuracy": gps_accuracy},
        last_updated=dt_util.utcnow(),
    )


@pytest.mark.parametrize("scale", [0.0001, 0.001, 0.01])
def test_small_diagonal_outside_point_is_not_counted(scale):
    sensor = CustomZoneSensor("review", "Triangle", ["person.test"], [[0, 0], [0, scale], [scale, 0]])
    assert not sensor._point_in_polygon(scale * 0.8, scale * 0.8)
    sensor._handle_tracker_state_update(
        "person.test", state(latitude=scale * 0.8, longitude=scale * 0.8, gps_accuracy=0.1), False
    )
    assert sensor.native_value == "0 in zone"


@pytest.mark.parametrize("accuracy", ["nan", "inf", float("nan"), float("inf"), True, False, -1, 0])
def test_non_finite_or_non_positive_accuracy_is_unusable(accuracy):
    sensor = CustomZoneSensor("review", "Square", ["person.test"], SQUARE)
    sensor._handle_tracker_state_update("person.test", state(gps_accuracy=accuracy), False)
    sensor._update_state_and_attributes()
    assert sensor.native_value == "0 in zone"
    assert sensor.extra_state_attributes["count_unusable"] == 1


@pytest.mark.parametrize("lat,lon", [(91, 0), (0, 181), ("nan", 0), (True, 0), (0, "inf")])
def test_invalid_tracker_coordinates_are_unusable(lat, lon):
    sensor = CustomZoneSensor("review", "Square", ["person.test"], SQUARE)
    sensor._handle_tracker_state_update("person.test", state(latitude=lat, longitude=lon), False)
    sensor._update_state_and_attributes()
    assert sensor.extra_state_attributes["count_unusable"] == 1


async def setup_entry(hass, coordinates=None):
    fix = state()
    hass.states.async_set("person.review", fix.state, fix.attributes)
    entry = MockConfigEntry(
        domain="custom_zone",
        unique_id="driveway",
        version=1,
        data={
            "name": "Driveway",
            "trackers": ["person.review"],
            "zone_type": "polygon",
            "coordinates": SQUARE if coordinates is None else coordinates,
        },
    )
    entry.add_to_hass(hass)
    return entry


async def test_silent_tracker_expires_and_unload_cancels_timer(hass):
    entry = await setup_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.customzone_driveway").state == "1 in zone"
    future = dt_util.utcnow() + timedelta(minutes=6)
    with patch("custom_components.custom_zone.sensor.dt_util.utcnow", return_value=future):
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()
    result = hass.states.get("sensor.customzone_driveway")
    assert result.state == "0 in zone"
    assert result.attributes["count_unusable"] == 1
    assert await hass.config_entries.async_unload(entry.entry_id)
    async_fire_time_changed(hass, future + timedelta(minutes=1))
    await hass.async_block_till_done()
    assert hass.states.get("sensor.customzone_driveway").state == "unavailable"


async def test_rename_checks_current_names_and_releases_old_name(hass):
    entry = await setup_entry(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "name": "Backyard",
            "trackers": ["person.review"],
            "zone_type": "polygon",
            "polygon_edit_mode": "keep",
        },
    )
    assert entry.unique_id == "backyard"
    for name, expected in [("Backyard", "abort"), ("Driveway", "form")]:
        result = await hass.config_entries.flow.async_init(
            "custom_zone",
            context={"source": config_entries.SOURCE_USER},
            data={"name": name, "trackers": ["person.review"], "zone_type": "polygon"},
        )
        assert result["type"] == expected
    assert hass.states.get("sensor.customzone_driveway") is not None


@pytest.mark.parametrize("raw", ["invalid json", "{}", "[[0,0],[1,1]]", [[0, 0], [0, 1], [True, 0]]])
async def test_invalid_legacy_polygon_does_not_mutate_entry(hass, raw):
    entry = await setup_entry(hass, raw)
    old_data = dict(entry.data)
    assert not await async_migrate_entry(hass, entry)
    assert entry.version == 1
    assert dict(entry.data) == old_data


def test_repeated_point_can_be_corrected_without_restart():
    flow = CustomZoneConfigFlow()
    flow._points = [[0, 0], [0, 1]]
    errors, complete = flow._process_point_step({"latitude": 0, "longitude": 0, "finished": True})
    assert errors and not complete
    assert flow._points == [[0, 0], [0, 1]]
    errors, complete = flow._process_point_step({"latitude": 1, "longitude": 0, "finished": True})
    assert not errors and complete
    assert flow._points == [[0, 0], [0, 1], [1.0, 0.0]]
