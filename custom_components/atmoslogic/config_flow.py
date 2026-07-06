"""Config flow for AtmosLogic."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

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
    MODES,
)


def _build_schema(defaults: dict[str, object]) -> vol.Schema:
    """Build the config form schema."""

    return vol.Schema(
        {
            vol.Required(
                CONF_INDOOR_TEMPERATURE_ENTITY,
                default=defaults.get(CONF_INDOOR_TEMPERATURE_ENTITY, ""),
            ): cv.entity_id,
            vol.Required(
                CONF_OUTDOOR_TEMPERATURE_ENTITY,
                default=defaults.get(CONF_OUTDOOR_TEMPERATURE_ENTITY, ""),
            ): cv.entity_id,
            vol.Optional(
                CONF_TARGET_TEMPERATURE,
                default=defaults.get(CONF_TARGET_TEMPERATURE, DEFAULT_TARGET_TEMPERATURE),
            ): vol.All(vol.Coerce(float), vol.Range(min=5.0, max=35.0)),
            vol.Optional(
                CONF_INDOOR_HUMIDITY_ENTITY,
                default=defaults.get(CONF_INDOOR_HUMIDITY_ENTITY, ""),
            ): vol.Any(cv.entity_id, ""),
            vol.Optional(
                CONF_OUTDOOR_HUMIDITY_ENTITY,
                default=defaults.get(CONF_OUTDOOR_HUMIDITY_ENTITY, ""),
            ): vol.Any(cv.entity_id, ""),
            vol.Optional(CONF_RAIN_ENTITY, default=defaults.get(CONF_RAIN_ENTITY, "")): vol.Any(cv.entity_id, ""),
            vol.Optional(
                CONF_WIND_SPEED_ENTITY,
                default=defaults.get(CONF_WIND_SPEED_ENTITY, ""),
            ): vol.Any(cv.entity_id, ""),
            vol.Optional(CONF_WIND_GUST_ENTITY, default=defaults.get(CONF_WIND_GUST_ENTITY, "")): vol.Any(cv.entity_id, ""),
            vol.Optional(CONF_SOLAR_ENTITY, default=defaults.get(CONF_SOLAR_ENTITY, "")): vol.Any(cv.entity_id, ""),
            vol.Optional(CONF_CLIMATE_ENTITY, default=defaults.get(CONF_CLIMATE_ENTITY, "")): vol.Any(cv.entity_id, ""),
            vol.Optional(CONF_WEATHER_ENTITY, default=defaults.get(CONF_WEATHER_ENTITY, "")): vol.Any(cv.entity_id, ""),
            vol.Optional(
                CONF_COMFORT_MARGIN,
                default=defaults.get(CONF_COMFORT_MARGIN, DEFAULT_COMFORT_MARGIN),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=5.0)),
            vol.Optional(
                CONF_STRONG_WIND_THRESHOLD,
                default=defaults.get(CONF_STRONG_WIND_THRESHOLD, DEFAULT_STRONG_WIND_THRESHOLD),
            ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=200.0)),
            vol.Optional(
                CONF_HIGH_HUMIDITY_THRESHOLD,
                default=defaults.get(CONF_HIGH_HUMIDITY_THRESHOLD, DEFAULT_HIGH_HUMIDITY_THRESHOLD),
            ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=100.0)),
            vol.Optional(
                CONF_RAIN_THRESHOLD,
                default=defaults.get(CONF_RAIN_THRESHOLD, DEFAULT_RAIN_THRESHOLD),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1000.0)),
            vol.Optional(CONF_MODE, default=defaults.get(CONF_MODE, DEFAULT_MODE)): vol.In(MODES),
            vol.Optional(
                CONF_LAUNDRY_ENABLED,
                default=defaults.get(CONF_LAUNDRY_ENABLED, DEFAULT_LAUNDRY_ENABLED),
            ): cv.boolean,
            vol.Optional(
                CONF_WINDOWS_ENABLED,
                default=defaults.get(CONF_WINDOWS_ENABLED, DEFAULT_WINDOWS_ENABLED),
            ): cv.boolean,
            vol.Optional(
                CONF_COVERS_ENABLED,
                default=defaults.get(CONF_COVERS_ENABLED, DEFAULT_COVERS_ENABLED),
            ): cv.boolean,
        }
    )


def _clean_data(user_input: dict[str, object]) -> dict[str, object]:
    """Normalize empty optional entity ids to None."""

    cleaned = dict(user_input)
    for key in (
        CONF_INDOOR_HUMIDITY_ENTITY,
        CONF_OUTDOOR_HUMIDITY_ENTITY,
        CONF_RAIN_ENTITY,
        CONF_WIND_SPEED_ENTITY,
        CONF_WIND_GUST_ENTITY,
        CONF_SOLAR_ENTITY,
        CONF_CLIMATE_ENTITY,
        CONF_WEATHER_ENTITY,
    ):
        if cleaned.get(key) == "":
            cleaned[key] = None
    return cleaned


class AtmosLogicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AtmosLogic."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, object] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data = _clean_data(_build_schema({})(user_input))
            except vol.Invalid:
                errors["base"] = "invalid_input"
            else:
                return self.async_create_entry(title="AtmosLogic", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema({}),
            errors=errors,
        )


class AtmosLogicOptionsFlow(config_entries.OptionsFlow):
    """Handle options for AtmosLogic."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, object] | None = None):
        if user_input is not None:
            try:
                data = _clean_data(_build_schema({**self.config_entry.data, **self.config_entry.options})(user_input))
            except vol.Invalid:
                return self.async_show_form(
                    step_id="init",
                    data_schema=_build_schema({**self.config_entry.data, **self.config_entry.options}),
                    errors={"base": "invalid_input"},
                )
            return self.async_create_entry(title="", data=data)

        merged = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(merged),
        )


async def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> AtmosLogicOptionsFlow:
    """Return the options flow handler."""

    return AtmosLogicOptionsFlow(config_entry)
