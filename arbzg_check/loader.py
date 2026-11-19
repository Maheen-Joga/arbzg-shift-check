"""Read a roster from CSV.

Required columns: employee, date, start, end. Optional: breaks, break_min.

  date        2026-03-02 or 02.03.2026
  start, end  HH:MM; an end at or before the start means the shift ends the next day
  breaks      HH:MM-HH:MM, several separated by |  (for example 12:00-12:30|15:00-15:15)
  break_min   a total in minutes when positions are unknown; the break is placed mid-shift and
              flagged as assumed, so the rule on 6 hours without a break cannot be checked

The delimiter (comma or semicolon) is detected from the header line.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path

from .model import Break, RosterError, Shift, by_employee

REQUIRED = ("employee", "date", "start", "end")
_TIME = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


class RosterFormatError(RosterError):
    """The file could not be read; `problems` lists every row-level cause as (line, message)."""

    def __init__(self, problems: list[tuple[int, str]]):
        self.problems = problems
        super().__init__("; ".join(f"line {n}: {m}" if n else m for n, m in problems))


def _time(text: str) -> time:
    m = _TIME.match(text.strip())
    if not m:
        raise ValueError(f"time {text!r} is not HH:MM")
    return time(int(m[1]), int(m[2]))


def _date(text: str) -> date:
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"date {text!r} is not YYYY-MM-DD or DD.MM.YYYY")


def _after(day: date, t: time, not_before: datetime) -> datetime:
    """The first moment with clock time t that is not before `not_before` (searching from `day`)."""
    cand = datetime.combine(day, t)
    return cand if cand >= not_before else cand + timedelta(days=1)


def _breaks(text: str, start: datetime) -> tuple[Break, ...]:
    out, cursor = [], start
    for part in filter(None, (p.strip() for p in text.split("|"))):
        a, sep, b = part.partition("-")
        if not sep:
            raise ValueError(f"break {part!r} is not HH:MM-HH:MM")
        b_start = _after(cursor.date(), _time(a), cursor)
        b_end = _after(b_start.date(), _time(b), b_start)
        out.append(Break(b_start, b_end))
        cursor = b_end
    return tuple(out)


def _shift(row: dict[str, str], line: int) -> Shift:
    day = _date(row["date"])
    t_start, t_end = _time(row["start"]), _time(row["end"])
    if t_start == t_end:
        raise ValueError("start and end are the same time")
    start = datetime.combine(day, t_start)
    end = datetime.combine(day, t_end)
    if end <= start:
        end += timedelta(days=1)
    spec, minutes = (row.get("breaks") or "").strip(), (row.get("break_min") or "").strip()
    if spec and minutes:
        raise ValueError("give either breaks or break_min, not both")
    if spec:
        return Shift(row["employee"].strip(), start, end, _breaks(spec, start), False, line)
    if minutes:
        if not minutes.isdigit():
            raise ValueError(f"break_min {minutes!r} is not a whole number of minutes")
        total = timedelta(minutes=int(minutes))
        if total >= end - start:
            raise ValueError("break_min is as long as the whole shift")
        if total:
            b_start = start + (end - start - total) / 2
            return Shift(row["employee"].strip(), start, end, (Break(b_start, b_start + total),), True, line)
    return Shift(row["employee"].strip(), start, end, (), False, line)


def loads(text: str) -> list[Shift]:
    text = text.lstrip("﻿")
    lines = text.splitlines()
    if not lines or not lines[0].strip():
        raise RosterFormatError([(0, "the file is empty")])
    delimiter = ";" if lines[0].count(";") > lines[0].count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    header = [h.strip().lower() for h in (reader.fieldnames or [])]
    missing = [c for c in REQUIRED if c not in header]
    if missing:
        raise RosterFormatError([(1, f"missing column(s): {', '.join(missing)}")])
    reader.fieldnames = header
    shifts: list[Shift] = []
    problems: list[tuple[int, str]] = []
    for row in reader:
        line = reader.line_num
        if not any((v or "").strip() for v in row.values() if isinstance(v, str)):
            continue
        clean = {k: (v or "").strip() for k, v in row.items() if isinstance(k, str)}
        try:
            shifts.append(_shift(clean, line))
        except (ValueError, RosterError) as e:
            problems.append((line, str(e)))
    if problems:
        raise RosterFormatError(problems)
    if not shifts:
        raise RosterFormatError([(0, "the roster has no shifts")])
    try:
        by_employee(shifts)
    except RosterError as e:
        raise RosterFormatError([(0, str(e))]) from None
    return shifts


def load(path: str | Path) -> list[Shift]:
    return loads(Path(path).read_text(encoding="utf-8"))
