"""Command line: arbzg-check roster.csv"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

from . import __version__
from .checker import Options, check
from .holidays import REGIONS
from .loader import RosterFormatError, load
from .model import INFO, SEVERITIES, VIOLATION, WARNING, Finding
from .rules_rest import REDUCIBLE_SECTORS

EXIT_OK, EXIT_FINDINGS, EXIT_INPUT = 0, 1, 2
_LABEL = {VIOLATION: "VIOLATION", WARNING: "warning", INFO: "info"}


def summary(findings: list[Finding]) -> dict[str, int]:
    counts = Counter(f.severity for f in findings)
    return {s: counts.get(s, 0) for s in SEVERITIES}


def render_text(findings: list[Finding], shifts: int, employees: int, show_info: bool) -> str:
    lines = [f"{shifts} shifts, {employees} employees"]
    shown = [f for f in findings if show_info or f.severity != INFO]
    for f in shown:
        row = f" (row {f.line})" if f.line else ""
        lines.append(f"{f.when:%Y-%m-%d}  {f.employee}  {_LABEL[f.severity]}  {f.rule}  [{f.section}]{row}")
        lines.append(f"    {f.message}")
    s = summary(findings)
    hidden = "" if show_info or not s[INFO] else f" ({s[INFO]} info hidden, use --show-info)"
    lines.append(f"{s[VIOLATION]} violations, {s[WARNING]} warnings{hidden}" if not show_info else
                 f"{s[VIOLATION]} violations, {s[WARNING]} warnings, {s[INFO]} info")
    lines.append("This is a screening tool, not legal advice. Collective agreements and permits can change the rules.")
    return "\n".join(lines)


def render_json(findings: list[Finding], shifts: int, employees: int) -> str:
    return json.dumps({
        "shifts": shifts, "employees": employees, "summary": summary(findings),
        "findings": [{"rule": f.rule, "section": f.section, "severity": f.severity, "employee": f.employee,
                      "when": f.when.isoformat(), "row": f.line, "message": f.message} for f in findings],
    }, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="arbzg-check", description="Check a shift roster against the German "
                                "Working Hours Act (ArbZG). A screening tool, not legal advice.")
    p.add_argument("roster", help="CSV file with columns employee, date, start, end and optionally breaks, break_min")
    p.add_argument("--sector", choices=sorted(REDUCIBLE_SECTORS),
                   help="sector that may cut the 11 h rest to 10 h with compensation (§5 Abs. 2)")
    p.add_argument("--region", choices=REGIONS, default="BE", help="public holidays to use (default: BE, Berlin)")
    p.add_argument("--sunday-offset", type=int, default=0, metavar="HOURS",
                   help="move the Sunday rest window by -6..6 hours, multi-shift plants only (§9 Abs. 2)")
    p.add_argument("--year", type=int, help="also check for 15 work-free Sundays in this calendar year (§11)")
    p.add_argument("--night-worker", action="append", default=[], metavar="NAME",
                   help="treat NAME as a night worker (repeatable); 48 night-work days a year are detected anyway")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--show-info", action="store_true", help="also print informational findings")
    p.add_argument("--fail-on", choices=(VIOLATION, WARNING), default=VIOLATION,
                   help="exit with status 1 at this severity or above (default: violation)")
    p.add_argument("--version", action="version", version=f"arbzg-check {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        shifts = load(args.roster)
    except OSError as e:
        print(f"error: cannot read {args.roster}: {e.strerror}", file=sys.stderr)
        return EXIT_INPUT
    except RosterFormatError as e:
        print(f"error: {args.roster} is not a valid roster", file=sys.stderr)
        for line, msg in e.problems:
            print(f"  line {line}: {msg}" if line else f"  {msg}", file=sys.stderr)
        return EXIT_INPUT
    try:
        findings = check(shifts, Options(args.sector, args.region, args.sunday_offset, args.year,
                                         frozenset(args.night_worker)))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_INPUT
    employees = len({s.employee for s in shifts})
    if args.format == "json":
        print(render_json(findings, len(shifts), employees))
    else:
        print(render_text(findings, len(shifts), employees, args.show_info))
    s = summary(findings)
    failing = s[VIOLATION] + (s[WARNING] if args.fail_on == WARNING else 0)
    return EXIT_FINDINGS if failing else EXIT_OK
