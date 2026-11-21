"""Averaging periods for days over 8 hours.

Section 3 allows up to 10 hours a day if the average stays at 8 hours per working day over 24
weeks; section 6 Abs. 2 does the same for night workers over 4 weeks. A working day (Werktag) is
any day that is not a Sunday or public holiday, so a free Saturday still counts as a day with
0 hours. Work on Sundays and holidays is added to the hours but not to the day count.

A day over 8 hours passes if at least one reference window that contains it and lies fully inside
the roster has an average of 8 hours or less. If no such window exists the roster is too short
and the day is reported as not assessable, not as a violation.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta

from .holidays import holiday_name
from .model import INFO, VIOLATION, Finding, Shift, by_employee
from .rules_daily import ABSOLUTE_LIMIT, REGULAR_LIMIT, daily_totals
from .rules_night import is_night_work

GENERAL = (24 * 7, "DAILY_AVERAGE_NOT_MET", "ArbZG §3", "24 weeks")
NIGHT = (4 * 7, "NIGHT_DAILY_AVERAGE_NOT_MET", "ArbZG §6 Abs. 2", "4 weeks")


def check_averages(shifts: list[Shift], region: str = "BE",
                   night_worker_names: frozenset[str] | set[str] = frozenset()) -> list[Finding]:
    if not shifts:
        return []
    first = min(s.day for s in shifts)
    last = max(s.day for s in shifts)
    n = (last - first).days + 1
    dates = [first + timedelta(days=i) for i in range(n)]
    werktag = [0 if d.weekday() == 6 or holiday_name(d, region) else 1 for d in dates]
    work_days = [0]
    for w in werktag:
        work_days.append(work_days[-1] + w)
    limit = int(REGULAR_LIMIT.total_seconds() // 60)
    findings: list[Finding] = []
    totals = daily_totals(shifts)
    for name, group in by_employee(shifts).items():
        night_days = {s.day for s in group if is_night_work(s)} if name in night_worker_names else set()
        minutes = [int(totals[name].get(d, timedelta()).total_seconds() // 60) for d in dates]
        prefix = [0]
        for m in minutes:
            prefix.append(prefix[-1] + m)
        for i, d in enumerate(dates):
            total = timedelta(minutes=minutes[i])
            if not REGULAR_LIMIT < total <= ABSOLUTE_LIMIT:
                continue
            width, rule, section, label = NIGHT if d in night_days else GENERAL
            starts = range(max(0, i - width + 1), min(i, n - width) + 1)
            when = datetime.combine(d, time())
            if not starts:
                findings.append(Finding(
                    "AVERAGING_NOT_ASSESSED", section, INFO, name, when,
                    f"{d:%Y-%m-%d} is over 8 h, but the roster covers {n} days and the reference "
                    f"period is {label}; the average could not be checked"))
                continue
            best = min((prefix[s + width] - prefix[s]) / (work_days[s + width] - work_days[s]) for s in starts)
            if best > limit:
                findings.append(Finding(
                    rule, section, VIOLATION, name, when,
                    f"{d:%Y-%m-%d} is over 8 h and no {label} window containing it averages 8 h per "
                    f"working day; the best is {best / 60:.2f} h"))
    return findings
