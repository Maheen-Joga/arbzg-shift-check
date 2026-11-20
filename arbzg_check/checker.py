"""Run every rule over a roster."""
from __future__ import annotations

from dataclasses import dataclass

from .model import Finding, Shift
from .rules_breaks import check_breaks
from .rules_daily import check_daily
from .rules_rest import check_rest
from .rules_sunday import check_sunday


@dataclass(frozen=True)
class Options:
    sector: str | None = None  # healthcare, hospitality, transport, broadcasting, agriculture (§5 Abs. 2)
    region: str = "BE"  # public holidays: "BE" (Berlin) or "DE" (national only)
    sunday_offset_hours: int = 0  # shift the Sunday rest window, -6..6 (§9 Abs. 2)
    assess_year: int | None = None  # check 15 free Sundays (§11 Abs. 1) for this calendar year


def check(shifts: list[Shift], options: Options | None = None) -> list[Finding]:
    opts = options or Options()
    findings = [
        *check_daily(shifts),
        *check_breaks(shifts),
        *check_rest(shifts, opts.sector),
        *check_sunday(shifts, opts.region, opts.sunday_offset_hours, opts.assess_year),
    ]
    return sorted(findings, key=lambda f: (f.employee, f.when, f.rule))
