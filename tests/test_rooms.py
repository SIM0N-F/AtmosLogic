"""Unit tests for AtmosLogic room helpers."""

from __future__ import annotations

import unittest

from custom_components.atmoslogic.rooms import build_additional_room_configs


class RoomHelpersTest(unittest.TestCase):
    """Exercise room configuration parsing."""

    def test_builds_only_configured_rooms(self) -> None:
        rooms = build_additional_room_configs(
            {
                "room_1_name": "Cuisine",
                "room_1_temperature_entity": "sensor.cuisine_temperature",
                "room_2_name": "Chambre",
                "room_2_temperature_entity": "sensor.chambre_temperature",
                "room_3_name": "",
                "room_3_temperature_entity": "",
            }
        )

        self.assertEqual(len(rooms), 2)
        self.assertEqual(rooms[0].key, "room_1")
        self.assertEqual(rooms[0].name, "Cuisine")
        self.assertEqual(rooms[0].temperature_entity, "sensor.cuisine_temperature")
        self.assertEqual(rooms[1].key, "room_2")
        self.assertEqual(rooms[1].name, "Chambre")
        self.assertEqual(rooms[1].temperature_entity, "sensor.chambre_temperature")

    def test_defaults_room_name_when_missing(self) -> None:
        rooms = build_additional_room_configs(
            {
                "room_1_temperature_entity": "sensor.salon_temperature",
            }
        )

        self.assertEqual(len(rooms), 1)
        self.assertEqual(rooms[0].name, "Room 1")


if __name__ == "__main__":
    unittest.main()
