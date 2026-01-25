"""Constants for the Custom Zone integration."""

DOMAIN = "custom_zone"

CONF_TRACKERS = "trackers"
CONF_NAME = "name"
CONF_COORDINATES = "coordinates"
CONF_ZONE_TYPE = "zone_type"

CONF_MAX_TRACKERS = 10

ZONE_TYPE_POLYGON = "polygon"

# Tolerance used for vertex/boundary checks (about 1 meter at the equator).
COORD_TOLERANCE = 1e-5
