"""Config flow for AtmosLogic."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_COMFORT_MARGIN,
    CONF_COVERS_ENABLED,
    CONF_HIGH_HUMIDITY_THRESHOLD,
    CONF_INDOOR_HUMIDITY_ENTITY,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_LAUNDRY_ENABLED,
    CONF_MODE,
    CONF_NOTIFICATION_SERVICE,
    CONF_NOTIFICATIONS_ENABLED,
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
    CONF_WEATHER_ENTITY,
    CONF_WINDOWS_ENABLED,
    CONF_WIND_GUST_ENTITY,
    CONF_WIND_SPEED_ENTITY,
    DEFAULT_COMFORT_MARGIN,
    DEFAULT_COVERS_ENABLED,
    DEFAULT_NOTIFICATION_SERVICE,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DEFAULT_NOTIFY_COVER_CLOSE,
    DEFAULT_NOTIFY_COVER_OPEN,
    DEFAULT_NOTIFY_LAUNDRY_GOOD,
    DEFAULT_NOTIFY_WINDOW_CLOSE,
    DEFAULT_NOTIFY_WINDOW_OPEN,
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


def _entity_selector(domain: str) -> selector.EntitySelector:
    """Return a simple entity selector for a specific domain."""

    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domain))


def _number_selector(minimum: float, maximum: float, step: float) -> selector.NumberSelector:
    """Return a number selector for numeric thresholds."""

    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=step,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _build_schema(defaults: dict[str, object]) -> vol.Schema:
    """Build the config form schema."""

    return vol.Schema(
        {
            vol.Required(
                CONF_INDOOR_TEMPERATURE_ENTITY,
                default=defaults.get(CONF_INDOOR_TEMPERATURE_ENTITY),
            ): _entity_selector("sensor"),
            vol.Required(
                CONF_OUTDOOR_TEMPERATURE_ENTITY,
                default=defaults.get(CONF_OUTDOOR_TEMPERATURE_ENTITY),
            ): _entity_selector("sensor"),
            vol.Optional(
                CONF_TARGET_TEMPERATURE,
                default=defaults.get(CONF_TARGET_TEMPERATURE, DEFAULT_TARGET_TEMPERATURE),
            ): _number_selector(5.0, 35.0, 0.5),
            vol.Optional(
                CONF_INDOOR_HUMIDITY_ENTITY,
                default=defaults.get(CONF_INDOOR_HUMIDITY_ENTITY),
            ): _entity_selector("sensor"),
            vol.Optional(
                CONF_OUTDOOR_HUMIDITY_ENTITY,
                default=defaults.get(CONF_OUTDOOR_HUMIDITY_ENTITY),
            ): _entity_selector("sensor"),
            vol.Optional(
                CONF_RAIN_ENTITY,
                default=defaults.get(CONF_RAIN_ENTITY),
            ): selector.EntitySelector(selector.EntitySelectorConfig()),
            vol.Optional(
                CONF_WIND_SPEED_ENTITY,
                default=defaults.get(CONF_WIND_SPEED_ENTITY),
            ): _entity_selector("sensor"),
            vol.Optional(
                CONF_WIND_GUST_ENTITY,
                default=defaults.get(CONF_WIND_GUST_ENTITY),
            ): _entity_selector("sensor"),
            vol.Optional(
                CONF_SOLAR_ENTITY,
                default=defaults.get(CONF_SOLAR_ENTITY),
            ): _entity_selector("sensor"),
            vol.Optional(
                CONF_CLIMATE_ENTITY,
                default=defaults.get(CONF_CLIMATE_ENTITY),
            ): _entity_selector("climate"),
            vol.Optional(
                CONF_WEATHER_ENTITY,
                default=defaults.get(CONF_WEATHER_ENTITY),
            ): _entity_selector("weather"),
            vol.Optional(
                CONF_COMFORT_MARGIN,
                default=defaults.get(CONF_COMFORT_MARGIN, DEFAULT_COMFORT_MARGIN),
            ): _number_selector(0.1, 5.0, 0.1),
            vol.Optional(
                CONF_STRONG_WIND_THRESHOLD,
                default=defaults.get(CONF_STRONG_WIND_THRESHOLD, DEFAULT_STRONG_WIND_THRESHOLD),
            ): _number_selector(1.0, 200.0, 1.0),
            vol.Optional(
                CONF_HIGH_HUMIDITY_THRESHOLD,
                default=defaults.get(CONF_HIGH_HUMIDITY_THRESHOLD, DEFAULT_HIGH_HUMIDITY_THRESHOLD),
            ): _number_selector(1.0, 100.0, 1.0),
            vol.Optional(
                CONF_RAIN_THRESHOLD,
                default=defaults.get(CONF_RAIN_THRESHOLD, DEFAULT_RAIN_THRESHOLD),
            ): _number_selector(0.0, 1000.0, 0.1),
            vol.Optional(CONF_MODE, default=defaults.get(CONF_MODE, DEFAULT_MODE)): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(MODES))
            ),
            vol.Optional(
                CONF_LAUNDRY_ENABLED,
                default=defaults.get(CONF_LAUNDRY_ENABLED, DEFAULT_LAUNDRY_ENABLED),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_WINDOWS_ENABLED,
                default=defaults.get(CONF_WINDOWS_ENABLED, DEFAULT_WINDOWS_ENABLED),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_COVERS_ENABLED,
                default=defaults.get(CONF_COVERS_ENABLED, DEFAULT_COVERS_ENABLED),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NOTIFICATIONS_ENABLED,
                default=defaults.get(CONF_NOTIFICATIONS_ENABLED, DEFAULT_NOTIFICATIONS_ENABLED),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NOTIFICATION_SERVICE,
                default=defaults.get(CONF_NOTIFICATION_SERVICE, DEFAULT_NOTIFICATION_SERVICE),
            ): str,
            vol.Optional(
                CONF_NOTIFY_WINDOW_OPEN,
                default=defaults.get(CONF_NOTIFY_WINDOW_OPEN, DEFAULT_NOTIFY_WINDOW_OPEN),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NOTIFY_WINDOW_CLOSE,
                default=defaults.get(CONF_NOTIFY_WINDOW_CLOSE, DEFAULT_NOTIFY_WINDOW_CLOSE),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NOTIFY_COVER_OPEN,
                default=defaults.get(CONF_NOTIFY_COVER_OPEN, DEFAULT_NOTIFY_COVER_OPEN),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NOTIFY_COVER_CLOSE,
                default=defaults.get(CONF_NOTIFY_COVER_CLOSE, DEFAULT_NOTIFY_COVER_CLOSE),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NOTIFY_LAUNDRY_GOOD,
                default=defaults.get(CONF_NOTIFY_LAUNDRY_GOOD, DEFAULT_NOTIFY_LAUNDRY_GOOD),
            ): selector.BooleanSelector(),
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
        CONF_NOTIFICATION_SERVICE,
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
