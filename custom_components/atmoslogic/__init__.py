"""AtmosLogic integration."""

from __future__ import annotations

import json
from typing import Any

import voluptuous as vol

try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.exceptions import HomeAssistantError
    from homeassistant.helpers import config_validation as cv
except ModuleNotFoundError:  # pragma: no cover - test environment fallback
    ConfigEntry = Any  # type: ignore[assignment]
    HomeAssistant = Any  # type: ignore[assignment]
    HomeAssistantError = Exception  # type: ignore[assignment]
    cv = Any  # type: ignore[assignment]

from .const import DOMAIN, PLATFORMS
try:
    from .coordinator import AtmosLogicCoordinator
except ModuleNotFoundError:  # pragma: no cover - test environment fallback
    AtmosLogicCoordinator = Any  # type: ignore[assignment]

type AtmosLogicConfigEntry = ConfigEntry


def _export_service_schema() -> vol.Schema:
    return vol.Schema({vol.Optional("entry_id"): cv.string})


def _import_service_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("configuration"): cv.string,
            vol.Optional("entry_id"): cv.string,
        }
    )


def _find_entry(hass: HomeAssistant, entry_id: str | None) -> ConfigEntry:
    entries = hass.config_entries.async_entries(DOMAIN)
    if entry_id is not None:
        for entry in entries:
            if entry.entry_id == entry_id:
                return entry
        raise HomeAssistantError(f"AtmosLogic entry_id {entry_id!r} was not found")

    if len(entries) == 1:
        return entries[0]

    raise HomeAssistantError("Provide entry_id when more than one AtmosLogic entry exists")


def _export_payload(entry: ConfigEntry) -> dict[str, Any]:
    return {
        "domain": DOMAIN,
        "title": entry.title,
        "entry_id": entry.entry_id,
        "version": entry.version,
        "data": dict(entry.data),
        "options": dict(entry.options),
    }


async def _async_create_export_notification(hass: HomeAssistant, payload: dict[str, Any]) -> None:
    await hass.services.async_call(
        "persistent_notification",
        "create",
        {
            "title": "AtmosLogic configuration export",
            "message": "```json\n" + json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n```",
        },
        blocking=False,
    )


async def _async_handle_export_service(hass: HomeAssistant, call: Any) -> None:
    entry = _find_entry(hass, call.data.get("entry_id"))
    await _async_create_export_notification(hass, _export_payload(entry))


def _parse_configuration(configuration: str) -> dict[str, Any]:
    try:
        payload = json.loads(configuration)
    except json.JSONDecodeError as err:
        raise HomeAssistantError("AtmosLogic configuration is not valid JSON") from err

    if not isinstance(payload, dict):
        raise HomeAssistantError("AtmosLogic configuration must be a JSON object")

    return payload


def _normalized_import_data(payload: dict[str, Any]) -> dict[str, Any]:
    if "data" in payload or "options" in payload:
        data = payload.get("data", {})
        options = payload.get("options", {})
        title = payload.get("title") or "AtmosLogic"
        if not isinstance(data, dict) or not isinstance(options, dict):
            raise HomeAssistantError("AtmosLogic export payload is malformed")
        return {"title": title, "data": data, "options": options}

    title = payload.get("title") or "AtmosLogic"
    if not isinstance(title, str):
        raise HomeAssistantError("AtmosLogic import payload is malformed")
    data = {k: v for k, v in payload.items() if k != "title"}
    return {"title": title, "data": data, "options": {}}


async def _async_handle_import_service(hass: HomeAssistant, call: Any) -> None:
    payload = _normalized_import_data(_parse_configuration(call.data["configuration"]))
    entry_id = call.data.get("entry_id")

    if entry_id is not None:
        entry = _find_entry(hass, entry_id)
        hass.config_entries.async_update_entry(
            entry,
            title=payload["title"],
            data=payload["data"],
            options=payload["options"],
        )
        await hass.config_entries.async_reload(entry.entry_id)
        return

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": "import",
            "title": payload["title"],
        },
        data={**payload["data"], **payload["options"]},
    )
    if result["type"] == "abort":
        raise HomeAssistantError(f"AtmosLogic import aborted: {result.get('reason', 'unknown')}")


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up AtmosLogic services."""

    _async_register_services(hass)
    return True


def _async_register_services(hass: HomeAssistant) -> None:
    if not hass.services.has_service(DOMAIN, "export_configuration"):
        hass.services.async_register(
            DOMAIN,
            "export_configuration",
            lambda call: _async_handle_export_service(hass, call),
            schema=_export_service_schema(),
        )
    if not hass.services.has_service(DOMAIN, "import_configuration"):
        hass.services.async_register(
            DOMAIN,
            "import_configuration",
            lambda call: _async_handle_import_service(hass, call),
            schema=_import_service_schema(),
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AtmosLogic from a config entry."""

    _async_register_services(hass)
    coordinator = AtmosLogicCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_setup()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload AtmosLogic."""

    coordinator = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if coordinator is not None:
        await coordinator.async_unload()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
