"""Pure recommendation logic for AtmosLogic."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .const import (
    COVER_RECOMMENDATIONS,
    DEFAULT_COMFORT_MARGIN,
    LAUNDRY_RECOMMENDATIONS,
    MODE_AUTO,
    MODE_SUMMER,
    MODE_WINTER,
    WINDOW_RECOMMENDATIONS,
)
from .models import AtmosLogicConfig, AtmosLogicInput, AtmosLogicRecommendation


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a value to a range."""

    return max(minimum, min(maximum, value))


def _is_truthy_rain(condition: str | None) -> bool:
    if condition is None:
        return False
    normalized = condition.lower().strip()
    return normalized in {"rainy", "pouring", "pouring_rain", "lightning-rainy", "snowy", "hail"}


def _effective_wind_speed(reading: AtmosLogicInput) -> float | None:
    values = [value for value in (reading.wind_speed, reading.wind_gust) if value is not None]
    if not values:
        return None
    return max(values)


def _is_strong_wind(reading: AtmosLogicInput, threshold: float) -> bool:
    wind = _effective_wind_speed(reading)
    return wind is not None and wind >= threshold


def _solar_available(reading: AtmosLogicInput) -> bool:
    if reading.solar_value is None:
        return False

    unit = (reading.solar_unit or "").lower()
    value = reading.solar_value
    if "lux" in unit:
        return value >= 10000
    if "w/m" in unit or "watt" in unit:
        return value >= 200
    if "%" in unit:
        return value >= 60
    return value >= 500


def _is_night(reading: AtmosLogicInput) -> bool:
    if reading.sun_above_horizon is False:
        return True
    return False


def _confidence(reading: AtmosLogicInput) -> int:
    score = 100
    penalties = (
        (reading.indoor_humidity, 5),
        (reading.outdoor_humidity, 5),
        (reading.solar_value, 5),
        (reading.weather_condition, 5),
        (reading.climate_current_temperature, 5),
        (reading.climate_hvac_action, 5),
    )
    for value, penalty in penalties:
        if value is None:
            score -= penalty

    if reading.wind_speed is None and reading.wind_gust is None:
        score -= 10
    if reading.sun_above_horizon is None:
        score -= 5
    if not reading.weather_rain_forecast and reading.weather_condition is None:
        score -= 5

    return int(clamp(score, 0, 100))


def _thermal_reasons(reading: AtmosLogicInput, config: AtmosLogicConfig) -> list[str]:
    reasons: list[str] = []
    delta = reading.indoor_temperature - reading.target_temperature
    if abs(delta) <= config.comfort_margin:
        reasons.append("temperature_close_to_target")
    elif delta > 0:
        reasons.append("indoor_temperature_above_target")
    else:
        reasons.append("indoor_temperature_below_target")

    return reasons


def _rain_detected(config: AtmosLogicConfig, reading: AtmosLogicInput) -> bool:
    if reading.rain_detected:
        return True
    if reading.weather_condition and _is_truthy_rain(reading.weather_condition):
        return True
    return False


def _thermal_score(reading: AtmosLogicInput, config: AtmosLogicConfig) -> int:
    delta = reading.indoor_temperature - reading.target_temperature
    if abs(delta) <= config.comfort_margin:
        return 0

    margin = max(config.comfort_margin, DEFAULT_COMFORT_MARGIN / 10)
    score = int(round(abs(delta) / margin * 20))
    return int(clamp(score if delta < 0 else -score, -100, 100))


def _home_mode(config: AtmosLogicConfig, reading: AtmosLogicInput, rain: bool, strong_wind: bool) -> str:
    delta = reading.indoor_temperature - reading.target_temperature
    if abs(delta) <= config.comfort_margin:
        if config.mode == MODE_SUMMER:
            return "preserve_cool"
        if config.mode == MODE_WINTER:
            return "preserve_heat"
        return "comfort"

    if delta > config.comfort_margin:
        if not rain and not strong_wind and reading.outdoor_temperature < reading.indoor_temperature - 1:
            return "ventilate"
        if reading.outdoor_temperature >= reading.indoor_temperature:
            return "preserve_cool"
        return "cool_house"

    if reading.outdoor_temperature > reading.indoor_temperature:
        return "heat_house"
    if _solar_available(reading):
        return "heat_house"
    return "preserve_heat"


def _mode_reasons(
    config: AtmosLogicConfig,
    reading: AtmosLogicInput,
    rain: bool,
    strong_wind: bool,
) -> list[str]:
    reasons = _thermal_reasons(reading, config)
    if rain:
        reasons.append("rain_detected")
    if strong_wind:
        reasons.append("strong_wind_detected")
    if _solar_available(reading):
        reasons.append("solar_available")
    if _is_night(reading):
        reasons.append("nighttime")
    return reasons


def _window_recommendation(
    config: AtmosLogicConfig,
    reading: AtmosLogicInput,
    rain: bool,
    strong_wind: bool,
) -> str:
    if not config.windows_enabled:
        return "neutral"

    if rain or strong_wind:
        return "keep_closed"

    delta = reading.indoor_temperature - reading.target_temperature
    outside_vs_inside = reading.outdoor_temperature - reading.indoor_temperature

    if delta > config.comfort_margin:
        if outside_vs_inside <= -3:
            return "open"
        if outside_vs_inside <= -1:
            return "keep_open"
        return "keep_closed"

    if delta < -config.comfort_margin:
        if outside_vs_inside >= 1:
            return "open"
        return "close"

    if config.mode == MODE_WINTER:
        return "keep_closed"
    if config.mode == MODE_SUMMER and outside_vs_inside < -1:
        return "keep_open"
    return "neutral"


def _window_reasons(
    config: AtmosLogicConfig,
    reading: AtmosLogicInput,
    rain: bool,
    strong_wind: bool,
) -> list[str]:
    reasons: list[str] = []
    if not config.windows_enabled:
        reasons.append("module_disabled")
        return reasons
    if rain:
        reasons.append("rain_detected")
    if strong_wind:
        reasons.append("strong_wind_detected")

    delta = reading.indoor_temperature - reading.target_temperature
    outside_vs_inside = reading.outdoor_temperature - reading.indoor_temperature
    if delta > config.comfort_margin:
        reasons.append("indoor_hotter_than_target")
        if outside_vs_inside <= -3:
            reasons.append("outside_much_cooler")
        elif outside_vs_inside <= -1:
            reasons.append("outside_cooler")
        else:
            reasons.append("outside_not_cooler_enough")
    elif delta < -config.comfort_margin:
        reasons.append("indoor_cooler_than_target")
        if outside_vs_inside >= 1:
            reasons.append("outside_warmer")
        else:
            reasons.append("outside_not_warmer_enough")
    else:
        reasons.append("temperature_within_comfort_margin")

    return reasons


def _cover_recommendation(
    config: AtmosLogicConfig,
    reading: AtmosLogicInput,
    rain: bool,
    strong_wind: bool,
) -> str:
    if not config.covers_enabled:
        return "neutral"

    if rain or strong_wind:
        return "close"

    delta = reading.indoor_temperature - reading.target_temperature
    solar = _solar_available(reading)

    if delta > config.comfort_margin and reading.outdoor_temperature >= reading.indoor_temperature + 1:
        return "close"

    if delta < -config.comfort_margin and solar:
        return "open"

    if solar and abs(delta) <= config.comfort_margin:
        return "partial"

    if config.mode == MODE_WINTER and solar:
        return "open"
    if config.mode == MODE_SUMMER and delta > config.comfort_margin:
        return "close"

    return "neutral"


def _cover_reasons(
    config: AtmosLogicConfig,
    reading: AtmosLogicInput,
    rain: bool,
    strong_wind: bool,
) -> list[str]:
    reasons: list[str] = []
    if not config.covers_enabled:
        reasons.append("module_disabled")
        return reasons
    if rain:
        reasons.append("rain_detected")
    if strong_wind:
        reasons.append("strong_wind_detected")
    if _solar_available(reading):
        reasons.append("solar_available")

    delta = reading.indoor_temperature - reading.target_temperature
    if delta > config.comfort_margin and reading.outdoor_temperature >= reading.indoor_temperature + 1:
        reasons.append("outside_hotter_than_inside")
    elif delta < -config.comfort_margin and _solar_available(reading):
        reasons.append("warming_with_sunlight")
    elif config.mode == MODE_WINTER and _solar_available(reading):
        reasons.append("winter_sunlight")
    elif config.mode == MODE_SUMMER and delta > config.comfort_margin:
        reasons.append("summer_heat_protection")
    else:
        reasons.append("neutral_cover_strategy")

    return reasons


def _laundry_score(config: AtmosLogicConfig, reading: AtmosLogicInput, rain: bool, strong_wind: bool) -> tuple[int, list[dict[str, Any]]]:
    if not config.laundry_enabled:
        return 0, [{"reason": "module_disabled", "delta": 0}]

    score = 50
    components: list[dict[str, Any]] = [{"reason": "base", "delta": 50}]
    wind = _effective_wind_speed(reading)
    solar = _solar_available(reading)

    if reading.outdoor_temperature > 18:
        score += 20
        components.append({"reason": "mild_warm_weather", "delta": 20})
    elif 12 <= reading.outdoor_temperature <= 18:
        score += 10
        components.append({"reason": "moderate_temperature", "delta": 10})

    if reading.outdoor_humidity is not None:
        if reading.outdoor_humidity < 60:
            score += 15
            components.append({"reason": "dry_air", "delta": 15})
        elif reading.outdoor_humidity <= 75:
            score += 5
            components.append({"reason": "acceptable_humidity", "delta": 5})
        elif reading.outdoor_humidity > config.high_humidity_threshold:
            score -= 20
            components.append({"reason": "high_humidity", "delta": -20})

    if wind is not None and 5 <= wind <= 30:
        score += 15
        components.append({"reason": "helpful_wind", "delta": 15})

    if solar:
        score += 10
        components.append({"reason": "sunshine", "delta": 10})

    if rain:
        score -= 50
        components.append({"reason": "rain", "delta": -50})

    night = _is_night(reading)
    if night:
        score -= 35
        components.append({"reason": "nightfall", "delta": -35})

    if reading.weather_rain_forecast:
        score -= 35
        components.append({"reason": "rain_forecast", "delta": -35})

    if reading.outdoor_temperature < 8:
        score -= 15
        components.append({"reason": "too_cold", "delta": -15})

    if strong_wind:
        score -= 15
        components.append({"reason": "too_windy", "delta": -15})

    if night and reading.weather_rain_forecast:
        score = min(score, 20)
    elif night or reading.weather_rain_forecast:
        score = min(score, 35)

    score = int(clamp(score, 0, 100))
    return score, components


def _laundry_reasons(
    reading: AtmosLogicInput,
    rain: bool,
    strong_wind: bool,
    laundry_components: list[dict[str, Any]],
) -> list[str]:
    reasons = [str(component.get("reason")) for component in laundry_components if component.get("reason")]
    if rain:
        reasons.append("rain_detected")
    if strong_wind:
        reasons.append("strong_wind_detected")
    if _is_night(reading):
        reasons.append("nighttime")
    if reading.weather_rain_forecast:
        reasons.append("rain_forecast")
    return list(dict.fromkeys(reasons))


def _laundry_recommendation(score: int) -> str:
    if score >= 80:
        return "excellent"
    if score >= 60:
        return "good"
    if score >= 40:
        return "average"
    if score >= 20:
        return "poor"
    return "impossible"


def compute_recommendation(config: AtmosLogicConfig, reading: AtmosLogicInput) -> AtmosLogicRecommendation:
    """Compute a full AtmosLogic recommendation from a snapshot."""

    rain = _rain_detected(config, reading)
    strong_wind = _is_strong_wind(reading, config.strong_wind_threshold)
    confidence = _confidence(reading)
    thermal_score = _thermal_score(reading, config)
    home_mode = _home_mode(config, reading, rain, strong_wind)
    window_recommendation = _window_recommendation(config, reading, rain, strong_wind)
    cover_recommendation = _cover_recommendation(config, reading, rain, strong_wind)
    laundry_score, laundry_components = _laundry_score(config, reading, rain, strong_wind)
    laundry_recommendation = _laundry_recommendation(laundry_score)
    laundry_reasons = _laundry_reasons(reading, rain, strong_wind, laundry_components)

    details: dict[str, Any] = {
        "config": {
            "mode": config.mode,
            "comfort_margin": config.comfort_margin,
            "strong_wind_threshold": config.strong_wind_threshold,
            "high_humidity_threshold": config.high_humidity_threshold,
            "rain_threshold": config.rain_threshold,
            "windows_enabled": config.windows_enabled,
            "covers_enabled": config.covers_enabled,
            "laundry_enabled": config.laundry_enabled,
        },
        "inputs": asdict(reading),
        "signals": {
            "rain_detected": rain,
            "strong_wind": strong_wind,
            "solar_available": _solar_available(reading),
            "night": _is_night(reading),
            "rain_forecast": reading.weather_rain_forecast,
        },
        "confidence": confidence,
        "reasons": {
            "home": _mode_reasons(config, reading, rain, strong_wind),
            "room": _mode_reasons(config, reading, rain, strong_wind),
            "window": _window_reasons(config, reading, rain, strong_wind),
            "cover": _cover_reasons(config, reading, rain, strong_wind),
            "laundry": laundry_reasons,
        },
        "breakdown": {
            "thermal_score": thermal_score,
            "laundry_components": laundry_components,
        },
        "recommendations": {
            "home_mode": home_mode,
            "window_recommendation": window_recommendation,
            "cover_recommendation": cover_recommendation,
            "laundry_recommendation": laundry_recommendation,
        },
        "summary": {
            "home_mode": home_mode,
            "window_recommendation": window_recommendation,
            "cover_recommendation": cover_recommendation,
            "laundry_recommendation": laundry_recommendation,
            "thermal_score": thermal_score,
            "laundry_score": laundry_score,
        },
    }

    return AtmosLogicRecommendation(
        home_mode=home_mode,
        window_recommendation=window_recommendation,
        cover_recommendation=cover_recommendation,
        laundry_score=laundry_score,
        laundry_recommendation=laundry_recommendation,
        thermal_score=thermal_score,
        open_windows_recommended=window_recommendation in {"open", "keep_open"},
        close_windows_recommended=window_recommendation in {"close", "keep_closed"},
        open_covers_recommended=cover_recommendation in {"open", "partial"},
        close_covers_recommended=cover_recommendation == "close",
        good_for_laundry=laundry_recommendation in {"excellent", "good"},
        details=details,
    )
