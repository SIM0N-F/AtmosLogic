"""Coordinator for AtmosLogic."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from datetime import timezone
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_COMFORT_MARGIN,
    CONF_COVERS_ENABLED,
    CONF_HIGH_HUMIDITY_THRESHOLD,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_LAUNDRY_ENABLED,
    CONF_MODE,
    CONF_NOTIFICATIONS_ENABLED,
    CONF_NOTIFY_ROOM_RECOMMENDATIONS,
    CONF_NOTIFY_SUMMARY,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_RAIN_ENTITY,
    CONF_RAIN_THRESHOLD,
    CONF_SOLAR_ENTITY,
    CONF_STRONG_WIND_THRESHOLD,
    CONF_TARGET_TEMPERATURE,
    CONF_NOTIFY_COVER_CLOSE,
    CONF_NOTIFY_COVER_OPEN,
    CONF_NOTIFY_LAUNDRY_GOOD,
    CONF_NOTIFY_WINDOW_CLOSE,
    CONF_NOTIFY_WINDOW_OPEN,
    CONF_BINARY_SENSORS_ENABLED,
    CONF_WEATHER_ENTITY,
    CONF_WINDOWS_ENABLED,
    CONF_WIND_GUST_ENTITY,
    CONF_WIND_SPEED_ENTITY,
    DEFAULT_COMFORT_MARGIN,
    DEFAULT_COVERS_ENABLED,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DEFAULT_NOTIFY_COVER_CLOSE,
    DEFAULT_NOTIFY_COVER_OPEN,
    DEFAULT_NOTIFY_LAUNDRY_GOOD,
    DEFAULT_NOTIFY_WINDOW_CLOSE,
    DEFAULT_NOTIFY_WINDOW_OPEN,
    DEFAULT_BINARY_SENSORS_ENABLED,
    DEFAULT_HIGH_HUMIDITY_THRESHOLD,
    DEFAULT_LAUNDRY_ENABLED,
    DEFAULT_MODE,
    DEFAULT_RAIN_THRESHOLD,
    DEFAULT_NOTIFY_ROOM_RECOMMENDATIONS,
    DEFAULT_NOTIFY_SUMMARY,
    DEFAULT_STRONG_WIND_THRESHOLD,
    DEFAULT_TARGET_TEMPERATURE,
    DEFAULT_WINDOWS_ENABLED,
    DOMAIN,
    UPDATE_INTERVAL_MINUTES,
)
from .models import AtmosLogicConfig, AtmosLogicInput, AtmosLogicRecommendation
from .notification_rules import build_notification_batch
from .recommendation_engine import compute_recommendation
from .rooms import build_room_configs

_LOGGER = logging.getLogger(__name__)


def _coerce_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(state: State | None) -> bool:
    if state is None:
        return False

    normalized = state.state.lower().strip()
    if normalized in {"on", "true", "yes", "home", "open", "rainy", "pouring", "wet"}:
        return True
    if normalized in {"off", "false", "no", "closed", "dry", "clear", "not_raining"}:
        return False

    numeric = _coerce_float(state.state)
    return bool(numeric and numeric > 0)


class AtmosLogicCoordinator(DataUpdateCoordinator[AtmosLogicRecommendation | None]):
    """Coordinator that snapshots Home Assistant state into recommendations."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = entry
        self._unsubscribers: list[Callable[[], None]] = []
        self._last_recommendation: AtmosLogicRecommendation | None = None
        self._room_recommendations: dict[str, AtmosLogicRecommendation] = {}
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{entry.entry_id}",
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    @property
    def config(self) -> AtmosLogicConfig:
        """Build the current config snapshot from entry data and options."""

        merged = {**self.config_entry.data, **self.config_entry.options}
        return AtmosLogicConfig(
            indoor_temperature_entity=merged[CONF_INDOOR_TEMPERATURE_ENTITY],
            outdoor_temperature_entity=merged[CONF_OUTDOOR_TEMPERATURE_ENTITY],
            target_temperature=float(merged.get(CONF_TARGET_TEMPERATURE, DEFAULT_TARGET_TEMPERATURE)),
            comfort_margin=float(merged.get(CONF_COMFORT_MARGIN, DEFAULT_COMFORT_MARGIN)),
            strong_wind_threshold=float(merged.get(CONF_STRONG_WIND_THRESHOLD, DEFAULT_STRONG_WIND_THRESHOLD)),
            high_humidity_threshold=float(merged.get(CONF_HIGH_HUMIDITY_THRESHOLD, DEFAULT_HIGH_HUMIDITY_THRESHOLD)),
            rain_threshold=float(merged.get(CONF_RAIN_THRESHOLD, DEFAULT_RAIN_THRESHOLD)),
            mode=str(merged.get(CONF_MODE, DEFAULT_MODE)),
            laundry_enabled=bool(merged.get(CONF_LAUNDRY_ENABLED, DEFAULT_LAUNDRY_ENABLED)),
            windows_enabled=bool(merged.get(CONF_WINDOWS_ENABLED, DEFAULT_WINDOWS_ENABLED)),
            covers_enabled=bool(merged.get(CONF_COVERS_ENABLED, DEFAULT_COVERS_ENABLED)),
            notifications_enabled=bool(merged.get(CONF_NOTIFICATIONS_ENABLED, DEFAULT_NOTIFICATIONS_ENABLED)),
            notify_summary=bool(merged.get(CONF_NOTIFY_SUMMARY, DEFAULT_NOTIFY_SUMMARY)),
            notify_room_recommendations=bool(
                merged.get(CONF_NOTIFY_ROOM_RECOMMENDATIONS, DEFAULT_NOTIFY_ROOM_RECOMMENDATIONS)
            ),
            notify_window_open=bool(merged.get(CONF_NOTIFY_WINDOW_OPEN, DEFAULT_NOTIFY_WINDOW_OPEN)),
            notify_window_close=bool(merged.get(CONF_NOTIFY_WINDOW_CLOSE, DEFAULT_NOTIFY_WINDOW_CLOSE)),
            notify_cover_open=bool(merged.get(CONF_NOTIFY_COVER_OPEN, DEFAULT_NOTIFY_COVER_OPEN)),
            notify_cover_close=bool(merged.get(CONF_NOTIFY_COVER_CLOSE, DEFAULT_NOTIFY_COVER_CLOSE)),
            notify_laundry_good=bool(merged.get(CONF_NOTIFY_LAUNDRY_GOOD, DEFAULT_NOTIFY_LAUNDRY_GOOD)),
            binary_sensors_enabled=bool(merged.get(CONF_BINARY_SENSORS_ENABLED, DEFAULT_BINARY_SENSORS_ENABLED)),
            room_configs=build_room_configs(self.hass, merged),
            indoor_humidity_entity=merged.get(CONF_INDOOR_HUMIDITY_ENTITY) or None,
            outdoor_humidity_entity=merged.get(CONF_OUTDOOR_HUMIDITY_ENTITY) or None,
            rain_entity=merged.get(CONF_RAIN_ENTITY) or None,
            wind_speed_entity=merged.get(CONF_WIND_SPEED_ENTITY) or None,
            wind_gust_entity=merged.get(CONF_WIND_GUST_ENTITY) or None,
            solar_entity=merged.get(CONF_SOLAR_ENTITY) or None,
            climate_entity=merged.get(CONF_CLIMATE_ENTITY) or None,
            weather_entity=merged.get(CONF_WEATHER_ENTITY) or None,
        )

    async def async_setup(self) -> None:
        """Start listening to entity updates."""

        entity_ids = [
            entity_id
            for entity_id in self._watched_entities
            if entity_id is not None
        ]
        if entity_ids:
            self._unsubscribers.append(
                async_track_state_change_event(self.hass, entity_ids, self._handle_state_change)
            )
        await self.async_config_entry_first_refresh()

    async def async_unload(self) -> None:
        """Remove all listeners."""

        while self._unsubscribers:
            unsubscribe = self._unsubscribers.pop()
            unsubscribe()

    @property
    def _watched_entities(self) -> tuple[str | None, ...]:
        config = self.config
        entities: list[str | None] = [
            config.indoor_temperature_entity,
            config.outdoor_temperature_entity,
            config.indoor_humidity_entity,
            config.outdoor_humidity_entity,
            config.rain_entity,
            config.wind_speed_entity,
            config.wind_gust_entity,
            config.solar_entity,
            config.climate_entity,
            config.weather_entity,
            *[room.temperature_entity for room in config.room_configs],
        ]
        deduped: list[str | None] = []
        for entity_id in entities:
            if entity_id is not None and entity_id not in deduped:
                deduped.append(entity_id)
        return tuple(deduped)

    def _handle_state_change(self, _event: object) -> None:
        self.hass.add_job(self.async_request_refresh)

    async def _async_update_data(self) -> AtmosLogicRecommendation | None:
        config = self.config
        previous_recommendation = self._last_recommendation
        previous_room_recommendations = dict(self._room_recommendations)
        recommendation = self._build_recommendation_for_entity(
            config,
            config.indoor_temperature_entity,
        )
        self._room_recommendations = {}
        for room in config.room_configs:
            self._room_recommendations[room.key] = self._build_recommendation_for_entity(
                config,
                room.temperature_entity,
                room_key=room.key,
                room_name=room.name,
            )

        await self._maybe_send_notifications(
            config,
            previous_recommendation,
            recommendation,
            previous_room_recommendations,
            dict(self._room_recommendations),
            self.home_summary(),
        )
        self._last_recommendation = recommendation
        return recommendation

    def _fallback_recommendation(
        self,
        config: AtmosLogicConfig,
        *,
        missing_inputs: list[str | None],
    ) -> AtmosLogicRecommendation:
        missing = [entity_id for entity_id in missing_inputs if entity_id]
        return AtmosLogicRecommendation(
            home_mode="comfort",
            window_recommendation="neutral",
            cover_recommendation="neutral",
            laundry_score=50,
            laundry_recommendation="average",
            thermal_score=0,
            open_windows_recommended=False,
            close_windows_recommended=False,
            open_covers_recommended=False,
            close_covers_recommended=False,
            good_for_laundry=False,
            details={
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
                "inputs": {},
                "signals": {},
                "confidence": 0,
                "reasons": {
                    "home": ["missing_inputs"],
                    "room": ["missing_inputs"],
                    "window": ["missing_inputs"],
                    "cover": ["missing_inputs"],
                    "laundry": ["missing_inputs"],
                },
                "breakdown": {
                    "thermal_score": 0,
                    "laundry_components": [
                        {
                            "reason": "missing_inputs",
                            "delta": 0,
                            "missing": missing,
                        }
                    ],
                },
                "recommendations": {
                    "home_mode": "comfort",
                    "window_recommendation": "neutral",
                    "cover_recommendation": "neutral",
                    "laundry_recommendation": "average",
                },
                "summary": {
                    "home_mode": "comfort",
                    "window_recommendation": "neutral",
                    "cover_recommendation": "neutral",
                    "laundry_recommendation": "average",
                    "thermal_score": 0,
                    "laundry_score": 50,
                },
                "missing_inputs": missing,
                "data_valid": False,
            },
        )

    def _build_recommendation_for_entity(
        self,
        config: AtmosLogicConfig,
        indoor_temperature_entity: str,
        *,
        room_key: str | None = None,
        room_name: str | None = None,
    ) -> AtmosLogicRecommendation:
        reading = self._build_input(config, indoor_temperature_entity)
        if reading is None:
            recommendation = self._fallback_recommendation(
                config,
                missing_inputs=[
                    indoor_temperature_entity,
                    config.outdoor_temperature_entity,
                ],
            )
        else:
            recommendation = compute_recommendation(config, reading)

        if room_key is not None:
            recommendation.details.setdefault(
                "room",
                {
                    "key": room_key,
                    "name": room_name or room_key,
                    "temperature_entity": indoor_temperature_entity,
                },
            )

        return recommendation

    async def _maybe_send_notifications(
        self,
        config: AtmosLogicConfig,
        previous: AtmosLogicRecommendation | None,
        recommendation: AtmosLogicRecommendation,
        previous_room_recommendations: dict[str, AtmosLogicRecommendation],
        current_room_recommendations: dict[str, AtmosLogicRecommendation],
        home_summary: dict[str, Any],
    ) -> None:
        """Send configured notifications when recommendations rise."""

        notifications = build_notification_batch(
            config,
            previous,
            recommendation,
            previous_room_recommendations=previous_room_recommendations,
            current_room_recommendations=current_room_recommendations,
            home_summary=home_summary,
        )
        if not notifications:
            return

        message = "\n".join(f"- {notification.message}" for notification in notifications)
        if self.hass.services.has_service("notify", "notify"):
            await self.hass.services.async_call(
                "notify",
                "notify",
                {
                    "title": "AtmosLogic",
                    "message": message,
                },
                blocking=False,
            )
            return

        _LOGGER.debug("AtmosLogic notify.notify service is not available; using persistent notification fallback")
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "AtmosLogic",
                "message": message,
            },
            blocking=False,
        )

    @property
    def room_recommendations(self) -> dict[str, AtmosLogicRecommendation]:
        """Return the most recent room recommendations."""

        return self._room_recommendations

    def room_summary(self, room_key: str) -> dict[str, Any] | None:
        """Return a flattened attribute payload for a room sensor."""

        room = next((room for room in self.config.room_configs if room.key == room_key), None)
        recommendation = self._room_recommendations.get(room_key)
        if room is None or recommendation is None:
            return None

        details = recommendation.details
        return {
            "area_id": room.area_id,
            "name": room.name,
            "mode": recommendation.home_mode,
            "thermal_score": recommendation.thermal_score,
            "window_recommendation": recommendation.window_recommendation,
            "cover_recommendation": recommendation.cover_recommendation,
            "open_windows_recommended": recommendation.open_windows_recommended,
            "close_windows_recommended": recommendation.close_windows_recommended,
            "open_covers_recommended": recommendation.open_covers_recommended,
            "close_covers_recommended": recommendation.close_covers_recommended,
            "confidence": details.get("confidence", 0),
            "reasons": details.get("reasons", {}).get("room", []),
            "indoor_temperature": details.get("inputs", {}).get("indoor_temperature"),
            "outdoor_temperature": details.get("inputs", {}).get("outdoor_temperature"),
            "target_temperature": details.get("inputs", {}).get("target_temperature"),
        }

    def laundry_summary(self) -> dict[str, Any]:
        """Return a flattened attribute payload for the laundry sensor."""

        recommendation = self.data
        if recommendation is None:
            return {}

        details = recommendation.details
        inputs = details.get("inputs", {})
        signals = details.get("signals", {})
        return {
            "score": recommendation.laundry_score,
            "drying_time_estimation": None,
            "rain_risk": bool(signals.get("rain_detected") or signals.get("rain_forecast")),
            "humidity": inputs.get("outdoor_humidity"),
            "wind": inputs.get("wind_speed") or inputs.get("wind_gust"),
            "temperature": inputs.get("outdoor_temperature"),
            "reasons": details.get("reasons", {}).get("laundry", []),
            "confidence": details.get("confidence", 0),
        }

    def home_summary(self) -> dict[str, Any]:
        """Return a flattened attribute payload for the house sensor."""

        recommendation = self.data
        if recommendation is None:
            return {}

        rooms: list[dict[str, Any]] = []
        for room in self.config.room_configs:
            room_recommendation = self._room_recommendations.get(room.key)
            if room_recommendation is None:
                continue
            room_summary = self.room_summary(room.key)
            if room_summary is None:
                continue
            rooms.append(
                {
                    **room_summary,
                    "next_action_recommended": self._room_next_action(room_recommendation),
                }
            )

        global_score = self._global_score(rooms, recommendation)
        priority_room = self._priority_room(rooms)
        next_action = self._next_action(rooms)

        return {
            "room_count": len(self.config.room_configs),
            "rooms": rooms,
            "next_action_recommended": next_action,
            "priority_room": priority_room.get("name") if priority_room else None,
            "global_score": global_score,
            "home_mode": recommendation.home_mode,
            "thermal_score": recommendation.thermal_score,
            "window_recommendation": recommendation.window_recommendation,
            "cover_recommendation": recommendation.cover_recommendation,
            "laundry_recommendation": recommendation.laundry_recommendation,
            "laundry_score": recommendation.laundry_score,
            "confidence": recommendation.details.get("confidence", 0),
            "reasons": recommendation.details.get("reasons", {}).get("home", []),
        }

    @staticmethod
    def _room_next_action(recommendation: AtmosLogicRecommendation) -> str:
        if recommendation.close_windows_recommended:
            return "close_windows"
        if recommendation.open_windows_recommended:
            return "open_windows"
        if recommendation.close_covers_recommended:
            return "close_covers"
        if recommendation.open_covers_recommended:
            return "open_covers"
        if recommendation.good_for_laundry:
            return "laundry"
        return "none"

    @classmethod
    def _priority_room(cls, rooms: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not rooms:
            return None
        return max(
            rooms,
            key=lambda room: (
                abs(float(room.get("thermal_score") or 0)),
                room.get("confidence", 0),
            ),
        )

    @classmethod
    def _next_action(cls, rooms: list[dict[str, Any]]) -> str:
        priority = {
            "close_windows": 5,
            "open_windows": 4,
            "close_covers": 3,
            "open_covers": 2,
            "laundry": 1,
            "none": 0,
        }
        best_action = "none"
        best_rank = 0
        for room in rooms:
            next_action = str(room.get("next_action_recommended") or "none")
            rank = priority.get(next_action, 0)
            if rank > best_rank:
                best_action = next_action
                best_rank = rank
        return best_action

    @staticmethod
    def _global_score(rooms: list[dict[str, Any]], recommendation: AtmosLogicRecommendation) -> int:
        scores = [int(room.get("thermal_score") or 0) for room in rooms]
        if not scores:
            return int(recommendation.thermal_score)
        return int(round(sum(scores) / len(scores)))

    def _build_input(self, config: AtmosLogicConfig, indoor_temperature_entity: str) -> AtmosLogicInput | None:
        indoor_temperature = self._read_numeric(indoor_temperature_entity)
        outdoor_temperature = self._read_numeric(config.outdoor_temperature_entity)
        if indoor_temperature is None or outdoor_temperature is None:
            return None

        weather_state = self.hass.states.get(config.weather_entity) if config.weather_entity else None
        climate_state = self.hass.states.get(config.climate_entity) if config.climate_entity else None
        sun_state = self.hass.states.get("sun.sun")

        rain_detected = self._read_bool(config.rain_entity)
        wind_speed = self._read_numeric(config.wind_speed_entity)
        wind_gust = self._read_numeric(config.wind_gust_entity)
        solar_value, solar_unit = self._read_solar(config.solar_entity)
        sun_above_horizon = self._sun_above_horizon(sun_state)
        weather_rain_forecast = self._weather_rain_forecast(weather_state, config.rain_threshold) if weather_state else False

        if weather_state is not None:
            weather_rain = self._weather_rain(weather_state, config.rain_threshold)
            rain_detected = rain_detected or weather_rain

            if wind_speed is None:
                wind_speed = self._read_state_attribute(weather_state, "wind_speed")
            if wind_gust is None:
                wind_gust = self._read_state_attribute(weather_state, "wind_gust")

            if solar_value is None:
                solar_value, solar_unit = self._weather_solar(weather_state)

            indoor_humidity = self._read_numeric(config.indoor_humidity_entity) if config.indoor_humidity_entity else None
            outdoor_humidity = (
                self._read_numeric(config.outdoor_humidity_entity)
                if config.outdoor_humidity_entity
                else self._read_state_attribute(weather_state, "humidity")
            )
        else:
            indoor_humidity = self._read_numeric(config.indoor_humidity_entity) if config.indoor_humidity_entity else None
            outdoor_humidity = self._read_numeric(config.outdoor_humidity_entity) if config.outdoor_humidity_entity else None

        if climate_state is not None:
            climate_current_temperature = self._read_state_attribute(climate_state, "current_temperature")
            climate_hvac_action = climate_state.attributes.get("hvac_action")
        else:
            climate_current_temperature = None
            climate_hvac_action = None

        if solar_value is None and weather_state is not None:
            solar_value, solar_unit = self._weather_solar(weather_state)

        if wind_speed is not None and wind_speed < 0:
            wind_speed = None
        if wind_gust is not None and wind_gust < 0:
            wind_gust = None

        return AtmosLogicInput(
            indoor_temperature=indoor_temperature,
            outdoor_temperature=outdoor_temperature,
            target_temperature=config.target_temperature,
            comfort_margin=config.comfort_margin,
            indoor_humidity=indoor_humidity,
            outdoor_humidity=outdoor_humidity,
            rain_detected=rain_detected,
            wind_speed=wind_speed,
            wind_gust=wind_gust,
            solar_value=solar_value,
            solar_unit=solar_unit,
            sun_above_horizon=sun_above_horizon,
            weather_rain_forecast=weather_rain_forecast,
            weather_condition=weather_state.state if weather_state is not None else None,
            climate_current_temperature=climate_current_temperature,
            climate_hvac_action=str(climate_hvac_action) if climate_hvac_action is not None else None,
        )

    def _read_numeric(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        return _coerce_float(state.state)

    def _read_bool(self, entity_id: str | None) -> bool:
        if not entity_id:
            return False
        return _coerce_bool(self.hass.states.get(entity_id))

    def _read_solar(self, entity_id: str | None) -> tuple[float | None, str | None]:
        if not entity_id:
            return None, None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None, None
        value = _coerce_float(state.state)
        if value is None:
            return None, None
        unit = state.attributes.get("unit_of_measurement")
        return value, str(unit) if unit is not None else None

    def _weather_rain(self, state: State, rain_threshold: float) -> bool:
        condition = str(state.state).lower()
        if condition in {"rainy", "pouring", "lightning-rainy", "snowy", "hail"}:
            return True
        precipitation = self._read_state_attribute(state, "precipitation")
        precipitation_intensity = self._read_state_attribute(state, "precipitation_intensity")
        return any(
            value is not None and value >= rain_threshold
            for value in (precipitation, precipitation_intensity)
        )

    def _weather_solar(self, state: State) -> tuple[float | None, str | None]:
        uv_index = self._read_state_attribute(state, "uv_index")
        if uv_index is not None:
            return uv_index, "uv_index"

        cloud_coverage = self._read_state_attribute(state, "cloud_coverage")
        if cloud_coverage is not None:
            return max(0.0, 100.0 - cloud_coverage), "%"

        return None, None

    def _sun_above_horizon(self, state: State | None) -> bool | None:
        if state is None:
            return None

        normalized = state.state.lower().strip()
        if normalized == "above_horizon":
            return True
        if normalized == "below_horizon":
            return False
        return None

    def _weather_rain_forecast(self, state: State, rain_threshold: float) -> bool:
        forecasts = self._weather_forecasts(state)
        if not forecasts:
            return False

        horizon = dt_util.utcnow() + timedelta(hours=12)
        for forecast in forecasts[:6]:
            if not isinstance(forecast, dict):
                continue

            forecast_time = self._forecast_datetime(forecast)
            if forecast_time is not None and forecast_time > horizon:
                continue

            condition = forecast.get("condition")
            if isinstance(condition, str) and condition.lower().strip() in {"rainy", "pouring", "lightning-rainy", "snowy", "hail"}:
                return True

            precipitation = _coerce_float(forecast.get("precipitation"))
            precipitation_intensity = _coerce_float(forecast.get("precipitation_intensity"))
            if any(
                value is not None and value >= rain_threshold
                for value in (precipitation, precipitation_intensity)
            ):
                return True

        return False

    def _weather_forecasts(self, state: State) -> list[dict[str, object]]:
        for attribute in ("forecast_hourly", "forecast", "forecast_daily"):
            forecasts = state.attributes.get(attribute)
            if isinstance(forecasts, list):
                return [forecast for forecast in forecasts if isinstance(forecast, dict)]
        return []

    def _forecast_datetime(self, forecast: dict[str, object]):
        for key in ("datetime", "datetime_start", "time"):
            value = forecast.get(key)
            if isinstance(value, str):
                try:
                    parsed = dt_util.parse_datetime(value)
                    if parsed is not None and parsed.tzinfo is None:
                        return parsed.replace(tzinfo=timezone.utc)
                    return parsed
                except (ValueError, TypeError):
                    return None
        return None

    def _read_state_attribute(self, state: State, attribute: str) -> float | None:
        value = state.attributes.get(attribute)
        return _coerce_float(value)
