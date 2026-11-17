"""ArbZG section 3: daily working time."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta

from .model import INFO, VIOLATION, Finding, Shift, by_employee, hours

REGULAR_LIMIT = timedelta(hours=8)
ABSOLUTE_LIMIT = timedelta(hours=10)


def daily_totals(shifts: list[Shift]) -> dict[str, dict]:
    """Working time per employee and calendar day (a shift counts on the day it starts)."""
    out: dict[str, dict] = {}
    for name, group in by_employee(shifts).items():
        days: dict = defaultdict(timedelta)
        for s in group:
            days[s.day] += s.work_time
        out[name] = dict(days)
    return out


def check_daily(shifts: list[Shift]) -> list[Finding]:
    findings: list[Finding] = []
    for name, days in daily_totals(shifts).items():
        for day, total in sorted(days.items()):
            when = datetime.combine(day, time())
            if total > ABSOLUTE_LIMIT:
                findings.append(Finding(
                    "DAILY_OVER_10", "ArbZG §3", VIOLATION, name, when,
                    f"{hours(total)} h of work on one day; the limit is 10 h even with averaging"))
            elif total > REGULAR_LIMIT:
                findings.append(Finding(
                    "DAILY_OVER_8", "ArbZG §3", INFO, name, when,
                    f"{hours(total)} h exceeds the regular 8 h; allowed up to 10 h only if the average "
                    "stays at 8 h per working day over 24 weeks"))
    return findings
