"""Period-key utilities for cadence-aware, per-user-timezone streak tracking."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from duohabit.models.habits import HabitType


def local_today(tz: str) -> date:
    """Current date in the given IANA timezone (a member's own day boundary)."""
    return datetime.now(ZoneInfo(tz)).date()


def compute_period_key(check_date: date, habit_type: HabitType) -> str:
    """Compute the canonical period identifier a check_date falls into."""
    if habit_type in (HabitType.DAILY, HabitType.WEEKDAYS):
        return check_date.isoformat()
    if habit_type == HabitType.WEEKLY:
        iso_year, iso_week, _ = check_date.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    # MONTHLY
    return f"{check_date.year}-{check_date.month:02d}"


def current_period_key(habit_type: HabitType, tz: str) -> str:
    """Compute the period key for the current moment in the member's own timezone."""
    return compute_period_key(local_today(tz), habit_type)


def previous_period_key(habit_type: HabitType, tz: str) -> str:
    """Compute the period key immediately preceding the current one.

    Used to seed a brand-new HabitMember's last_resolved_period_key: the current period is
    still in progress and must not be pre-marked as resolved, or the eager same-day
    completion path in check_in would never be able to fire on day one.
    """
    today = local_today(tz)
    if habit_type in (HabitType.DAILY, HabitType.WEEKDAYS):
        return compute_period_key(today - timedelta(days=1), habit_type)
    if habit_type == HabitType.WEEKLY:
        return compute_period_key(today - timedelta(days=7), habit_type)
    # MONTHLY
    first_of_this_month = today.replace(day=1)
    last_of_prev_month = first_of_this_month - timedelta(days=1)
    return compute_period_key(last_of_prev_month, habit_type)


def period_end_local(period_key: str, habit_type: HabitType, tz: str) -> datetime:
    """Exclusive upper bound (in the member's timezone) of a period.

    E.g. '2026-08-20' -> 2026-08-21T00:00:00 in that timezone.
    """
    zone = ZoneInfo(tz)
    if habit_type in (HabitType.DAILY, HabitType.WEEKDAYS):
        day = date.fromisoformat(period_key)
        return datetime(day.year, day.month, day.day, tzinfo=zone) + timedelta(days=1)
    if habit_type == HabitType.WEEKLY:
        year_str, week_str = period_key.split("-W")
        monday = date.fromisocalendar(int(year_str), int(week_str), 1)
        return datetime(monday.year, monday.month, monday.day, tzinfo=zone) + timedelta(
            days=7
        )
    # MONTHLY
    year_str, month_str = period_key.split("-")
    year, month = int(year_str), int(month_str)
    next_month_year = year + 1 if month == 12 else year
    next_month = 1 if month == 12 else month + 1
    return datetime(next_month_year, next_month, 1, tzinfo=zone)
