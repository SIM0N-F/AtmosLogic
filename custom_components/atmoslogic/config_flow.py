"""Config flow for AtmosLogic."""

from __future__ import annotations

from collections.abc import Mapping

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import area_registry, selector

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
    CONF_OUTDOOR_HUMIDITY_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    CONF_RAIN_ENTITY,
    CONF_RAIN_THRESHOLD,
    CONF_ROOM_AREAS,
    CONF_ROOM_CONFIGS,
    CONF_ROOM_TEMPERATURE_ENTITY,
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
    CONF_ROOM_1_NAME,
    CONF_ROOM_1_TEMPERATURE_ENTITY,
    CONF_ROOM_2_NAME,
    CONF_ROOM_2_TEMPERATURE_ENTITY,
    CONF_ROOM_3_NAME,
    CONF_ROOM_3_TEMPERATURE_ENTITY,
)
from .rooms import build_room_configs


def _entity_selector(domain: str) -> selector.EntitySelector:
    """Return a simple entity selector for a specific domain."""

    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domain))


def _area_selector() -> selector.AreaSelector:
    """Return a selector for Home Assistant areas."""

    return selector.AreaSelector(selector.AreaSelectorConfig(multiple=True, reorder=True))


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


def _build_core_schema(defaults: Mapping[str, object]) -> vol.Schema:
    """Build the core config form schema."""

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
                CONF_ROOM_AREAS,
                default=defaults.get(CONF_ROOM_AREAS, []),
            ): _area_selector(),
            vol.Optional(
                CONF_NOTIFICATIONS_ENABLED,
                default=defaults.get(CONF_NOTIFICATIONS_ENABLED, DEFAULT_NOTIFICATIONS_ENABLED),
            ): selector.BooleanSelector(),
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


def _prepare_core_schema_input(user_input: dict[str, object]) -> dict[str, object]:
    """Normalize optional values for schema validation."""

    prepared = dict(user_input)
    prepared.pop(CONF_ROOM_CONFIGS, None)
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
        if prepared.get(key) is None:
            prepared[key] = ""
    return prepared


def _clean_core_data(user_input: dict[str, object]) -> dict[str, object]:
    """Normalize empty optional entity ids to None."""

    cleaned = dict(user_input)
    cleaned.pop(CONF_ROOM_CONFIGS, None)
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


def _room_config_defaults(merged: Mapping[str, object]) -> list[dict[str, str]]:
    """Return the room configs already stored in the entry."""

    room_configs = merged.get(CONF_ROOM_CONFIGS)
    if not isinstance(room_configs, list):
        return []

    defaults: list[dict[str, str]] = []
    for room in room_configs:
        if not isinstance(room, Mapping):
            continue

        area_id = str(room.get("area_id") or "").strip()
        temperature_entity = str(room.get("temperature_entity") or "").strip()
        if not area_id:
            continue

        defaults.append(
            {
                "area_id": area_id,
                "temperature_entity": temperature_entity,
            }
        )

    return defaults


def _dedupe(values: list[str]) -> list[str]:
    """Deduplicate a list while preserving order."""

    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


class AtmosLogicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AtmosLogic."""

    VERSION = 1

    def __init__(self) -> None:
        self._core_data: dict[str, object] = {}
        self._selected_room_area_ids: list[str] = []
        self._room_configs: list[dict[str, str]] = []
        self._room_defaults_by_area_id: dict[str, str] = {}

    def _area_name(self, area_id: str) -> str:
        registry = area_registry.async_get(self.hass)
        area = registry.async_get_area(area_id)
        if area is not None and area.name:
            return area.name
        return area_id

    def _area_temperature_default(self, area_id: str) -> str | None:
        if area_id in self._room_defaults_by_area_id:
            return self._room_defaults_by_area_id[area_id] or None

        registry = area_registry.async_get(self.hass)
        area = registry.async_get_area(area_id)
        if area is None or not area.temperature_entity_id:
            return None
        return area.temperature_entity_id

    async def async_step_user(self, user_input: dict[str, object] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data = _clean_core_data(_build_core_schema({})(_prepare_core_schema_input(user_input)))
            except vol.Invalid:
                errors["base"] = "invalid_input"
            else:
                self._core_data = data
                title = str(self.context.get("title") or "AtmosLogic")
                return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_core_schema({}),
            errors=errors,
        )

    async def async_step_rooms(self, user_input: dict[str, object] | None = None):
        merged_defaults = dict(self._core_data)
        if user_input is None:
            return self.async_show_form(
                step_id="rooms",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_ROOM_AREAS,
                            default=_dedupe([room["area_id"] for room in _room_config_defaults(merged_defaults)]),
                        ): _area_selector(),
                    }
                ),
            )

        try:
            selected_area_ids = user_input.get(CONF_ROOM_AREAS, [])
            if not isinstance(selected_area_ids, list):
                raise vol.Invalid("room_areas must be a list")
            self._selected_room_area_ids = _dedupe([str(area_id) for area_id in selected_area_ids if str(area_id).strip()])
        except vol.Invalid:
            return self.async_show_form(
                step_id="rooms",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_ROOM_AREAS,
                            default=_dedupe([room["area_id"] for room in _room_config_defaults(merged_defaults)]),
                        ): _area_selector(),
                    }
                ),
                errors={"base": "invalid_input"},
            )

        self._room_configs = []
        self._room_defaults_by_area_id = {
            room["area_id"]: room["temperature_entity"]
            for room in _room_config_defaults(merged_defaults)
            if room.get("area_id")
        }

        if not self._selected_room_area_ids:
            return self._async_create_entry()

        return await self.async_step_room()

    async def async_step_room(self, user_input: dict[str, object] | None = None):
        if not self._selected_room_area_ids:
            return self._async_create_entry()

        if len(self._room_configs) >= len(self._selected_room_area_ids):
            return self._async_create_entry()

        area_id = self._selected_room_area_ids[len(self._room_configs)]
        area_name = self._area_name(area_id)
        default_temperature_entity = self._area_temperature_default(area_id)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ROOM_TEMPERATURE_ENTITY,
                    default=default_temperature_entity,
                ): _entity_selector("sensor"),
            }
        )

        if user_input is None:
            return self.async_show_form(
                step_id="room",
                data_schema=schema,
                description_placeholders={"room_name": area_name},
            )

        try:
            validated = schema(user_input)
        except vol.Invalid:
            return self.async_show_form(
                step_id="room",
                data_schema=schema,
                errors={"base": "invalid_input"},
                description_placeholders={"room_name": area_name},
            )

        self._room_configs.append(
            {
                "area_id": area_id,
                "temperature_entity": str(validated[CONF_ROOM_TEMPERATURE_ENTITY]),
            }
        )

        if len(self._room_configs) >= len(self._selected_room_area_ids):
            return self._async_create_entry()

        return await self.async_step_room()

    def _async_create_entry(self):
        data = dict(self._core_data)
        data[CONF_ROOM_CONFIGS] = list(self._room_configs)

        title = str(self.context.get("title") or "AtmosLogic")
        return self.async_create_entry(title=title, data=data)

    async def async_step_import(self, user_input: dict[str, object]) -> config_entries.ConfigFlowResult:
        """Import an AtmosLogic configuration payload."""

        room_configs = user_input.get(CONF_ROOM_CONFIGS)
        legacy_room_keys = (
            CONF_ROOM_1_NAME,
            CONF_ROOM_1_TEMPERATURE_ENTITY,
            CONF_ROOM_2_NAME,
            CONF_ROOM_2_TEMPERATURE_ENTITY,
            CONF_ROOM_3_NAME,
            CONF_ROOM_3_TEMPERATURE_ENTITY,
        )
        legacy_room_data = {key: user_input[key] for key in legacy_room_keys if key in user_input}
        core_input = dict(user_input)
        core_input.pop(CONF_ROOM_CONFIGS, None)
        for key in legacy_room_keys:
            core_input.pop(key, None)

        try:
            data = _clean_core_data(_build_core_schema({})(_prepare_core_schema_input(core_input)))
        except vol.Invalid:
            return self.async_abort(reason="invalid_input")

        if isinstance(room_configs, list):
            data[CONF_ROOM_CONFIGS] = room_configs
        data.update(legacy_room_data)

        title = str(self.context.get("title") or "AtmosLogic")
        return self.async_create_entry(title=title, data=data)


class AtmosLogicOptionsFlow(config_entries.OptionsFlow):
    """Handle options for AtmosLogic."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self._core_data: dict[str, object] = {}
        self._selected_room_area_ids: list[str] = []
        self._room_configs: list[dict[str, str]] = []
        self._room_defaults_by_area_id: dict[str, str] = {}

    def _merged(self) -> dict[str, object]:
        return {**self.config_entry.data, **self.config_entry.options, **self._core_data}

    async def async_step_init(self, user_input: dict[str, object] | None = None):
        merged = {**self.config_entry.data, **self.config_entry.options}
        room_defaults = _dedupe(
            [room.area_id for room in build_room_configs(self.hass, merged) if not room.area_id.startswith("legacy_room_")]
        )
        schema_defaults = {**merged, CONF_ROOM_AREAS: room_defaults}
        if user_input is not None:
            try:
                self._core_data = _clean_core_data(_build_core_schema(merged)(_prepare_core_schema_input(user_input)))
            except vol.Invalid:
                return self.async_show_form(
                    step_id="init",
                    data_schema=_build_core_schema(schema_defaults),
                    errors={"base": "invalid_input"},
                )
            return self.async_create_entry(title="", data=self._core_data)

        return self.async_show_form(
            step_id="init",
            data_schema=_build_core_schema(schema_defaults),
        )

    async def async_step_rooms(self, user_input: dict[str, object] | None = None):
        merged = self._merged()
        current_rooms = build_room_configs(self.hass, merged)
        current_area_ids = _dedupe(
            [room.area_id for room in current_rooms if not room.area_id.startswith("legacy_room_")]
        )
        has_modern_room_configs = CONF_ROOM_CONFIGS in merged

        if user_input is None:
            return self.async_show_form(
                step_id="rooms",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_ROOM_AREAS,
                            default=current_area_ids,
                        ): _area_selector(),
                    }
                ),
            )

        try:
            selected_area_ids = user_input.get(CONF_ROOM_AREAS, [])
            if not isinstance(selected_area_ids, list):
                raise vol.Invalid("room_areas must be a list")
            self._selected_room_area_ids = _dedupe([str(area_id) for area_id in selected_area_ids if str(area_id).strip()])
        except vol.Invalid:
            return self.async_show_form(
                step_id="rooms",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_ROOM_AREAS,
                            default=current_area_ids,
                        ): _area_selector(),
                    }
                ),
                errors={"base": "invalid_input"},
            )

        self._room_configs = []
        self._room_defaults_by_area_id = {
            room.area_id: room.temperature_entity
            for room in current_rooms
            if not room.area_id.startswith("legacy_room_")
        }

        if not self._selected_room_area_ids:
            data = dict(self._core_data)
            if has_modern_room_configs:
                data[CONF_ROOM_CONFIGS] = []
            return self.async_create_entry(title="", data=data)

        return await self.async_step_room()

    async def async_step_room(self, user_input: dict[str, object] | None = None):
        if not self._selected_room_area_ids:
            data = dict(self._core_data)
            if CONF_ROOM_CONFIGS in self._merged():
                data[CONF_ROOM_CONFIGS] = []
            return self.async_create_entry(title="", data=data)

        if len(self._room_configs) >= len(self._selected_room_area_ids):
            data = dict(self._core_data)
            data[CONF_ROOM_CONFIGS] = list(self._room_configs)
            return self.async_create_entry(title="", data=data)

        area_id = self._selected_room_area_ids[len(self._room_configs)]
        area_name = self._area_name(area_id)
        default_temperature_entity = self._area_temperature_default(area_id)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ROOM_TEMPERATURE_ENTITY,
                    default=default_temperature_entity,
                ): _entity_selector("sensor"),
            }
        )

        if user_input is None:
            return self.async_show_form(
                step_id="room",
                data_schema=schema,
                description_placeholders={"room_name": area_name},
            )

        try:
            validated = schema(user_input)
        except vol.Invalid:
            return self.async_show_form(
                step_id="room",
                data_schema=schema,
                errors={"base": "invalid_input"},
                description_placeholders={"room_name": area_name},
            )

        self._room_configs.append(
            {
                "area_id": area_id,
                "temperature_entity": str(validated[CONF_ROOM_TEMPERATURE_ENTITY]),
            }
        )

        if len(self._room_configs) >= len(self._selected_room_area_ids):
            data = dict(self._core_data)
            if self._room_configs:
                data[CONF_ROOM_CONFIGS] = list(self._room_configs)
            return self.async_create_entry(title="", data=data)

        return await self.async_step_room()

    def _area_name(self, area_id: str) -> str:
        registry = area_registry.async_get(self.hass)
        area = registry.async_get_area(area_id)
        if area is not None and area.name:
            return area.name
        return area_id

    def _area_temperature_default(self, area_id: str) -> str | None:
        if area_id in self._room_defaults_by_area_id:
            return self._room_defaults_by_area_id[area_id] or None

        registry = area_registry.async_get(self.hass)
        area = registry.async_get_area(area_id)
        if area is None or not area.temperature_entity_id:
            return None
        return area.temperature_entity_id


@callback
def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> AtmosLogicOptionsFlow:
    """Return the options flow handler."""

    return AtmosLogicOptionsFlow(config_entry)
