"""Run every rule over a roster."""
from __future__ import annotations

from .model import Finding, Shift
from .rules_breaks import check_breaks
from .rules_daily import check_daily


def check(shifts: list[Shift]) -> list[Finding]:
    findings = [*check_daily(shifts), *check_breaks(shifts)]
    return sorted(findings, key=lambda f: (f.employee, f.when, f.rule))
