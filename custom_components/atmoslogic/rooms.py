"""Room helpers for AtmosLogic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

try:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers import area_registry
except ModuleNotFoundError:  # pragma: no cover - test environment fallback
    from typing import Any

    HomeAssistant = Any  # type: ignore[assignment]

    class _AreaRegistryFallback:
        def async_get(self, _hass: Any) -> Any:
            raise ModuleNotFoundError

    area_registry = _AreaRegistryFallback()

from .const import (
    CONF_ROOM_CONFIGS,
    ROOM_SLOT_DEFINITIONS,
)


@dataclass(slots=True)
class AtmosLogicRoomConfig:
    """Optional room-specific configuration."""

    area_id: str
    name: str
    temperature_entity: str

    @property
    def key(self) -> str:
        """Return a stable key for entity names and unique IDs."""

        return self.area_id


def _area_name(hass: HomeAssistant | None, area_id: str, fallback: str) -> str:
    if hass is None:
        return fallback

    registry = area_registry.async_get(hass)
    area = registry.async_get_area(area_id)
    if area is None or not area.name:
        return fallback
    return area.name


def _build_room_from_mapping(
    hass: HomeAssistant | None,
    mapping: Mapping[str, Any],
    *,
    default_name: str,
) -> AtmosLogicRoomConfig | None:
    area_id = str(mapping.get("area_id") or mapping.get("key") or "").strip()
    temperature_entity = mapping.get("temperature_entity") or mapping.get("temperature_entity_id")
    if not area_id and not temperature_entity:
        return None

    if temperature_entity is None and hass is not None and area_id:
        registry = area_registry.async_get(hass)
        area = registry.async_get_area(area_id)
        if area is not None and area.temperature_entity_id:
            temperature_entity = area.temperature_entity_id

    if not area_id or not temperature_entity:
        return None

    fallback_name = str(mapping.get("name") or default_name or area_id).strip() or area_id
    return AtmosLogicRoomConfig(
        area_id=area_id,
        name=_area_name(hass, area_id, fallback_name),
        temperature_entity=str(temperature_entity),
    )


def _build_legacy_rooms(values: Mapping[str, Any]) -> tuple[AtmosLogicRoomConfig, ...]:
    rooms: list[AtmosLogicRoomConfig] = []
    for slot, name_key, entity_key in ROOM_SLOT_DEFINITIONS:
        temperature_entity = values.get(entity_key)
        if not temperature_entity:
            continue

        room_name = str(values.get(name_key) or f"Room {slot}").strip()
        if not room_name:
            room_name = f"Room {slot}"

        rooms.append(
            AtmosLogicRoomConfig(
                area_id=f"legacy_room_{slot}",
                name=room_name,
                temperature_entity=str(temperature_entity),
            )
        )

    return tuple(rooms)


def build_room_configs(hass: HomeAssistant | None, values: Mapping[str, Any]) -> tuple[AtmosLogicRoomConfig, ...]:
    """Build room configurations from entry data or legacy slot fields."""

    raw_room_configs = values.get(CONF_ROOM_CONFIGS)
    if isinstance(raw_room_configs, (list, tuple)):
        rooms: list[AtmosLogicRoomConfig] = []
        for index, room_data in enumerate(raw_room_configs):
            if not isinstance(room_data, Mapping):
                continue

            room = _build_room_from_mapping(
                hass,
                room_data,
                default_name=f"Room {index + 1}",
            )
            if room is not None:
                rooms.append(room)

        return tuple(rooms)

    raw_room_areas = values.get("room_areas")
    if isinstance(raw_room_areas, (list, tuple)):
        rooms: list[AtmosLogicRoomConfig] = []
        registry = area_registry.async_get(hass) if hass is not None else None
        for area_id_value in raw_room_areas:
            area_id = str(area_id_value).strip()
            if not area_id:
                continue

            area = registry.async_get_area(area_id) if registry is not None else None
            if area is None or not area.temperature_entity_id:
                continue

            rooms.append(
                AtmosLogicRoomConfig(
                    area_id=area_id,
                    name=area.name or area_id,
                    temperature_entity=area.temperature_entity_id,
                )
            )

        return tuple(rooms)

    return _build_legacy_rooms(values)


def build_additional_room_configs(values: Mapping[str, Any]) -> tuple[AtmosLogicRoomConfig, ...]:
    """Backward-compatible alias for older tests and callers."""

    return build_room_configs(None, values)
