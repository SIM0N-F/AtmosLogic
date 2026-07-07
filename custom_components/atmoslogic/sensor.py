"""Sensor platform for AtmosLogic."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ROOM_AREAS, DOMAIN
from .coordinator import AtmosLogicCoordinator
from .rooms import AtmosLogicRoomConfig

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="rooms_summary",
        name="Rooms summary",
        translation_key="rooms_summary",
        icon="mdi:home-group",
    ),
    SensorEntityDescription(
        key="home_mode",
        name="Home mode",
        translation_key="home_mode",
        icon="mdi:home-thermometer",
    ),
    SensorEntityDescription(
        key="window_recommendation",
        name="Window recommendation",
        translation_key="window_recommendation",
        icon="mdi:window-open-variant",
    ),
    SensorEntityDescription(
        key="cover_recommendation",
        name="Cover recommendation",
        translation_key="cover_recommendation",
        icon="mdi:blinds-horizontal",
    ),
    SensorEntityDescription(
        key="laundry_score",
        name="Laundry score",
        translation_key="laundry_score",
        icon="mdi:tumble-dryer",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key="laundry_recommendation",
        name="Laundry recommendation",
        translation_key="laundry_recommendation",
        icon="mdi:tumble-dryer-alert",
    ),
    SensorEntityDescription(
        key="thermal_score",
        name="Thermal score",
        translation_key="thermal_score",
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
)

ROOM_SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = tuple(
    description
    for description in SENSOR_DESCRIPTIONS
    if description.key != "laundry_score" and description.key != "laundry_recommendation"
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: object,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AtmosLogic sensors."""

    coordinator: AtmosLogicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AtmosLogicSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )
    for room in coordinator.config.room_configs:
        async_add_entities(
            AtmosLogicSensor(coordinator, description, room)
            for description in ROOM_SENSOR_DESCRIPTIONS
        )


class AtmosLogicSensor(CoordinatorEntity[AtmosLogicCoordinator], SensorEntity):
    """AtmosLogic sensor."""

    def __init__(
        self,
        coordinator: AtmosLogicCoordinator,
        description: SensorEntityDescription,
        room: AtmosLogicRoomConfig | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._attr_entity_description = description
        self._room = room
        self._attr_icon = description.icon
        self._attr_name = f"AtmosLogic {room.name} {description.name}" if room is not None else f"AtmosLogic {description.name}"
        room_suffix = f"_{room.key}" if room is not None else ""
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}{room_suffix}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "AtmosLogic",
            "manufacturer": "AtmosLogic",
        }

    @property
    def available(self) -> bool:
        if self._room is None:
            return super().available and self.coordinator.data is not None
        return super().available and self.coordinator.room_recommendations.get(self._room.key) is not None

    @property
    def native_value(self):  # type: ignore[override]
        if self._attr_entity_description.key == "rooms_summary":
            return self._rooms_summary_state()

        data = self.coordinator.data if self._room is None else self.coordinator.room_recommendations.get(self._room.key)
        if data is None:
            return None

        key = self._attr_entity_description.key
        if key == "home_mode":
            return data.home_mode
        if key == "window_recommendation":
            return data.window_recommendation
        if key == "cover_recommendation":
            return data.cover_recommendation
        if key == "laundry_score":
            return data.laundry_score
        if key == "laundry_recommendation":
            return data.laundry_recommendation
        if key == "thermal_score":
            return data.thermal_score
        return None

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        if self._attr_entity_description.key == "rooms_summary":
            return self._rooms_summary_attributes()

        data = self.coordinator.data if self._room is None else self.coordinator.room_recommendations.get(self._room.key)
        if data is None:
            return None
        return data.details

    def _rooms_summary_state(self) -> str:
        merged = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
        selected_room_area_ids = merged.get(CONF_ROOM_AREAS)
        if not isinstance(selected_room_area_ids, list) or not selected_room_area_ids:
            return "No rooms selected"

        rooms = self.coordinator.config.room_configs
        if not rooms:
            return "No area temperature sensor configured"

        return f"{len(rooms)} rooms configured"

    def _rooms_summary_attributes(self) -> dict[str, object]:
        merged = {**self.coordinator.config_entry.data, **self.coordinator.config_entry.options}
        selected_room_area_ids = merged.get(CONF_ROOM_AREAS)
        registry = area_registry.async_get(self.coordinator.hass)
        selected_areas: list[dict[str, object]] = []
        missing_temperature_areas: list[str] = []

        if isinstance(selected_room_area_ids, list):
            for area_id_value in selected_room_area_ids:
                area_id = str(area_id_value).strip()
                if not area_id:
                    continue
                area = registry.async_get_area(area_id)
                area_name = area.name if area is not None and area.name else area_id
                temperature_entity = area.temperature_entity_id if area is not None else None
                selected_areas.append(
                    {
                        "area_id": area_id,
                        "name": area_name,
                        "temperature_entity": temperature_entity,
                    }
                )
                if not temperature_entity:
                    missing_temperature_areas.append(area_name)

        return {
            "selected_areas": selected_areas,
            "configured_rooms": [
                {
                    "area_id": room.area_id,
                    "name": room.name,
                    "temperature_entity": room.temperature_entity,
                }
                for room in self.coordinator.config.room_configs
            ],
            "missing_temperature_areas": missing_temperature_areas,
            "summary": self.native_value,
        }
