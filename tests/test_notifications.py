"""Unit tests for AtmosLogic notification rules."""

from __future__ import annotations

import unittest

from custom_components.atmoslogic.const import DEFAULT_TARGET_TEMPERATURE
from custom_components.atmoslogic.models import AtmosLogicConfig, AtmosLogicInput
from custom_components.atmoslogic.notification_rules import build_notification_batch
from custom_components.atmoslogic.recommendation_engine import compute_recommendation


def make_config(**overrides: object) -> AtmosLogicConfig:
    """Create a config with notification defaults for tests."""

    data = {
        "indoor_temperature_entity": "sensor.indoor_temperature",
        "outdoor_temperature_entity": "sensor.outdoor_temperature",
        "target_temperature": DEFAULT_TARGET_TEMPERATURE,
        "comfort_margin": 0.5,
        "strong_wind_threshold": 35.0,
        "high_humidity_threshold": 80.0,
        "rain_threshold": 0.1,
        "mode": "auto",
        "laundry_enabled": True,
        "windows_enabled": True,
        "covers_enabled": True,
        "notifications_enabled": True,
        "notify_window_open": True,
        "notify_window_close": True,
        "notify_cover_open": True,
        "notify_cover_close": True,
        "notify_laundry_good": True,
        "indoor_humidity_entity": "sensor.indoor_humidity",
        "outdoor_humidity_entity": "sensor.outdoor_humidity",
        "rain_entity": "binary_sensor.rain",
        "wind_speed_entity": "sensor.wind_speed",
        "wind_gust_entity": "sensor.wind_gust",
        "solar_entity": "sensor.solar",
        "climate_entity": "climate.home",
        "weather_entity": "weather.home",
    }
    data.update(overrides)
    return AtmosLogicConfig(**data)


class NotificationRulesTest(unittest.TestCase):
    """Exercise the notification helper directly."""

    def test_initial_snapshot_does_not_notify(self) -> None:
        config = make_config()
        current = compute_recommendation(
            config,
            AtmosLogicInput(
                indoor_temperature=25.0,
                outdoor_temperature=19.0,
                outdoor_humidity=55.0,
                wind_speed=12.0,
                solar_value=120.0,
                solar_unit="%",
            ),
        )

        self.assertEqual(build_notification_batch(config, None, current), [])

    def test_window_open_transition_triggers_notification(self) -> None:
        config = make_config()
        previous = compute_recommendation(
            config,
            AtmosLogicInput(
                indoor_temperature=20.0,
                outdoor_temperature=19.5,
            ),
        )
        current = compute_recommendation(
            config,
            AtmosLogicInput(
                indoor_temperature=25.0,
                outdoor_temperature=19.0,
                outdoor_humidity=55.0,
                wind_speed=12.0,
                solar_value=120.0,
                solar_unit="%",
            ),
        )

        notifications = build_notification_batch(config, previous, current)

        self.assertTrue(any(notification.key == "window_open" for notification in notifications))
        self.assertTrue(any("fenetres" in notification.message for notification in notifications))

    def test_multiple_rising_rules_are_batched(self) -> None:
        config = make_config()
        previous = compute_recommendation(
            config,
            AtmosLogicInput(
                indoor_temperature=21.0,
                outdoor_temperature=20.0,
                outdoor_humidity=90.0,
                rain_detected=True,
            ),
        )
        current = compute_recommendation(
            config,
            AtmosLogicInput(
                indoor_temperature=25.0,
                outdoor_temperature=19.0,
                outdoor_humidity=55.0,
                wind_speed=12.0,
                solar_value=120.0,
                solar_unit="%",
            ),
        )

        notifications = build_notification_batch(config, previous, current)

        self.assertGreaterEqual(len(notifications), 2)
        self.assertTrue(any(notification.key == "window_open" for notification in notifications))
        self.assertTrue(any(notification.key == "laundry_good" for notification in notifications))


if __name__ == "__main__":
    unittest.main()
