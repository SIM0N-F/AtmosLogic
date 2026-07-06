"""Dataclasses for AtmosLogic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .const import (
    DEFAULT_COMFORT_MARGIN,
    DEFAULT_COVERS_ENABLED,
    DEFAULT_HIGH_HUMIDITY_THRESHOLD,
    DEFAULT_LAUNDRY_ENABLED,
    DEFAULT_MODE,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DEFAULT_NOTIFY_COVER_CLOSE,
    DEFAULT_NOTIFY_COVER_OPEN,
    DEFAULT_NOTIFY_LAUNDRY_GOOD,
    DEFAULT_NOTIFY_WINDOW_CLOSE,
    DEFAULT_NOTIFY_WINDOW_OPEN,
    DEFAULT_RAIN_THRESHOLD,
    DEFAULT_STRONG_WIND_THRESHOLD,
    DEFAULT_TARGET_TEMPERATURE,
    DEFAULT_WINDOWS_ENABLED,
)


@dataclass(slots=True)
class AtmosLogicConfig:
    """User configuration for AtmosLogic."""

    indoor_temperature_entity: str
    outdoor_temperature_entity: str
    target_temperature: float = DEFAULT_TARGET_TEMPERATURE
    comfort_margin: float = DEFAULT_COMFORT_MARGIN
    strong_wind_threshold: float = DEFAULT_STRONG_WIND_THRESHOLD
    high_humidity_threshold: float = DEFAULT_HIGH_HUMIDITY_THRESHOLD
    rain_threshold: float = DEFAULT_RAIN_THRESHOLD
    mode: str = DEFAULT_MODE
    laundry_enabled: bool = DEFAULT_LAUNDRY_ENABLED
    windows_enabled: bool = DEFAULT_WINDOWS_ENABLED
    covers_enabled: bool = DEFAULT_COVERS_ENABLED
    notifications_enabled: bool = DEFAULT_NOTIFICATIONS_ENABLED
    notify_window_open: bool = DEFAULT_NOTIFY_WINDOW_OPEN
    notify_window_close: bool = DEFAULT_NOTIFY_WINDOW_CLOSE
    notify_cover_open: bool = DEFAULT_NOTIFY_COVER_OPEN
    notify_cover_close: bool = DEFAULT_NOTIFY_COVER_CLOSE
    notify_laundry_good: bool = DEFAULT_NOTIFY_LAUNDRY_GOOD
    indoor_humidity_entity: str | None = None
    outdoor_humidity_entity: str | None = None
    rain_entity: str | None = None
    wind_speed_entity: str | None = None
    wind_gust_entity: str | None = None
    solar_entity: str | None = None
    climate_entity: str | None = None
    weather_entity: str | None = None


@dataclass(slots=True)
class AtmosLogicInput:
    """Resolved environment data used by the recommendation engine."""

    indoor_temperature: float
    outdoor_temperature: float
    target_temperature: float = DEFAULT_TARGET_TEMPERATURE
    comfort_margin: float = DEFAULT_COMFORT_MARGIN
    indoor_humidity: float | None = None
    outdoor_humidity: float | None = None
    rain_detected: bool = False
    wind_speed: float | None = None
    wind_gust: float | None = None
    solar_value: float | None = None
    solar_unit: str | None = None
    weather_condition: str | None = None
    climate_current_temperature: float | None = None
    climate_hvac_action: str | None = None


@dataclass(slots=True)
class AtmosLogicRecommendation:
    """Calculated recommendation snapshot."""

    home_mode: str
    window_recommendation: str
    cover_recommendation: str
    laundry_score: int
    laundry_recommendation: str
    thermal_score: int
    open_windows_recommended: bool
    close_windows_recommended: bool
    open_covers_recommended: bool
    close_covers_recommended: bool
    good_for_laundry: bool
    details: dict[str, Any] = field(default_factory=dict)
