# AtmosLogic

<p align="center">
  <img src="https://raw.githubusercontent.com/SIM0N-F/AtmosLogic/main/branding/logo.png" alt="AtmosLogic logo" width="420">
</p>

**Weather-Based Environmental Advisor for Home Assistant**

AtmosLogic is a Home Assistant custom integration that turns indoor climate data, outdoor weather data, and a few user preferences into simple recommendations:

- open or close windows
- open or close covers
- whether the home is in a comfortable, cooling, heating, or preserve mode
- whether conditions are good for drying laundry outside

This version is intentionally advisory only. It does not control any equipment directly. Instead, it exposes a small set of rich `sensor` entities that you can reuse in your own Home Assistant automations.

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
- optional binary sensors toggle
- notifications toggle
- per-rule notification toggles for windows, covers, and laundry
- optional Home Assistant rooms, discovered from your Areas and linked to the temperature sensor configured on each Area
- export/import services for backup and restore

After the integration is created, you can reopen its options from **Settings > Devices & services > AtmosLogic > Configure** to adjust thresholds and feature toggles.
The configuration dialog now starts with a small menu, so the room management panel is separate from the rest of the settings.
You can add, remove, or edit monitored Areas from that dedicated Rooms panel, then link a temperature sensor for each one.
You can also reconfigure the integration from the device page when Home Assistant exposes the reconfigure action for the device.

## Entities

### Sensors

- `sensor.atmoslogic_home`
- `sensor.atmoslogic_laundry`
- one `sensor.atmoslogic_<area>` per configured Home Assistant Area
  - each room sensor exposes the current mode plus detailed attributes

### Binary sensors

- optional, disabled by default
- `binary_sensor.atmoslogic_open_windows_recommended`
- `binary_sensor.atmoslogic_close_windows_recommended`
- `binary_sensor.atmoslogic_open_covers_recommended`
- `binary_sensor.atmoslogic_close_covers_recommended`
- `binary_sensor.atmoslogic_good_for_laundry`
  - these expose custom Material Design icons such as `mdi:window-open-variant`

## Notifications

AtmosLogic can also send notifications automatically when a recommendation becomes active.

You can configure:

- the built-in Home Assistant notify service if it is available
- window-open notifications
- window-close notifications
- cover-open notifications
- cover-close notifications
- laundry-ready notifications

Notifications are sent only when a recommendation changes from inactive to active, which helps avoid repeated spam.

If the standard `notify.notify` service is not available, AtmosLogic falls back to a persistent notification so you still see the alert inside Home Assistant.

For quick access from the device page, the notification toggles are also exposed as config switches inside the AtmosLogic device.

Laundry recommendations also take into account nighttime and short-term rain forecasts when the data is available, so "good for laundry" is reserved for a real drying window.

Room management lives in the dedicated `Rooms` panel in the integration options, where you can add or edit one temperature sensor per Home Assistant Area.

If you prefer, you can still use the exposed sensors and binary sensors inside your own Home Assistant automations.

Room recommendations follow the Areas configured in Home Assistant. For each selected area, AtmosLogic uses the temperature sensor selected in the dedicated Rooms panel, and falls back to the Home Assistant Area temperature sensor when available.

## Export and Import

AtmosLogic exposes two Home Assistant services:

- `atmoslogic.export_configuration`
- `atmoslogic.import_configuration`

`export_configuration` creates a persistent notification containing a JSON backup of the selected config entry.

`import_configuration` accepts that JSON back and either:

- creates a new AtmosLogic config entry, or
- replaces an existing one if you pass `entry_id`

This is useful for moving a setup between Home Assistant instances or restoring a known-good configuration.

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
