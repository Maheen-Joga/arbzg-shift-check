"""Run every rule over a roster."""
from __future__ import annotations

from dataclasses import dataclass

from .model import Finding, Shift
from .rules_breaks import check_breaks
from .rules_daily import check_daily
from .rules_rest import check_rest


@dataclass(frozen=True)
class Options:
    sector: str | None = None  # healthcare, hospitality, transport, broadcasting, agriculture (§5 Abs. 2)


def check(shifts: list[Shift], options: Options | None = None) -> list[Finding]:
    opts = options or Options()
    findings = [
        *check_daily(shifts),
        *check_breaks(shifts),
        *check_rest(shifts, opts.sector),
    ]
    return sorted(findings, key=lambda f: (f.employee, f.when, f.rule))
