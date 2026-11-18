"""ArbZG section 5: uninterrupted rest period between two shifts."""
from __future__ import annotations

from datetime import timedelta

from .model import INFO, VIOLATION, Finding, Shift, by_employee, hours

REST = timedelta(hours=11)
REDUCED_REST = timedelta(hours=10)
COMPENSATING_REST = timedelta(hours=12)
COMPENSATION_WINDOW = timedelta(weeks=4)

# Section 5 Abs. 2: these sectors may cut the rest period by up to one hour.
REDUCIBLE_SECTORS = frozenset({"healthcare", "hospitality", "transport", "broadcasting", "agriculture"})


def check_rest(shifts: list[Shift], sector: str | None = None) -> list[Finding]:
    """Flag rest periods under 11 h.

    With a sector from REDUCIBLE_SECTORS a rest of 10 h to 11 h is allowed, but each such cut
    must be offset by a later rest of at least 12 h that starts within four weeks. Every
    compensating rest is used for one cut only.
    """
    if sector is not None and sector not in REDUCIBLE_SECTORS:
        raise ValueError(f"unknown sector {sector!r}; choose from {sorted(REDUCIBLE_SECTORS)}")
    findings: list[Finding] = []
    for name, group in by_employee(shifts).items():
        gaps = [(a, b, b.start - a.end) for a, b in zip(group, group[1:])]
        used: set[int] = set()
        for i, (a, b, gap) in enumerate(gaps):
            if gap >= REST:
                continue
            short = REST - gap
            if sector and gap >= REDUCED_REST:
                match = next((j for j in range(i + 1, len(gaps))
                              if j not in used and gaps[j][2] >= COMPENSATING_REST
                              and gaps[j][0].end - b.start <= COMPENSATION_WINDOW), None)
                if match is None:
                    findings.append(Finding(
                        "REST_REDUCTION_NOT_COMPENSATED", "ArbZG §5 Abs. 2", VIOLATION, name, b.start,
                        f"rest of {hours(gap)} h is cut by {hours(short)} h, which {sector} may do, but no "
                        "rest of 12 h or more starts within four weeks to offset it", b.line))
                else:
                    used.add(match)
                    findings.append(Finding(
                        "REST_REDUCED", "ArbZG §5 Abs. 2", INFO, name, b.start,
                        f"rest of {hours(gap)} h is cut by {hours(short)} h and offset by a rest of "
                        f"{hours(gaps[match][2])} h on {gaps[match][0].end:%Y-%m-%d}", b.line))
                continue
            limit = "10 h even where §5 Abs. 2 allows a cut" if sector else "11 h"
            findings.append(Finding(
                "REST_UNDER_11H", "ArbZG §5 Abs. 1", VIOLATION, name, b.start,
                f"rest of {hours(gap)} h after the shift ending {a.end:%Y-%m-%d %H:%M}; the minimum is "
                f"{limit} ({hours(short)} h short of 11 h)", b.line))
    return findings
