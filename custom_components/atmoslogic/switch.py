"""Switch platform for AtmosLogic notification settings."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_NOTIFICATIONS_ENABLED,
    CONF_NOTIFY_COVER_CLOSE,
    CONF_NOTIFY_COVER_OPEN,
    CONF_NOTIFY_LAUNDRY_GOOD,
    CONF_NOTIFY_ROOM_RECOMMENDATIONS,
    CONF_NOTIFY_SUMMARY,
    CONF_NOTIFY_WINDOW_CLOSE,
    CONF_NOTIFY_WINDOW_OPEN,
    DOMAIN,
)
from .coordinator import AtmosLogicCoordinator


@dataclass(slots=True, frozen=True)
class AtmosLogicSwitchDescription:
    """Description of a notification setting switch."""

    key: str
    name: str
    icon: str


SWITCH_DESCRIPTIONS: tuple[AtmosLogicSwitchDescription, ...] = (
    AtmosLogicSwitchDescription(
        key=CONF_NOTIFICATIONS_ENABLED,
        name="Notifications enabled",
        icon="mdi:bell",
    ),
    AtmosLogicSwitchDescription(
        key=CONF_NOTIFY_SUMMARY,
        name="Send summary notifications",
        icon="mdi:text-box-outline",
    ),
    AtmosLogicSwitchDescription(
        key=CONF_NOTIFY_ROOM_RECOMMENDATIONS,
        name="Notify room recommendations",
        icon="mdi:home-city-outline",
    ),
    AtmosLogicSwitchDescription(
        key=CONF_NOTIFY_WINDOW_OPEN,
        name="Notify windows should open",
        icon="mdi:window-open-variant",
    ),
    AtmosLogicSwitchDescription(
        key=CONF_NOTIFY_WINDOW_CLOSE,
        name="Notify windows should close",
        icon="mdi:window-closed-variant",
    ),
    AtmosLogicSwitchDescription(
        key=CONF_NOTIFY_COVER_OPEN,
        name="Notify covers should open",
        icon="mdi:blinds-open",
    ),
    AtmosLogicSwitchDescription(
        key=CONF_NOTIFY_COVER_CLOSE,
        name="Notify covers should close",
        icon="mdi:blinds",
    ),
    AtmosLogicSwitchDescription(
        key=CONF_NOTIFY_LAUNDRY_GOOD,
        name="Notify when laundry is good",
        icon="mdi:tumble-dryer-check",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: object,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AtmosLogic notification switches."""

    coordinator: AtmosLogicCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AtmosLogicNotificationSwitch(coordinator, description)
        for description in SWITCH_DESCRIPTIONS
    )


class AtmosLogicNotificationSwitch(CoordinatorEntity[AtmosLogicCoordinator], SwitchEntity):
    """Switch that updates AtmosLogic notification options."""

    def __init__(
        self,
        coordinator: AtmosLogicCoordinator,
        description: AtmosLogicSwitchDescription,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._attr_name = f"AtmosLogic {description.name}"
        self._attr_icon = description.icon
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "AtmosLogic",
            "manufacturer": "AtmosLogic",
        }

    @property
    def is_on(self) -> bool:
        config = self.coordinator.config
        return bool(getattr(config, self._description.key))

    async def _async_set_state(self, value: bool) -> None:
        entry = self.coordinator.config_entry
        options = {**entry.options, self._description.key: value}
        self.hass.config_entries.async_update_entry(entry, options=options)
        await self.hass.config_entries.async_reload(entry.entry_id)

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn the switch on."""

        if not self.is_on:
            await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn the switch off."""

        if self.is_on:
            await self._async_set_state(False)
