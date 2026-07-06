# AtmosLogic

**Weather-Based Environmental Advisor for Home Assistant**

AtmosLogic is a Home Assistant custom integration that turns indoor climate data, outdoor weather data, and a few user preferences into simple recommendations:

- open or close windows
- open or close covers
- whether the home is in a comfortable, cooling, heating, or preserve mode
- whether conditions are good for drying laundry outside

This first version is intentionally advisory only. It does not control any equipment directly. Instead, it exposes `sensor` and `binary_sensor` entities that you can reuse in your own Home Assistant automations.

## Features

- HACS-compatible custom integration
- Config Flow setup from the Home Assistant UI
- No YAML required
- Pure recommendation engine separated from Home Assistant code
- English and French translations
- Basic unit tests
- GitHub Actions validation workflow

## Installation

### Option 1: HACS custom repository

1. Add this repository as a custom repository in HACS.
2. Choose the category `Integration`.
3. Install `AtmosLogic`.
4. Restart Home Assistant.
5. Go to **Settings > Devices & services > Add integration** and configure AtmosLogic.

### Option 2: Manual installation

1. Copy the `custom_components/atmoslogic/` directory into your Home Assistant `custom_components/` folder.
2. Restart Home Assistant.
3. Add the integration from **Settings > Devices & services**.

## Configuration

AtmosLogic asks for:

- indoor temperature entity
- outdoor temperature entity
- target temperature, default `21 °C`

Optional inputs:

- indoor humidity entity
- outdoor humidity entity
- rain entity
- average wind entity
- wind gust entity
- brightness or solar radiation entity
- climate entity
- weather entity

Optional tuning:

- comfort margin, default `0.5 °C`
- strong wind threshold
- high humidity threshold
- rain threshold
- mode: `auto`, `summer`, or `winter`
- laundry module toggle
- windows module toggle
- covers module toggle
- notifications toggle
- notification service name or a comma-separated list, for example `mobile_app_my_phone`
- per-rule notification toggles for windows, covers, and laundry

## Entities

### Sensors

- `sensor.atmoslogic_home_mode`
- `sensor.atmoslogic_window_recommendation`
- `sensor.atmoslogic_cover_recommendation`
- `sensor.atmoslogic_laundry_score`
- `sensor.atmoslogic_laundry_recommendation`
- `sensor.atmoslogic_thermal_score`

### Binary sensors

- `binary_sensor.atmoslogic_open_windows_recommended`
- `binary_sensor.atmoslogic_close_windows_recommended`
- `binary_sensor.atmoslogic_open_covers_recommended`
- `binary_sensor.atmoslogic_close_covers_recommended`
- `binary_sensor.atmoslogic_good_for_laundry`

## Notifications

AtmosLogic can also send notifications automatically when a recommendation becomes active.

You can configure:

- a notify service name such as `mobile_app_my_phone`, or a comma-separated list
- window-open notifications
- window-close notifications
- cover-open notifications
- cover-close notifications
- laundry-ready notifications

Notifications are sent only when a recommendation changes from inactive to active, which helps avoid repeated spam.

If you prefer, you can still use the exposed sensors and binary sensors inside your own Home Assistant automations.

## Quick logic summary

- If indoor temperature is above target plus margin, the integration favors cooling.
- If indoor temperature is below target minus margin, it favors heating.
- Windows close when rain or strong wind is detected.
- Covers close when it is hot outside and the home needs cooling.
- Covers open when the home needs heating and sunlight is available.
- Laundry score starts at `50` and is adjusted by temperature, humidity, wind, sunlight, and rain.

## Development

The recommendation logic lives in:

- [`custom_components/atmoslogic/recommendation_engine.py`](custom_components/atmoslogic/recommendation_engine.py)

The Home Assistant-facing layer lives in:

- [`custom_components/atmoslogic/coordinator.py`](custom_components/atmoslogic/coordinator.py)
- [`custom_components/atmoslogic/sensor.py`](custom_components/atmoslogic/sensor.py)
- [`custom_components/atmoslogic/binary_sensor.py`](custom_components/atmoslogic/binary_sensor.py)

Run the basic tests with:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Notes

- This is a first functional version, not a complete automation platform.
- It is designed to stay advisory so you can build your own automations on top of the recommendation entities.
