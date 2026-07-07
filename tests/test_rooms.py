"""Unit tests for AtmosLogic room helpers."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from custom_components.atmoslogic.rooms import build_room_configs


class FakeArea:
    """Minimal area registry entry for tests."""

    def __init__(self, name: str, temperature_entity_id: str | None = None) -> None:
        self.name = name
        self.temperature_entity_id = temperature_entity_id


class FakeAreaRegistry:
    """Minimal area registry for tests."""

    def __init__(self, areas: dict[str, FakeArea]) -> None:
        self._areas = areas

    def async_get_area(self, area_id: str) -> FakeArea | None:
        return self._areas.get(area_id)


class RoomHelpersTest(unittest.TestCase):
    """Exercise room configuration parsing."""

    def test_builds_rooms_from_home_assistant_areas(self) -> None:
        registry = FakeAreaRegistry(
            {
                "living_room": FakeArea("Salon", "sensor.living_temperature"),
                "bedroom": FakeArea("Chambre", "sensor.bedroom_temperature"),
            }
        )

        with patch("custom_components.atmoslogic.rooms.area_registry.async_get", return_value=registry):
            rooms = build_room_configs(
                object(),
                {
                    "room_areas": ["living_room", "bedroom"],
                },
            )

        self.assertEqual(len(rooms), 2)
        self.assertEqual(rooms[0].area_id, "living_room")
        self.assertEqual(rooms[0].name, "Salon")
        self.assertEqual(rooms[0].temperature_entity, "sensor.living_temperature")
        self.assertEqual(rooms[1].area_id, "bedroom")
        self.assertEqual(rooms[1].name, "Chambre")
        self.assertEqual(rooms[1].temperature_entity, "sensor.bedroom_temperature")

    def test_falls_back_to_legacy_room_slots(self) -> None:
        rooms = build_room_configs(
            None,
            {
                "room_1_name": "Cuisine",
                "room_1_temperature_entity": "sensor.cuisine_temperature",
                "room_2_name": "Chambre",
                "room_2_temperature_entity": "sensor.chambre_temperature",
            },
        )

        self.assertEqual(len(rooms), 2)
        self.assertEqual(rooms[0].area_id, "legacy_room_1")
        self.assertEqual(rooms[0].name, "Cuisine")
        self.assertEqual(rooms[0].temperature_entity, "sensor.cuisine_temperature")
        self.assertEqual(rooms[1].area_id, "legacy_room_2")
        self.assertEqual(rooms[1].name, "Chambre")
        self.assertEqual(rooms[1].temperature_entity, "sensor.chambre_temperature")


if __name__ == "__main__":
    unittest.main()
