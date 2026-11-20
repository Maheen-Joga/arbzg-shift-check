"""Public holidays for Germany (national) and Berlin, computed without any data file.

Easter Sunday comes from the anonymous Gregorian algorithm; the movable holidays are fixed
offsets from it. Berlin adds International Women's Day (8 March) from 2019 and had one-off
holidays on 8 May 2020 and 8 May 2025; 18 June 2028 is a one-off holiday in Berlin as well.
Other states are not covered.
"""
from __future__ import annotations

from datetime import date, timedelta

REGIONS = ("DE", "BE")

_ONE_OFF = {
    "BE": {
        date(2020, 5, 8): "Tag der Befreiung (einmalig)",
        date(2025, 5, 8): "Tag der Befreiung (einmalig)",
        date(2028, 6, 18): "75. Jahrestag des Volksaufstands 1953 (einmalig)",
    },
}


def easter(year: int) -> date:
    a, b, c = year % 19, year // 100, year % 100
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * l) // 433
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def holidays(year: int, region: str = "BE") -> dict[date, str]:
    if region not in REGIONS:
        raise ValueError(f"unknown region {region!r}; choose from {list(REGIONS)}")
    ostern = easter(year)
    out = {
        date(year, 1, 1): "Neujahr",
        ostern - timedelta(days=2): "Karfreitag",
        ostern + timedelta(days=1): "Ostermontag",
        date(year, 5, 1): "Tag der Arbeit",
        ostern + timedelta(days=39): "Christi Himmelfahrt",
        ostern + timedelta(days=50): "Pfingstmontag",
        date(year, 10, 3): "Tag der Deutschen Einheit",
        date(year, 12, 25): "1. Weihnachtstag",
        date(year, 12, 26): "2. Weihnachtstag",
    }
    if region == "BE":
        if year >= 2019:
            out[date(year, 3, 8)] = "Internationaler Frauentag"
        out.update({d: n for d, n in _ONE_OFF["BE"].items() if d.year == year})
    return dict(sorted(out.items()))


def holiday_name(day: date, region: str = "BE") -> str | None:
    return holidays(day.year, region).get(day)
