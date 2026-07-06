"""Unit tests for the AtmosLogic recommendation engine."""

from __future__ import annotations

import unittest

from custom_components.atmoslogic.const import DEFAULT_TARGET_TEMPERATURE
from custom_components.atmoslogic.models import AtmosLogicConfig, AtmosLogicInput
from custom_components.atmoslogic.recommendation_engine import compute_recommendation


def make_config(**overrides: object) -> AtmosLogicConfig:
    """Create a config with sensible defaults for tests."""

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


class RecommendationEngineTest(unittest.TestCase):
    """Exercise the pure recommendation logic directly."""

    def test_cooling_conditions_favor_ventilation(self) -> None:
        config = make_config()
        reading = AtmosLogicInput(
            indoor_temperature=25.0,
            outdoor_temperature=19.0,
            outdoor_humidity=55.0,
            wind_speed=12.0,
            solar_value=120.0,
            solar_unit="%",
        )

        recommendation = compute_recommendation(config, reading)

        self.assertEqual(recommendation.home_mode, "ventilate")
        self.assertEqual(recommendation.window_recommendation, "open")
        self.assertTrue(recommendation.open_windows_recommended)
        self.assertFalse(recommendation.close_windows_recommended)
        self.assertEqual(recommendation.cover_recommendation, "neutral")
        self.assertGreaterEqual(recommendation.laundry_score, 80)
        self.assertEqual(recommendation.laundry_recommendation, "excellent")
        self.assertTrue(recommendation.good_for_laundry)

    def test_rain_and_strong_wind_close_everything(self) -> None:
        config = make_config()
        reading = AtmosLogicInput(
            indoor_temperature=20.0,
            outdoor_temperature=10.0,
            outdoor_humidity=92.0,
            rain_detected=True,
            wind_speed=50.0,
            solar_value=80.0,
            solar_unit="%",
        )

        recommendation = compute_recommendation(config, reading)

        self.assertEqual(recommendation.window_recommendation, "keep_closed")
        self.assertTrue(recommendation.close_windows_recommended)
        self.assertEqual(recommendation.cover_recommendation, "close")
        self.assertTrue(recommendation.close_covers_recommended)
        self.assertEqual(recommendation.laundry_recommendation, "impossible")
        self.assertEqual(recommendation.laundry_score, 0)
        self.assertFalse(recommendation.good_for_laundry)

    def test_heating_with_sunlight_opens_covers(self) -> None:
        config = make_config(mode="winter")
        reading = AtmosLogicInput(
            indoor_temperature=18.0,
            outdoor_temperature=22.0,
            outdoor_humidity=45.0,
            wind_speed=8.0,
            solar_value=15000.0,
            solar_unit="lux",
        )

        recommendation = compute_recommendation(config, reading)

        self.assertEqual(recommendation.home_mode, "heat_house")
        self.assertEqual(recommendation.window_recommendation, "open")
        self.assertEqual(recommendation.cover_recommendation, "open")
        self.assertTrue(recommendation.open_covers_recommended)
        self.assertGreater(recommendation.thermal_score, 0)

    def test_scores_are_clamped(self) -> None:
        config = make_config()
        reading = AtmosLogicInput(
            indoor_temperature=5.0,
            outdoor_temperature=-12.0,
            outdoor_humidity=99.0,
            rain_detected=True,
            wind_speed=120.0,
            solar_value=0.0,
        )

        recommendation = compute_recommendation(config, reading)

        self.assertGreaterEqual(recommendation.laundry_score, 0)
        self.assertLessEqual(recommendation.laundry_score, 100)
        self.assertGreaterEqual(recommendation.thermal_score, -100)
        self.assertLessEqual(recommendation.thermal_score, 100)


if __name__ == "__main__":
    unittest.main()
