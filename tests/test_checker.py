import random
from datetime import timedelta
from pathlib import Path

from arbzg_check import Options, check, load

from .helpers import dt, shift

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def pairs(findings, minimum="violation"):
    order = {"violation": 0, "warning": 1, "info": 2}
    return sorted({(f.employee, f.rule) for f in findings if order[f.severity] <= order[minimum]})


def test_the_clean_example_has_no_violations_or_warnings():
    assert pairs(check(load(EXAMPLES / "roster_ok.csv")), "warning") == []


def test_the_violation_example_triggers_exactly_the_intended_rules():
    found = check(load(EXAMPLES / "roster_violations.csv"))
    assert pairs(found) == [
        ("chris", "BREAK_TOO_SHORT"), ("chris", "DAILY_OVER_10"),
        ("dana", "BREAK_TOO_SHORT"), ("dana", "WORK_STRETCH_OVER_6H"),
        ("eli", "BREAK_TOO_SHORT"), ("eli", "WORK_STRETCH_OVER_6H"),
        ("fatima", "REST_UNDER_11H"),
    ]
    assert ("gabor", "SUNDAY_WORK") in pairs(found, "warning")
    assert ("hana", "DAILY_OVER_8") in pairs(found, "info")


def test_findings_are_sorted_by_person_then_time():
    found = check(load(EXAMPLES / "roster_violations.csv"))
    assert [(f.employee, f.when, f.rule) for f in found] == sorted((f.employee, f.when, f.rule) for f in found)


def test_options_reach_the_rules():
    two = [shift("a", "2026-03-02 14:00", "22:00"), shift("a", "2026-03-03 08:30", "16:30"),
           shift("a", "2026-03-05 08:30", "16:30")]
    assert "REST_UNDER_11H" in {f.rule for f in check(two)}
    assert "REST_REDUCED" in {f.rule for f in check(two, Options(sector="hospitality"))}
    sunday = [shift("a", "2026-03-14 22:00", "06:00")]
    assert "SUNDAY_WORK" in {f.rule for f in check(sunday)}
    assert "SUNDAY_WORK" not in {f.rule for f in check(sunday, Options(sunday_offset_hours=6))}
    assert "NIGHT_WORKER" in {f.rule for f in check(sunday, Options(night_workers=frozenset({"a"})))}
    year = [shift("a", "2026-01-04 08:00", "16:00")]
    assert "FREE_SUNDAYS_UNDER_15" not in {f.rule for f in check(year, Options(assess_year=2026))}


def test_random_rosters_never_crash_and_stay_sorted():
    rng = random.Random(7)
    for _ in range(25):
        shifts = []
        for name in "abcde":
            cursor = dt("2026-02-20 00:00") + timedelta(hours=rng.randint(0, 30))
            for _ in range(rng.randint(1, 25)):
                length = timedelta(minutes=rng.randint(60, 14 * 60))
                begin, end = cursor, cursor + length
                breaks = []
                if length > timedelta(hours=3) and rng.random() < 0.8:
                    b = begin + timedelta(minutes=rng.randint(30, 120))
                    breaks = [(b.strftime("%H:%M"), (b + timedelta(minutes=rng.choice([5, 15, 30, 45]))).strftime("%H:%M"))]
                shifts.append(shift(name, begin.strftime("%Y-%m-%d %H:%M"), end.strftime("%H:%M"), *breaks))
                cursor = end + timedelta(hours=rng.randint(6, 40))
        found = check(shifts, Options(night_workers=frozenset({"a"})))
        keys = [(f.employee, f.when, f.rule) for f in found]
        assert keys == sorted(keys)
        assert all(f.severity in {"violation", "warning", "info"} for f in found)
