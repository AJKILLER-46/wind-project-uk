"""
Timezone utilities for Europe/London handling.

All timestamps are stored internally as UTC-aware datetimes.
Europe/London is used for delivery-date calculations and display.
Daylight-saving transitions are handled via pytz — never hardcode offsets.
"""
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pytz

UK_TZ = pytz.timezone("Europe/London")
UTC_TZ = pytz.UTC

UK_ZONEINFO = ZoneInfo("Europe/London")


def parse_utc(ts_str: str) -> datetime:
    """Parse an ISO 8601 timestamp string and return a UTC-aware datetime."""
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts_str)
    if dt.tzinfo is None:
        dt = UTC_TZ.localize(dt)
    else:
        dt = dt.astimezone(UTC_TZ)
    return dt


def to_uk(dt: datetime) -> datetime:
    """Convert a UTC-aware datetime to Europe/London local time."""
    return dt.astimezone(UK_ZONEINFO)


def uk_midnight_utc(d: date) -> datetime:
    """Return the UTC datetime corresponding to midnight on date d in Europe/London."""
    naive_midnight = datetime.combine(d, time(0, 0, 0))
    uk_midnight = UK_TZ.localize(naive_midnight, is_dst=None)
    return uk_midnight.astimezone(UTC_TZ)


def delivery_date_uk(start_time_utc: datetime) -> date:
    """Return the Europe/London calendar date for a delivery period start time."""
    uk_dt = to_uk(start_time_utc)
    return uk_dt.date()


def cutoff_utc(decision_date: date, cutoff_time_str: str) -> datetime:
    """
    Compute the decision cutoff as a UTC-aware datetime.

    decision_date: the calendar date (Europe/London) on which the cutoff falls.
    cutoff_time_str: 'HH:MM' in Europe/London local time.
    """
    hh, mm = [int(x) for x in cutoff_time_str.split(":")]
    naive_cutoff = datetime.combine(decision_date, time(hh, mm, 0))
    try:
        uk_cutoff = UK_TZ.localize(naive_cutoff, is_dst=None)
    except pytz.exceptions.NonExistentTimeError:
        # Clocks spring forward — use the post-transition offset
        uk_cutoff = UK_TZ.localize(naive_cutoff, is_dst=True)
    except pytz.exceptions.AmbiguousTimeError:
        # Clocks fall back — use the pre-transition (standard time) offset
        uk_cutoff = UK_TZ.localize(naive_cutoff, is_dst=False)
    return uk_cutoff.astimezone(UTC_TZ)


def settlement_period_from_start(start_time_utc: datetime) -> int:
    """
    Derive settlement period number (1-based) from delivery start time.

    SP 1 starts at 23:00 UTC on the preceding calendar day (midnight UK time in winter).
    This correctly handles DST transitions (25-hour and 23-hour days).
    """
    uk_dt = to_uk(start_time_utc)
    uk_date = uk_dt.date()
    # SP 1 starts at the beginning of the UK business day
    try:
        day_start_uk = UK_TZ.localize(datetime.combine(uk_date, time(0, 0, 0)), is_dst=None)
    except pytz.exceptions.AmbiguousTimeError:
        day_start_uk = UK_TZ.localize(datetime.combine(uk_date, time(0, 0, 0)), is_dst=False)
    except pytz.exceptions.NonExistentTimeError:
        day_start_uk = UK_TZ.localize(datetime.combine(uk_date, time(0, 0, 0)), is_dst=True)

    minutes_from_midnight = int((uk_dt - day_start_uk).total_seconds() / 60)
    sp = (minutes_from_midnight // 30) + 1
    return max(1, sp)
