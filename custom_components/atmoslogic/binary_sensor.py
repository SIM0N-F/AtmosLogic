"""Binary sensor platform for AtmosLogic."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AtmosLogicCoordinator

BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="open_windows_recommended",
        name="Open windows recommended",
        translation_key="open_windows_recommended",
        device_class=BinarySensorDeviceClass.WINDOW,
    ),
    BinarySensorEntityDescription(
        key="close_windows_recommended",
        name="Close windows recommended",
        translation_key="close_windows_recommended",
        device_class=BinarySensorDeviceClass.WINDOW,
    ),
    BinarySensorEntityDescription(
        key="open_covers_recommended",
        name="Open covers recommended",
        translation_key="open_covers_recommended",
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    BinarySensorEntityDescription(
        key="close_covers_recommended",
        name="Close covers recommended",
        translation_key="close_covers_recommended",
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    BinarySensorEntityDescription(
        key="good_for_laundry",
        name="Good for laundry",
        translation_key="good_for_laundry",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: object,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AtmosLogic binary sensors."""

    coordinator: AtmosLogicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AtmosLogicBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class AtmosLogicBinarySensor(CoordinatorEntity[AtmosLogicCoordinator], BinarySensorEntity):
    """AtmosLogic binary sensor."""

    def __init__(
        self,
        coordinator: AtmosLogicCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self._attr_entity_description = description
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
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if data is None:
            return None

        key = self._attr_entity_description.key
        if key == "open_windows_recommended":
            return data.open_windows_recommended
        if key == "close_windows_recommended":
            return data.close_windows_recommended
        if key == "open_covers_recommended":
            return data.open_covers_recommended
        if key == "close_covers_recommended":
            return data.close_covers_recommended
        if key == "good_for_laundry":
            return data.good_for_laundry
        return None

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        data = self.coordinator.data
        if data is None:
            return None
        return data.details
