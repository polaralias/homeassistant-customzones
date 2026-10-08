"""Tests for the Custom Zone config flow."""

import pytest
import voluptuous as vol
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


async def _start_polygon_flow(hass, name: str = "Garden") -> str:
    """Start the config flow and return the point-step flow id."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={
            CONF_NAME: name,
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    return result["flow_id"]


def _schema_has_field(schema: vol.Schema, key: str) -> bool:
    """Return True when a voluptuous schema includes the named field."""
    return any(getattr(marker, "schema", None) == key for marker in schema.schema)


async def _add_points(hass, flow_id: str, points: tuple[tuple[float, float], ...]) -> dict:
    """Submit polygon points without finishing."""
    result = None
    for latitude, longitude in points:
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input={
                CONF_LATITUDE: latitude,
                CONF_LONGITUDE: longitude,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "point"
    assert result is not None
    return result


async def _setup_entry(hass, name: str, trackers: list[str], coordinates: list[list[float]]) -> MockConfigEntry:
    """Create and set up a test config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=name.lower(),
        data={
            CONF_NAME: name,
            CONF_TRACKERS: trackers,
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            CONF_COORDINATES: coordinates,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _required_field_default(schema: vol.Schema, key: str):
    """Return the voluptuous default for a required schema field."""
    for marker in schema.schema:
        if getattr(marker, "schema", None) == key:
            default = getattr(marker, "default", vol.UNDEFINED)
            if default is vol.UNDEFINED:
                return vol.UNDEFINED
            return default()
    raise AssertionError(f"Schema is missing {key}")


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


async def test_blank_zone_name_is_rejected(hass) -> None:
    """Zone names should not be empty or whitespace."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={
            CONF_NAME: "   ",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_NAME: "empty_name"}


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


def _config_flow_handler(hass, flow_id: str):
    """Return the in-progress config flow handler."""
    return hass.config_entries.flow._progress[flow_id]


def _options_flow_handler(hass, flow_id: str):
    """Return the in-progress options flow handler."""
    return hass.config_entries.options._progress[flow_id]


async def test_point_one_accepts_decimal_gps_ending_in_zero(hass) -> None:
    """Point 1 must accept real GPS decimals, including values that end in 0."""
    flow_id = await _start_polygon_flow(hass, name="Uzhhorod")

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_LATITUDE: 48.623560,
            CONF_LONGITUDE: 22.294930,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result.get("errors") in (None, {})
    assert "required_fields" not in str(result)
    assert result["description_placeholders"]["status_msg"] == "Point 2"
    assert _config_flow_handler(hass, flow_id)._points == [[48.623560, 22.294930]]


async def test_point_one_accepts_frontend_string_coordinates(hass) -> None:
    """Frontend JSON may deliver GPS decimals as strings, not Python floats."""
    flow_id = await _start_polygon_flow(hass, name="String GPS")

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_LATITUDE: "48.623560",
            CONF_LONGITUDE: "22.294930",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result.get("errors") in (None, {})
    assert result["description_placeholders"]["status_msg"] == "Point 2"
    assert _config_flow_handler(hass, flow_id)._points == [[48.623560, 22.294930]]


async def test_point_one_accepts_integer_zero_coordinates(hass) -> None:
    """JSON number 0 is a Python int; 0,0 is a valid GPS point."""
    flow_id = await _start_polygon_flow(hass, name="Zero GPS")

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_LATITUDE: 0,
            CONF_LONGITUDE: 0,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result.get("errors") in (None, {})
    assert "required_fields" not in str(result)
    assert result["description_placeholders"]["status_msg"] == "Point 2"
    assert _config_flow_handler(hass, flow_id)._points == [[0.0, 0.0]]


async def test_options_point_one_accepts_decimal_gps_and_zero(hass) -> None:
    """Options replace mode must accept the same GPS and zero coordinates."""
    entry = await _setup_entry(
        hass,
        "Driveway",
        ["person.alice"],
        [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Driveway",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            "polygon_edit_mode": "replace",
        },
    )
    assert result["description_placeholders"]["status_msg"] == "Point 1"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_LATITUDE: 48.623560,
            CONF_LONGITUDE: 22.294930,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result.get("errors") in (None, {})
    assert result["description_placeholders"]["status_msg"] == "Point 2"
    assert _options_flow_handler(hass, result["flow_id"])._points == [[48.623560, 22.294930]]

    entry = await _setup_entry(
        hass,
        "Zero Options",
        ["person.alice"],
        [[1.0, 1.0], [1.0, 2.0], [2.0, 2.0]],
    )
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Zero Options",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            "polygon_edit_mode": "replace",
        },
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_LATITUDE: 0,
            CONF_LONGITUDE: 0,
        },
    )
    assert result.get("errors") in (None, {})
    assert result["description_placeholders"]["status_msg"] == "Point 2"
    assert _options_flow_handler(hass, result["flow_id"])._points == [[0.0, 0.0]]


async def test_tracker_selection_is_not_limited_to_ten_entities(hass) -> None:
    """The config flow should not impose an arbitrary small tracker cap."""
    trackers = [f"person.person_{index}" for index in range(11)]

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={
            CONF_NAME: "Large Zone",
            CONF_TRACKERS: trackers,
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"


async def test_user_form_trackers_default_is_empty_list(hass) -> None:
    """A new zone must default trackers to a list, not None (issue #18)."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    default = _required_field_default(result["data_schema"], CONF_TRACKERS)
    assert default == []
    assert default is not None


async def test_user_form_omitted_trackers_does_not_fail_with_value_should_be_a_list(hass) -> None:
    """Missing trackers must become [] and fail as empty_trackers, not a selector crash."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Garden",
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_TRACKERS: "empty_trackers"}
    assert "Value should be a list" not in str(result.get("errors"))
    assert "Value should be a list" not in str(result.get("description_placeholders"))


async def test_user_form_accepts_person_and_device_tracker_entities(hass) -> None:
    """Trackers may include both person and device_tracker entities."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={
            CONF_NAME: "School",
            CONF_TRACKERS: ["person.alice", "device_tracker.alice_phone"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"


async def test_options_form_preserves_existing_tracker_defaults(hass) -> None:
    """Options Flow should prefill the current tracker list."""
    existing = ["person.alice", "device_tracker.alice_phone"]
    entry = await _setup_entry(
        hass,
        "Driveway",
        existing,
        [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert _required_field_default(result["data_schema"], CONF_TRACKERS) == existing


async def test_empty_tracker_selection_is_rejected(hass) -> None:
    """The config flow should require at least one tracker."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={
            CONF_NAME: "Garden",
            CONF_TRACKERS: [],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_TRACKERS: "empty_trackers"}


async def test_repeated_polygon_points_are_rejected_when_finishing(hass) -> None:
    """A polygon with repeated points should not be accepted."""
    flow_id = await _start_polygon_flow(hass, name="Repeated Point Zone")
    await _add_points(hass, flow_id, ((0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (0.0, 0.0)))

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={"finished": True},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result["errors"] == {"base": "repeated_points"}


async def test_finishing_with_fewer_than_three_distinct_points_fails_cleanly(hass) -> None:
    """A polygon needs three distinct points before the flow can complete."""
    flow_id = await _start_polygon_flow(hass, name="Short Polygon Zone")

    for latitude, longitude in ((0.0, 0.0), (0.0, 1.0)):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input={
                CONF_LATITUDE: latitude,
                CONF_LONGITUDE: longitude,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "point"

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_LATITUDE: 0.0,
            CONF_LONGITUDE: 1.0,
            "finished": True,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result["errors"] == {"base": "not_enough_points"}


HEXAGON_POINTS = (
    (10.0, 10.0),
    (12.0, 10.0),
    (13.0, 11.0),
    (12.0, 12.0),
    (10.0, 12.0),
    (9.0, 11.0),
)


@pytest.mark.parametrize(
    ("points", "final_point"),
    [
        (((0.0, 0.0), (0.0, 2.0), (2.0, 2.0)), (2.0, 0.0)),
        (((1.0, 0.0), (1.0, 1.0), (0.0, 1.0)), (0.0, 0.0)),
    ],
)
async def test_finishing_with_final_point_preserves_all_coordinates(hass, points, final_point) -> None:
    """A final coordinate, including 0,0, must be saved when finishing."""
    flow_id = await _start_polygon_flow(hass)
    await _add_points(hass, flow_id, points)
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={CONF_LATITUDE: final_point[0], CONF_LONGITUDE: final_point[1], "finished": True},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_COORDINATES] == [list(point) for point in (*points, final_point)]


@pytest.mark.parametrize("edit_mode", ["replace", "append"])
async def test_options_finishing_with_final_point_preserves_all_coordinates(hass, edit_mode) -> None:
    """Both editing paths preserve a final point submitted with Finished."""
    points = ((0.0, 0.0), (0.0, 2.0), (2.0, 2.0))
    entry = await _setup_entry(hass, "Square", ["person.alice"], [list(point) for point in points])
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Square",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            "polygon_edit_mode": edit_mode,
        },
    )
    if edit_mode == "replace":
        for latitude, longitude in points:
            result = await hass.config_entries.options.async_configure(
                result["flow_id"], user_input={CONF_LATITUDE: latitude, CONF_LONGITUDE: longitude}
            )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_LATITUDE: 2.0, CONF_LONGITUDE: 0.0, "finished": True}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_COORDINATES] == [list(point) for point in points] + [[2.0, 0.0]]


@pytest.mark.parametrize(
    ("submission", "expected_errors"),
    [
        ({CONF_LATITUDE: 2.0, "finished": True}, {CONF_LONGITUDE: "invalid_longitude"}),
        ({CONF_LATITUDE: 99.0, CONF_LONGITUDE: 0.0, "finished": True}, {CONF_LATITUDE: "invalid_latitude"}),
        ({}, {CONF_LATITUDE: "invalid_latitude", CONF_LONGITUDE: "invalid_longitude"}),
    ],
)
async def test_invalid_point_is_not_silently_discarded_when_finishing(hass, submission, expected_errors) -> None:
    """Partial, invalid, or unfinished blank input must not save the polygon."""
    flow_id = await _start_polygon_flow(hass)
    points = ((0.0, 0.0), (0.0, 2.0), (2.0, 2.0))
    await _add_points(hass, flow_id, points)
    result = await hass.config_entries.flow.async_configure(flow_id, user_input=submission)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == expected_errors
    assert _config_flow_handler(hass, flow_id)._points == [list(point) for point in points]


async def test_finish_only_after_six_points_preserves_coordinates(hass) -> None:
    """Finishing with blank coordinates stores the six entered points."""
    flow_id = await _start_polygon_flow(hass, name="Hexagon Zone")
    result = await _add_points(hass, flow_id, HEXAGON_POINTS)

    assert result["description_placeholders"]["status_msg"] == "Point 7"
    assert result["description_placeholders"]["shape_desc"] == "Hexagon"
    assert _schema_has_field(result["data_schema"], "finished")
    assert result["data_schema"]({"finished": True}) == {"finished": True}

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={"finished": True},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result.get("errors") in (None, {})
    stored = result["data"][CONF_COORDINATES]
    assert stored == [list(point) for point in HEXAGON_POINTS]
    assert [0.0, 0.0] not in stored
    assert "not_enough_points" not in str(result)


async def test_finish_only_after_three_points_preserves_coordinates(hass) -> None:
    """Finishing with blank coordinates stores the three entered points."""
    triangle = ((10.0, 10.0), (12.0, 10.0), (11.0, 12.0))
    flow_id = await _start_polygon_flow(hass, name="Triangle Zone")
    result = await _add_points(hass, flow_id, triangle)

    assert result["description_placeholders"]["status_msg"] == "Point 4"
    assert result["description_placeholders"]["shape_desc"] == "Triangle"

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={"finished": True},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    stored = result["data"][CONF_COORDINATES]
    assert stored == [list(point) for point in triangle]
    assert [0.0, 0.0] not in stored


async def test_polygon_flow_does_not_auto_complete_at_fifteen_points(hass) -> None:
    """The flow should allow more than fifteen points until the user finishes."""
    flow_id = await _start_polygon_flow(hass, name="Large Polygon Zone")

    for index in range(15):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input={
                CONF_LATITUDE: 0.0,
                CONF_LONGITUDE: index * 0.01,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"


async def test_self_intersecting_polygon_is_rejected_when_finishing(hass) -> None:
    """A bow-tie polygon should be rejected as invalid authoring."""
    flow_id = await _start_polygon_flow(hass, name="Bow Tie Zone")
    await _add_points(hass, flow_id, ((0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0)))

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={"finished": True},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result["errors"] == {"base": "self_intersection"}


async def test_new_entries_store_coordinates_as_structured_lists(hass) -> None:
    """New config entries should store polygon points as structured data."""
    flow_id = await _start_polygon_flow(hass, name="Structured Storage Zone")

    result = None
    for latitude, longitude, finished in (
        (0.0, 0.0, False),
        (0.0, 1.0, False),
        (1.0, 1.0, True),
    ):
        user_input = {
            CONF_LATITUDE: latitude,
            CONF_LONGITUDE: longitude,
        }
        if finished:
            user_input["finished"] = True
        result = await hass.config_entries.flow.async_configure(flow_id, user_input=user_input)

    assert result is not None
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_COORDINATES] == [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0]]


async def test_options_flow_updates_zone_in_place(hass) -> None:
    """Editing should update the existing config entry instead of creating a new one."""
    entry = await _setup_entry(
        hass,
        "Driveway",
        ["person.alice"],
        [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["description_placeholders"] == {
        "current_name": "Driveway",
        "current_tracker_count": "1",
        "current_point_count": "3",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Backyard",
            CONF_TRACKERS: ["person.alice", "person.bob"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            "polygon_edit_mode": "replace",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"

    for latitude, longitude in (
        (0.0, 0.0),
        (0.0, 2.0),
        (2.0, 2.0),
        (2.0, 0.0),
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_LATITUDE: latitude,
                CONF_LONGITUDE: longitude,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "point"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"finished": True},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_NAME] == "Backyard"
    assert entry.data[CONF_TRACKERS] == ["person.alice", "person.bob"]
    assert entry.data[CONF_COORDINATES] == [[0.0, 0.0], [0.0, 2.0], [2.0, 2.0], [2.0, 0.0]]


async def test_options_flow_rejects_blank_zone_name(hass) -> None:
    """Editing should not allow clearing the zone name."""
    entry = await _setup_entry(
        hass,
        "Driveway",
        ["person.alice"],
        [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: " ",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            "polygon_edit_mode": "keep",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {CONF_NAME: "empty_name"}


async def test_editing_zone_preserves_sensor_entity_id(hass) -> None:
    """Renaming a zone should not create a new entity identity."""
    entry = await _setup_entry(
        hass,
        "Driveway",
        ["person.alice"],
        [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Backyard",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            "polygon_edit_mode": "replace",
        },
    )

    for latitude, longitude, finished in (
        (0.0, 0.0, False),
        (0.0, 1.0, False),
        (1.0, 1.0, True),
    ):
        user_input = {
            CONF_LATITUDE: latitude,
            CONF_LONGITUDE: longitude,
        }
        if finished:
            user_input["finished"] = True
        result = await hass.config_entries.options.async_configure(result["flow_id"], user_input=user_input)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert hass.states.get("sensor.customzone_driveway") is not None
    assert hass.states.get("sensor.customzone_backyard") is None


async def test_options_point_step_describes_polygon_reentry(hass) -> None:
    """Replace mode should explain that the polygon is being re-entered."""
    entry = await _setup_entry(
        hass,
        "Driveway",
        ["person.alice"],
        [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0]],
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Driveway",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            "polygon_edit_mode": "replace",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result["description_placeholders"] == {
        "status_msg": "Point 1",
        "shape_desc": "Not a polygon yet",
        "existing_point_count": "4",
    }


async def test_options_flow_can_keep_existing_polygon_without_reentry(hass) -> None:
    """Rename or tracker edits should not force polygon re-entry when unchanged."""
    entry = await _setup_entry(
        hass,
        "Driveway",
        ["person.alice"],
        [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Backyard",
            CONF_TRACKERS: ["person.alice", "person.bob"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            "polygon_edit_mode": "keep",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_NAME] == "Backyard"
    assert entry.data[CONF_TRACKERS] == ["person.alice", "person.bob"]
    assert entry.data[CONF_COORDINATES] == [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0]]


async def test_options_flow_can_append_points_to_existing_polygon(hass) -> None:
    """Append mode should continue from the existing polygon points."""
    entry = await _setup_entry(
        hass,
        "Driveway",
        ["person.alice"],
        [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Driveway",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            "polygon_edit_mode": "append",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result["description_placeholders"] == {
        "status_msg": "Point 4",
        "shape_desc": "Triangle",
        "existing_point_count": "3",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_LATITUDE: 1.0,
            CONF_LONGITUDE: 0.0,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"finished": True},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_COORDINATES] == [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0]]


async def test_options_flow_can_remove_last_point_then_continue(hass) -> None:
    """Remove-last mode should trim the polygon before re-entry continues."""
    entry = await _setup_entry(
        hass,
        "Driveway",
        ["person.alice"],
        [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0]],
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Driveway",
            CONF_TRACKERS: ["person.alice"],
            CONF_ZONE_TYPE: ZONE_TYPE_POLYGON,
            "polygon_edit_mode": "remove_last",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"
    assert result["description_placeholders"] == {
        "status_msg": "Point 4",
        "shape_desc": "Triangle",
        "existing_point_count": "4",
    }

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_LATITUDE: 2.0,
            CONF_LONGITUDE: 0.0,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "point"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"finished": True},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_COORDINATES] == [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 0.0]]
