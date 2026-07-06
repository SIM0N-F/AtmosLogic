"""Notification helpers for AtmosLogic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


def build_notification_batch(
    config: AtmosLogicConfig,
    previous: AtmosLogicRecommendation | None,
    current: AtmosLogicRecommendation,
) -> list[AtmosLogicNotification]:
    """Build notifications for rising recommendations."""

    if not config.notifications_enabled:
        return []
    if previous is None:
        return []

    notifications: list[AtmosLogicNotification] = []
    details = _inputs_summary(current)

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

    return notifications
