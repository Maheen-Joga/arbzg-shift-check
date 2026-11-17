"""Data model: shifts, breaks and findings.

All times are naive local wall-clock times. Daylight-saving changes are not modelled, so a
shift that spans the clock change is off by one hour. A shift belongs to the calendar day on
which it starts.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

MIN_BREAK_SEGMENT = timedelta(minutes=15)  # ArbZG section 4: a break counts from 15 minutes

VIOLATION = "violation"
WARNING = "warning"
INFO = "info"
SEVERITIES = (VIOLATION, WARNING, INFO)


class RosterError(ValueError):
    """The roster itself is inconsistent (as opposed to breaking a working-time rule)."""


@dataclass(frozen=True)
class Break:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise RosterError(f"break must end after it starts ({self.start} to {self.end})")

    @property
    def duration(self) -> timedelta:
        return self.end - self.start


@dataclass(frozen=True)
class Shift:
    employee: str
    start: datetime
    end: datetime
    breaks: tuple[Break, ...] = ()
    breaks_assumed: bool = False  # True when only a total was given and the break was placed mid-shift
    line: int | None = None  # source row, used in messages

    def __post_init__(self) -> None:
        if not self.employee:
            raise RosterError("shift has no employee")
        if self.end <= self.start:
            raise RosterError(f"shift must end after it starts ({self.start} to {self.end})")
        prev_end = self.start
        for b in self.breaks:
            if b.start < prev_end or b.end > self.end:
                raise RosterError(f"breaks must lie inside the shift and not overlap ({self.start} to {self.end})")
            prev_end = b.end

    @property
    def day(self) -> date:
        return self.start.date()

    @property
    def span(self) -> timedelta:
        return self.end - self.start

    @property
    def counted_breaks(self) -> tuple[Break, ...]:
        """Only breaks of at least 15 minutes are rest breaks in the sense of the law."""
        return tuple(b for b in self.breaks if b.duration >= MIN_BREAK_SEGMENT)

    @property
    def break_time(self) -> timedelta:
        return sum((b.duration for b in self.counted_breaks), timedelta())

    @property
    def work_time(self) -> timedelta:
        return self.span - self.break_time

    def work_stretches(self) -> list[timedelta]:
        """Lengths of uninterrupted work, split at every counted break."""
        out, cursor = [], self.start
        for b in self.counted_breaks:
            out.append(b.start - cursor)
            cursor = b.end
        out.append(self.end - cursor)
        return out


@dataclass(frozen=True)
class Finding:
    rule: str  # stable identifier, e.g. REST_UNDER_11H
    section: str  # e.g. "ArbZG §5 Abs. 1"
    severity: str
    employee: str
    when: datetime
    message: str
    line: int | None = None

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"unknown severity {self.severity!r}")


def by_employee(shifts: list[Shift]) -> dict[str, list[Shift]]:
    """Group by employee, sorted by start. Overlapping shifts of one person are a roster error."""
    groups: dict[str, list[Shift]] = defaultdict(list)
    for s in shifts:
        groups[s.employee].append(s)
    for name, group in groups.items():
        group.sort(key=lambda s: (s.start, s.end))
        for a, b in zip(group, group[1:]):
            if b.start < a.end:
                where = f" (rows {a.line} and {b.line})" if a.line and b.line else ""
                raise RosterError(f"{name}: shifts overlap, {a.start:%Y-%m-%d %H:%M} to {a.end:%H:%M} and "
                                  f"{b.start:%Y-%m-%d %H:%M}{where}")
    return dict(groups)


def hours(td: timedelta) -> str:
    """Format a duration as H:MM, e.g. 8:30."""
    minutes = round(td.total_seconds() / 60)
    sign = "-" if minutes < 0 else ""
    h, m = divmod(abs(minutes), 60)
    return f"{sign}{h}:{m:02d}"
