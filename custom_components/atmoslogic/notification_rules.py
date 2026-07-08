"""Notification helpers for AtmosLogic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .models import AtmosLogicConfig, AtmosLogicRecommendation


@dataclass(slots=True)
class AtmosLogicNotification:
    """Notification payload built from a recommendation transition."""

    key: str
    message: str


def _is_rising(previous: bool | None, current: bool) -> bool:
    return current and not bool(previous)


def _format_temperature(value: Any) -> str | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if number.is_integer():
        return f"{int(number)} C"
    return f"{number:.1f} C"


def _format_numeric(value: Any) -> str | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}"


def _inputs_summary(recommendation: AtmosLogicRecommendation) -> str:
    inputs = recommendation.details.get("inputs", {})
    parts: list[str] = []

    indoor = _format_temperature(inputs.get("indoor_temperature"))
    outdoor = _format_temperature(inputs.get("outdoor_temperature"))
    if indoor is not None:
        parts.append(f"interieur {indoor}")
    if outdoor is not None:
        parts.append(f"exterieur {outdoor}")

    wind = _format_numeric(inputs.get("wind_speed"))
    if wind is not None:
        parts.append(f"vent {wind}")

    humidity = _format_numeric(inputs.get("outdoor_humidity"))
    if humidity is not None:
        parts.append(f"humidite exterieure {humidity}%")

    if not parts:
        return ""
    return " - " + ", ".join(parts)


def _home_mode_label(value: str) -> str:
    return {
        "comfort": "confort",
        "cool_house": "rafraîchir la maison",
        "heat_house": "chauffer la maison",
        "preserve_cool": "préserver la fraîcheur",
        "preserve_heat": "préserver la chaleur",
        "ventilate": "ventiler",
    }.get(value, value)


def _action_label(value: str) -> str:
    return {
        "close_windows": "fermer les fenêtres",
        "open_windows": "ouvrir les fenêtres",
        "close_covers": "fermer les volets",
        "open_covers": "ouvrir les volets",
        "laundry": "étendre le linge",
        "none": "aucune action",
    }.get(value, value.replace("_", " "))


def _room_summary_label(room: Mapping[str, Any]) -> str:
    name = str(room.get("name") or "Pièce").strip() or "Pièce"
    action = str(room.get("next_action_recommended") or "none")
    return f"{name}: {_action_label(action)}"


def _summary_message(home_summary: Mapping[str, Any]) -> str | None:
    parts: list[str] = []

    home_mode = home_summary.get("home_mode")
    if isinstance(home_mode, str) and home_mode:
        parts.append(f"mode {_home_mode_label(home_mode)}")

    global_score = home_summary.get("global_score")
    if global_score is not None:
        parts.append(f"score {global_score}")

    priority_room = home_summary.get("priority_room")
    if isinstance(priority_room, str) and priority_room:
        parts.append(f"pièce prioritaire {priority_room}")

    next_action = home_summary.get("next_action_recommended")
    if isinstance(next_action, str) and next_action and next_action != "none":
        parts.append(f"action suivante {_action_label(next_action)}")

    rooms = home_summary.get("rooms")
    if isinstance(rooms, list):
        active_rooms = [
            _room_summary_label(room)
            for room in rooms
            if isinstance(room, Mapping) and str(room.get("next_action_recommended") or "none") != "none"
        ]
        if active_rooms:
            parts.append("pièces actives: " + "; ".join(active_rooms))

    if not parts:
        return None

    return "Résumé AtmosLogic: " + " | ".join(parts) + "."


def _room_notifications(
    config: AtmosLogicConfig,
    previous_rooms: Mapping[str, AtmosLogicRecommendation],
    current_rooms: Mapping[str, AtmosLogicRecommendation],
) -> list[AtmosLogicNotification]:
    notifications: list[AtmosLogicNotification] = []

    for room_key, current_room in current_rooms.items():
        previous_room = previous_rooms.get(room_key)
        if previous_room is None:
            continue

        room_name = str(current_room.details.get("room", {}).get("name") or room_key)
        details = _inputs_summary(current_room)

        if config.notify_window_open and _is_rising(previous_room.open_windows_recommended, current_room.open_windows_recommended):
            notifications.append(
                AtmosLogicNotification(
                    key=f"room_{room_key}_window_open",
                    message=f"{room_name}: ouvrez les fenetres maintenant{details}.",
                )
            )

        if config.notify_window_close and _is_rising(previous_room.close_windows_recommended, current_room.close_windows_recommended):
            notifications.append(
                AtmosLogicNotification(
                    key=f"room_{room_key}_window_close",
                    message=f"{room_name}: fermez les fenetres maintenant{details}.",
                )
            )

        if config.notify_cover_open and _is_rising(previous_room.open_covers_recommended, current_room.open_covers_recommended):
            notifications.append(
                AtmosLogicNotification(
                    key=f"room_{room_key}_cover_open",
                    message=f"{room_name}: ouvrez les volets maintenant{details}.",
                )
            )

        if config.notify_cover_close and _is_rising(previous_room.close_covers_recommended, current_room.close_covers_recommended):
            notifications.append(
                AtmosLogicNotification(
                    key=f"room_{room_key}_cover_close",
                    message=f"{room_name}: fermez les volets maintenant{details}.",
                )
            )

    return notifications


def build_notification_batch(
    config: AtmosLogicConfig,
    previous: AtmosLogicRecommendation | None,
    current: AtmosLogicRecommendation,
    *,
    previous_room_recommendations: Mapping[str, AtmosLogicRecommendation] | None = None,
    current_room_recommendations: Mapping[str, AtmosLogicRecommendation] | None = None,
    home_summary: Mapping[str, Any] | None = None,
) -> list[AtmosLogicNotification]:
    """Build notifications for rising recommendations."""

    if not config.notifications_enabled:
        return []
    if previous is None:
        return []

    notifications: list[AtmosLogicNotification] = []
    details = _inputs_summary(current)

    if config.notify_room_recommendations and previous_room_recommendations is not None and current_room_recommendations is not None:
        notifications.extend(
            _room_notifications(config, previous_room_recommendations, current_room_recommendations)
        )

    if config.notify_window_open and _is_rising(previous.open_windows_recommended, current.open_windows_recommended):
        notifications.append(
            AtmosLogicNotification(
                key="window_open",
                message=f"Ouvrez les fenetres maintenant{details}.",
            )
        )

    if config.notify_window_close and _is_rising(previous.close_windows_recommended, current.close_windows_recommended):
        notifications.append(
            AtmosLogicNotification(
                key="window_close",
                message=f"Fermez les fenetres maintenant{details}.",
            )
        )

    if config.notify_cover_open and _is_rising(previous.open_covers_recommended, current.open_covers_recommended):
        notifications.append(
            AtmosLogicNotification(
                key="cover_open",
                message=f"Ouvrez les volets maintenant{details}.",
            )
        )

    if config.notify_cover_close and _is_rising(previous.close_covers_recommended, current.close_covers_recommended):
        notifications.append(
            AtmosLogicNotification(
                key="cover_close",
                message=f"Fermez les volets maintenant{details}.",
            )
        )

    if config.notify_laundry_good and _is_rising(previous.good_for_laundry, current.good_for_laundry):
        notifications.append(
            AtmosLogicNotification(
                key="laundry_good",
                message=f"Bon moment pour etendre le linge dehors{details}.",
            )
        )

    if config.notify_summary and notifications and home_summary is not None:
        summary = _summary_message(home_summary)
        if summary is not None:
            notifications.insert(
                0,
                AtmosLogicNotification(
                    key="summary",
                    message=summary,
                ),
            )

    return notifications
