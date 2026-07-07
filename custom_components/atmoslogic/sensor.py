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
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AtmosLogicCoordinator
from .rooms import AtmosLogicRoomConfig

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
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
        data = self.coordinator.data if self._room is None else self.coordinator.room_recommendations.get(self._room.key)
        if data is None:
            return None
        return data.details
