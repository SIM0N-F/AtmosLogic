"""Sensor platform for AtmosLogic."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AtmosLogicCoordinator
from .rooms import AtmosLogicRoomConfig

MAIN_SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="home",
        name="Home",
        translation_key="home",
        icon="mdi:home-analytics",
    ),
    SensorEntityDescription(
        key="laundry",
        name="Laundry",
        translation_key="laundry",
        icon="mdi:tumble-dryer",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: object,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AtmosLogic sensors."""

    coordinator: AtmosLogicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AtmosLogicMainSensor(coordinator, description)
        for description in MAIN_SENSOR_DESCRIPTIONS
    )
    async_add_entities(
        AtmosLogicRoomSensor(coordinator, room)
        for room in coordinator.config.room_configs
    )


class AtmosLogicMainSensor(CoordinatorEntity[AtmosLogicCoordinator], SensorEntity):
    """Main AtmosLogic sensor for the house or the laundry module."""

    def __init__(
        self,
        coordinator: AtmosLogicCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self._attr_entity_description = description
        self._attr_icon = description.icon
        self._attr_name = f"AtmosLogic {description.name}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "AtmosLogic",
            "manufacturer": "AtmosLogic",
        }

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data is not None

    @property
    def native_value(self):  # type: ignore[override]
        data = self.coordinator.data
        if data is None:
            return None

        if self._attr_entity_description.key == "home":
            return data.home_mode
        if self._attr_entity_description.key == "laundry":
            return data.laundry_recommendation
        return None

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        if self._attr_entity_description.key == "home":
            return self.coordinator.home_summary()
        if self._attr_entity_description.key == "laundry":
            return self.coordinator.laundry_summary()
        return None


class AtmosLogicRoomSensor(CoordinatorEntity[AtmosLogicCoordinator], SensorEntity):
    """Per-room AtmosLogic sensor."""

    def __init__(
        self,
        coordinator: AtmosLogicCoordinator,
        room: AtmosLogicRoomConfig,
    ) -> None:
        super().__init__(coordinator)
        self._room = room
        self._attr_name = f"AtmosLogic {room.name}"
        self._attr_icon = "mdi:thermometer"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{room.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "AtmosLogic",
            "manufacturer": "AtmosLogic",
        }

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.room_recommendations.get(self._room.key) is not None

    @property
    def native_value(self):  # type: ignore[override]
        recommendation = self.coordinator.room_recommendations.get(self._room.key)
        if recommendation is None:
            return None
        return recommendation.home_mode

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        return self.coordinator.room_summary(self._room.key)
