"""ArbZG sections 9 and 11: Sunday and public-holiday rest.

Work on a Sunday or holiday is reported as a warning, because it is lawful with an exemption
(sections 10, 13 to 15 or a permit) that a roster cannot show. What the roster can show is
reported as a violation: fewer than 15 free Sundays in a year, and a missing substitute day.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from .holidays import holiday_name
from .model import INFO, VIOLATION, WARNING, Finding, Shift, by_employee, hours

FREE_SUNDAYS_PER_YEAR = 15
SUNDAY_SUBSTITUTE_DAYS = 14  # a work-free day within 14 days, counting the worked day as day 1
HOLIDAY_SUBSTITUTE_DAYS = 56  # within 8 weeks


def _window(day: date, offset_hours: int) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time()) + timedelta(hours=offset_hours)
    return start, start + timedelta(days=1)


def _overlap(s: Shift, lo: datetime, hi: datetime) -> timedelta:
    return max(timedelta(), min(s.end, hi) - max(s.start, lo))


def _works_on(group: list[Shift], day: date) -> bool:
    lo = datetime.combine(day, time())
    return any(_overlap(s, lo, lo + timedelta(days=1)) > timedelta() for s in group)


def _days(first: date, last: date):
    d = first
    while d <= last:
        yield d
        d += timedelta(days=1)


def check_sunday(shifts: list[Shift], region: str = "BE", offset_hours: int = 0,
                 assess_year: int | None = None) -> list[Finding]:
    """offset_hours moves the 24 h rest window (section 9 Abs. 2, multi-shift operations):
    up to 6 hours earlier or later, valid only if the plant is idle for the 24 h after it begins."""
    if not -6 <= offset_hours <= 6:
        raise ValueError("offset_hours must be between -6 and 6 (ArbZG §9 Abs. 2)")
    findings: list[Finding] = []
    groups = by_employee(shifts)
    last_end = max(s.end for s in shifts).date() if shifts else None
    for name, group in groups.items():
        first = group[0].start.date() - timedelta(days=1)
        for day in _days(first, group[-1].end.date()):
            holiday = holiday_name(day, region)
            if day.weekday() != 6 and not holiday:
                continue
            lo, hi = _window(day, offset_hours)
            worked = [(s, _overlap(s, lo, hi)) for s in group]
            worked = [(s, o) for s, o in worked if o > timedelta()]
            if not worked:
                continue
            label = f"Sunday ({holiday})" if holiday and day.weekday() == 6 else (holiday or "Sunday")
            rule = "SUNDAY_WORK" if day.weekday() == 6 else "HOLIDAY_WORK"
            total = sum((o for _, o in worked), timedelta())
            findings.append(Finding(
                rule, "ArbZG §9 Abs. 1", WARNING, name, datetime.combine(day, time()),
                f"{hours(total)} h of work on {label} {day:%Y-%m-%d}; lawful only with an exemption "
                "(§10, §13 to §15) or a permit", worked[0][0].line))
            days_allowed = SUNDAY_SUBSTITUTE_DAYS if day.weekday() == 6 else HOLIDAY_SUBSTITUTE_DAYS
            window_end = day + timedelta(days=days_allowed - 1)
            if last_end is None or last_end < window_end:
                findings.append(Finding(
                    "SUBSTITUTE_REST_NOT_ASSESSED", "ArbZG §11 Abs. 3", INFO, name,
                    datetime.combine(day, time()),
                    f"the roster ends before {window_end:%Y-%m-%d}, so the substitute rest day for "
                    f"{day:%Y-%m-%d} could not be checked", worked[0][0].line))
            elif not any(not _works_on(group, d) for d in _days(day + timedelta(days=1), window_end)):
                findings.append(Finding(
                    "SUBSTITUTE_REST_MISSING", "ArbZG §11 Abs. 3", VIOLATION, name,
                    datetime.combine(day, time()),
                    f"work on {label} {day:%Y-%m-%d} needs a work-free day within {days_allowed} days "
                    f"(until {window_end:%Y-%m-%d}); there is none", worked[0][0].line))
        if assess_year is not None:
            sundays = [d for d in _days(date(assess_year, 1, 1), date(assess_year, 12, 31)) if d.weekday() == 6]
            free = 0
            for d in sundays:
                lo, hi = _window(d, offset_hours)
                if not any(_overlap(s, lo, hi) > timedelta() for s in group):
                    free += 1
            if free < FREE_SUNDAYS_PER_YEAR:
                findings.append(Finding(
                    "FREE_SUNDAYS_UNDER_15", "ArbZG §11 Abs. 1", VIOLATION, name,
                    datetime.combine(date(assess_year, 12, 31), time()),
                    f"{free} work-free Sundays in {assess_year}; at least {FREE_SUNDAYS_PER_YEAR} are required"))
    return findings
