"""Coordinator for AtmosLogic."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_COMFORT_MARGIN,
    CONF_COVERS_ENABLED,
    CONF_HIGH_HUMIDITY_THRESHOLD,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_LAUNDRY_ENABLED,
    CONF_MODE,
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_RAIN_ENTITY,
    CONF_RAIN_THRESHOLD,
    CONF_SOLAR_ENTITY,
    CONF_STRONG_WIND_THRESHOLD,
    CONF_TARGET_TEMPERATURE,
    CONF_WEATHER_ENTITY,
    CONF_WINDOWS_ENABLED,
    CONF_WIND_GUST_ENTITY,
    CONF_WIND_SPEED_ENTITY,
    DEFAULT_COMFORT_MARGIN,
    DEFAULT_COVERS_ENABLED,
    DEFAULT_HIGH_HUMIDITY_THRESHOLD,
    DEFAULT_LAUNDRY_ENABLED,
    DEFAULT_MODE,
    DEFAULT_RAIN_THRESHOLD,
    DEFAULT_STRONG_WIND_THRESHOLD,
    DEFAULT_TARGET_TEMPERATURE,
    DEFAULT_WINDOWS_ENABLED,
    DOMAIN,
    UPDATE_INTERVAL_MINUTES,
)
from .models import AtmosLogicConfig, AtmosLogicInput, AtmosLogicRecommendation
from .recommendation_engine import compute_recommendation

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
        return (
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
        )

    async def _handle_state_change(self, _event: object) -> None:
        await self.async_request_refresh()

    async def _async_update_data(self) -> AtmosLogicRecommendation | None:
        config = self.config
        reading = self._build_input(config)
        if reading is None:
            return None
        return compute_recommendation(config, reading)

    def _build_input(self, config: AtmosLogicConfig) -> AtmosLogicInput | None:
        indoor_temperature = self._read_numeric(config.indoor_temperature_entity)
        outdoor_temperature = self._read_numeric(config.outdoor_temperature_entity)
        if indoor_temperature is None or outdoor_temperature is None:
            return None

        weather_state = self.hass.states.get(config.weather_entity) if config.weather_entity else None
        climate_state = self.hass.states.get(config.climate_entity) if config.climate_entity else None

        rain_detected = self._read_bool(config.rain_entity)
        wind_speed = self._read_numeric(config.wind_speed_entity)
        wind_gust = self._read_numeric(config.wind_gust_entity)
        solar_value, solar_unit = self._read_solar(config.solar_entity)

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

    def _read_state_attribute(self, state: State, attribute: str) -> float | None:
        value = state.attributes.get(attribute)
        return _coerce_float(value)
