"""Room helpers for AtmosLogic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .const import ROOM_SLOT_DEFINITIONS


@dataclass(slots=True)
class AtmosLogicRoomConfig:
    """Optional room-specific configuration."""

    key: str
    name: str
    temperature_entity: str


def build_additional_room_configs(values: Mapping[str, Any]) -> tuple[AtmosLogicRoomConfig, ...]:
    """Build the optional room configuration list from flat config data."""

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
                key=f"room_{slot}",
                name=room_name,
                temperature_entity=str(temperature_entity),
            )
        )

    return tuple(rooms)
