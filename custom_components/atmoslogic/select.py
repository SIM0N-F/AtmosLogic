"""Select platform for AtmosLogic room configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from homeassistant.components.select import SelectEntity
    from homeassistant.const import EntityCategory
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers import area_registry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
except ModuleNotFoundError:  # pragma: no cover - test environment fallback
    from typing import Any as HomeAssistant  # type: ignore[assignment]

    class SelectEntity:  # type: ignore[override]
        """Fallback select entity for tests."""

    class EntityCategory:  # type: ignore[override]
        CONFIG = "config"

    class CoordinatorEntity:  # type: ignore[override]
        def __init__(self, coordinator: Any) -> None:
            self.coordinator = coordinator

        @classmethod
        def __class_getitem__(cls, _item: Any) -> Any:
            return cls

    class _AreaRegistryFallback:
        def async_get(self, _hass: Any) -> Any:
            raise ModuleNotFoundError

    area_registry = _AreaRegistryFallback()

    def AddEntitiesCallback(*args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        raise ModuleNotFoundError

from .const import CONF_ROOM_CONFIGS, CONF_ROOM_AREAS, DOMAIN
from .coordinator import AtmosLogicCoordinator
from .rooms import get_selected_area_ids


@dataclass(slots=True, frozen=True)
class AtmosLogicRoomSelectDescription:
    """Description of a room temperature selector."""

    area_id: str
    area_name: str


def _temperature_entity_options(hass: HomeAssistant) -> list[str]:
    options: list[str] = []
    for state in hass.states.async_all("sensor"):
        device_class = state.attributes.get("device_class")
        unit = str(state.attributes.get("unit_of_measurement") or "").strip()
        if device_class == "temperature" or unit in {"°C", "°F", "K"}:
            options.append(state.entity_id)
    return sorted(dict.fromkeys(options))


def _current_room_configs(merged: dict[str, Any]) -> dict[str, str]:
    current: dict[str, str] = {}
    room_configs = merged.get(CONF_ROOM_CONFIGS)
    if not isinstance(room_configs, list):
        return current

    for room_data in room_configs:
        if not isinstance(room_data, dict):
            continue
        area_id = str(room_data.get("area_id") or room_data.get("key") or "").strip()
        temperature_entity = str(room_data.get("temperature_entity") or room_data.get("temperature_entity_id") or "").strip()
        if area_id and temperature_entity:
            current[area_id] = temperature_entity
    return current


async def async_setup_entry(
    hass: HomeAssistant,
    entry: object,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AtmosLogic room selectors."""

    coordinator: AtmosLogicCoordinator = hass.data[DOMAIN][entry.entry_id]
    merged = {**coordinator.config_entry.data, **coordinator.config_entry.options}
    area_ids = get_selected_area_ids(merged)
    if not area_ids:
        return

    registry = area_registry.async_get(hass)
    current_room_configs = _current_room_configs(merged)
    options = _temperature_entity_options(hass)

    entities = []
    for area_id in area_ids:
        area = registry.async_get_area(area_id)
        if area is None:
            continue
        entities.append(
            AtmosLogicRoomTemperatureSelect(
                coordinator=coordinator,
                area_id=area_id,
                area_name=area.name or area_id,
                options=options,
                current_option=current_room_configs.get(area_id) or area.temperature_entity_id,
            )
        )

    async_add_entities(entities)


class AtmosLogicRoomTemperatureSelect(CoordinatorEntity[AtmosLogicCoordinator], SelectEntity):
    """Select entity that stores the temperature sensor linked to an area."""

    def __init__(
        self,
        coordinator: AtmosLogicCoordinator,
        *,
        area_id: str,
        area_name: str,
        options: list[str],
        current_option: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._area_id = area_id
        self._area_name = area_name
        self._options = list(options)
        if current_option and current_option not in self._options:
            self._options.append(current_option)
        self._current_option = current_option
        self._attr_name = f"AtmosLogic {area_name} temperature sensor"
        self._attr_icon = "mdi:thermometer"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{area_id}_temperature_sensor"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "AtmosLogic",
            "manufacturer": "AtmosLogic",
        }

    @property
    def options(self) -> list[str]:
        return self._options

    @property
    def current_option(self) -> str | None:
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        merged = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
        room_configs = _current_room_configs(merged)
        room_configs[self._area_id] = option

        data = dict(self.coordinator.config_entry.options)
        data[CONF_ROOM_CONFIGS] = [
            {
                "area_id": area_id,
                "temperature_entity": temperature_entity,
            }
            for area_id, temperature_entity in room_configs.items()
        ]
        self.hass.config_entries.async_update_entry(self.coordinator.config_entry, options=data)
        await self.hass.config_entries.async_reload(self.coordinator.config_entry.entry_id)
