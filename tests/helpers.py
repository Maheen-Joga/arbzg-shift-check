"""Small builders so tests read like a roster."""
from datetime import datetime, timedelta

from arbzg_check import Break, Shift


def dt(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%d %H:%M")


def _clock(day: datetime, hhmm: str, not_before: datetime) -> datetime:
    t = datetime.strptime(hhmm, "%H:%M").time()
    out = datetime.combine(day.date(), t)
    return out if out >= not_before else out + timedelta(days=1)


def shift(employee: str, start: str, end: str, *breaks: tuple[str, str], assumed: bool = False, line=None) -> Shift:
    """shift("anna", "2026-03-02 06:00", "14:30", ("10:00", "10:30")).

    `end` and break times are clock times; an earlier clock time means the next day.
    """
    s = dt(start)
    e = _clock(s, end, s + timedelta(minutes=1))
    bs, cursor = [], s
    for a, b in breaks:
        b_start = _clock(cursor, a, cursor)
        b_end = _clock(b_start, b, b_start + timedelta(minutes=1))
        bs.append(Break(b_start, b_end))
        cursor = b_end
    return Shift(employee, s, e, tuple(bs), assumed, line)
