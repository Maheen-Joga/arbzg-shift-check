"""ArbZG section 4: rest breaks."""
from __future__ import annotations

from datetime import timedelta

from .model import INFO, MIN_BREAK_SEGMENT, VIOLATION, WARNING, Finding, Shift, hours

LONG_STRETCH = timedelta(hours=6)


def required_break(work: timedelta) -> timedelta:
    """Minimum total break for a given amount of work: 30 min above 6 h, 45 min above 9 h."""
    if work > timedelta(hours=9):
        return timedelta(minutes=45)
    if work > timedelta(hours=6):
        return timedelta(minutes=30)
    return timedelta()


def check_breaks(shifts: list[Shift]) -> list[Finding]:
    findings: list[Finding] = []
    for s in sorted(shifts, key=lambda s: (s.employee, s.start)):
        for b in s.breaks:
            if b.duration < MIN_BREAK_SEGMENT:
                findings.append(Finding(
                    "BREAK_SEGMENT_UNDER_15", "ArbZG §4 Satz 2", WARNING, s.employee, b.start,
                    f"a {round(b.duration.total_seconds() / 60)} min pause does not count as a rest "
                    "break; breaks count from 15 min", s.line))
        need = required_break(s.work_time)
        if s.break_time < need:
            findings.append(Finding(
                "BREAK_TOO_SHORT", "ArbZG §4 Satz 1", VIOLATION, s.employee, s.start,
                f"{hours(s.work_time)} h of work needs at least {round(need.total_seconds() / 60)} min of "
                f"break, found {round(s.break_time.total_seconds() / 60)} min", s.line))
        if s.breaks_assumed:
            if s.work_time > LONG_STRETCH:
                findings.append(Finding(
                    "BREAK_POSITION_UNKNOWN", "ArbZG §4 Satz 3", INFO, s.employee, s.start,
                    "only a total break was given, so the 6 h limit on work without a break was not checked",
                    s.line))
            continue
        longest = max(s.work_stretches())
        if longest > LONG_STRETCH:
            findings.append(Finding(
                "WORK_STRETCH_OVER_6H", "ArbZG §4 Satz 3", VIOLATION, s.employee, s.start,
                f"{hours(longest)} h of work in a row without a break; the limit is 6 h", s.line))
    return findings
