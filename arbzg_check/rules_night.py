"""ArbZG sections 2 and 6: night work and night workers.

Night time is 23:00 to 06:00. Night work is work that covers more than two hours of it. A night
worker is someone who works night shifts in rotation or at least 48 days of night work in a
calendar year. The roster cannot show rotation, so such people are named by the caller; the
48-day test is applied automatically.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta

from .model import INFO, Finding, Shift, by_employee

NIGHT_START = time(23)
NIGHT_END = time(6)
NIGHT_WORK_OVER = timedelta(hours=2)
NIGHT_DAYS_PER_YEAR = 48


def night_overlap(s: Shift) -> timedelta:
    """How much of the shift lies in night time (23:00 to 06:00), breaks included."""
    total = timedelta()
    day = s.start.date() - timedelta(days=1)
    while day <= s.end.date():
        lo = datetime.combine(day, NIGHT_START)
        hi = datetime.combine(day + timedelta(days=1), NIGHT_END)
        total += max(timedelta(), min(s.end, hi) - max(s.start, lo))
        day += timedelta(days=1)
    return total


def is_night_work(s: Shift) -> bool:
    return night_overlap(s) > NIGHT_WORK_OVER


def night_workers(shifts: list[Shift], declared: frozenset[str] = frozenset()) -> dict[str, str]:
    """Map each night worker to the reason: 'declared' or '<n> night-work days in <year>'."""
    out = {name: "declared" for name in declared}
    for name, group in by_employee(shifts).items():
        per_year: dict[int, set] = defaultdict(set)
        for s in group:
            if is_night_work(s):
                per_year[s.day.year].add(s.day)
        for year, days in sorted(per_year.items()):
            if len(days) >= NIGHT_DAYS_PER_YEAR and name not in out:
                out[name] = f"{len(days)} night-work days in {year}"
    return out


def check_night(shifts: list[Shift], declared: frozenset[str] = frozenset()) -> list[Finding]:
    first_seen = {name: group[0].start for name, group in by_employee(shifts).items()}
    return [Finding("NIGHT_WORKER", "ArbZG §2 Abs. 5", INFO, name, first_seen.get(name, datetime.min),
                    f"treated as a night worker ({reason}); the 4-week average applies on night-work days")
            for name, reason in sorted(night_workers(shifts, declared).items())
            if name in first_seen]
