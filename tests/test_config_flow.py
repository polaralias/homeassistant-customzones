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

    for latitude, longitude in ((0.0, 0.0), (0.0, 1.0), (1.0, 0.0)):
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
            CONF_LONGITUDE: 0.0,
            "finished": True,
        },
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

    for latitude, longitude in ((0.0, 0.0), (1.0, 1.0), (0.0, 1.0)):
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
            CONF_LATITUDE: 1.0,
            CONF_LONGITUDE: 0.0,
            "finished": True,
        },
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

    for latitude, longitude, finished in (
        (0.0, 0.0, False),
        (0.0, 2.0, False),
        (2.0, 2.0, False),
        (2.0, 0.0, True),
    ):
        user_input = {
            CONF_LATITUDE: latitude,
            CONF_LONGITUDE: longitude,
        }
        if finished:
            user_input["finished"] = True
        result = await hass.config_entries.options.async_configure(result["flow_id"], user_input=user_input)

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
            "finished": True,
        },
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
            "finished": True,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_COORDINATES] == [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 0.0]]
