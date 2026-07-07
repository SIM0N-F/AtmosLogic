"""Constants for AtmosLogic."""

from __future__ import annotations

try:
    from homeassistant.const import Platform
except ModuleNotFoundError:  # pragma: no cover - test environment fallback
    class Platform:  # type: ignore[override]
        """Minimal fallback for tests without Home Assistant installed."""

        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"
        SWITCH = "switch"

DOMAIN = "atmoslogic"
NAME = "AtmosLogic"

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH)

CONF_INDOOR_TEMPERATURE_ENTITY = "indoor_temperature_entity"
CONF_OUTDOOR_TEMPERATURE_ENTITY = "outdoor_temperature_entity"
CONF_TARGET_TEMPERATURE = "target_temperature"
CONF_INDOOR_HUMIDITY_ENTITY = "indoor_humidity_entity"
CONF_OUTDOOR_HUMIDITY_ENTITY = "outdoor_humidity_entity"
CONF_RAIN_ENTITY = "rain_entity"
CONF_WIND_SPEED_ENTITY = "wind_speed_entity"
CONF_WIND_GUST_ENTITY = "wind_gust_entity"
CONF_SOLAR_ENTITY = "solar_entity"
CONF_CLIMATE_ENTITY = "climate_entity"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_COMFORT_MARGIN = "comfort_margin"
CONF_STRONG_WIND_THRESHOLD = "strong_wind_threshold"
CONF_HIGH_HUMIDITY_THRESHOLD = "high_humidity_threshold"
CONF_RAIN_THRESHOLD = "rain_threshold"
CONF_NOTIFICATIONS_ENABLED = "notifications_enabled"
CONF_NOTIFY_WINDOW_OPEN = "notify_window_open"
CONF_NOTIFY_WINDOW_CLOSE = "notify_window_close"
CONF_NOTIFY_COVER_OPEN = "notify_cover_open"
CONF_NOTIFY_COVER_CLOSE = "notify_cover_close"
CONF_NOTIFY_LAUNDRY_GOOD = "notify_laundry_good"
CONF_MODE = "mode"
CONF_LAUNDRY_ENABLED = "laundry_enabled"
CONF_WINDOWS_ENABLED = "windows_enabled"
CONF_COVERS_ENABLED = "covers_enabled"
CONF_ROOM_1_NAME = "room_1_name"
CONF_ROOM_1_TEMPERATURE_ENTITY = "room_1_temperature_entity"
CONF_ROOM_2_NAME = "room_2_name"
CONF_ROOM_2_TEMPERATURE_ENTITY = "room_2_temperature_entity"
CONF_ROOM_3_NAME = "room_3_name"
CONF_ROOM_3_TEMPERATURE_ENTITY = "room_3_temperature_entity"

DEFAULT_TARGET_TEMPERATURE = 21.0
DEFAULT_COMFORT_MARGIN = 0.5
DEFAULT_STRONG_WIND_THRESHOLD = 35.0
DEFAULT_HIGH_HUMIDITY_THRESHOLD = 80.0
DEFAULT_RAIN_THRESHOLD = 0.1
DEFAULT_NOTIFICATIONS_ENABLED = False
DEFAULT_NOTIFY_WINDOW_OPEN = True
DEFAULT_NOTIFY_WINDOW_CLOSE = False
DEFAULT_NOTIFY_COVER_OPEN = False
DEFAULT_NOTIFY_COVER_CLOSE = False
DEFAULT_NOTIFY_LAUNDRY_GOOD = False
DEFAULT_MODE = "auto"
DEFAULT_LAUNDRY_ENABLED = True
DEFAULT_WINDOWS_ENABLED = True
DEFAULT_COVERS_ENABLED = True

MODE_AUTO = "auto"
MODE_SUMMER = "summer"
MODE_WINTER = "winter"
MODES: tuple[str, ...] = (MODE_AUTO, MODE_SUMMER, MODE_WINTER)

HOME_MODES: tuple[str, ...] = (
    "comfort",
    "cool_house",
    "heat_house",
    "preserve_cool",
    "preserve_heat",
    "ventilate",
)

WINDOW_RECOMMENDATIONS: tuple[str, ...] = (
    "open",
    "close",
    "keep_open",
    "keep_closed",
    "neutral",
)

COVER_RECOMMENDATIONS: tuple[str, ...] = (
    "open",
    "close",
    "partial",
    "neutral",
)

LAUNDRY_RECOMMENDATIONS: tuple[str, ...] = (
    "excellent",
    "good",
    "average",
    "poor",
    "impossible",
)

ENTITY_KEYS = (
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_RAIN_ENTITY,
    CONF_WIND_SPEED_ENTITY,
    CONF_WIND_GUST_ENTITY,
    CONF_SOLAR_ENTITY,
    CONF_CLIMATE_ENTITY,
    CONF_WEATHER_ENTITY,
)

ROOM_SLOT_DEFINITIONS: tuple[tuple[int, str, str], ...] = (
    (1, CONF_ROOM_1_NAME, CONF_ROOM_1_TEMPERATURE_ENTITY),
    (2, CONF_ROOM_2_NAME, CONF_ROOM_2_TEMPERATURE_ENTITY),
    (3, CONF_ROOM_3_NAME, CONF_ROOM_3_TEMPERATURE_ENTITY),
)

UPDATE_INTERVAL_MINUTES = 10
