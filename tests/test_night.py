from datetime import timedelta

from arbzg_check.rules_night import check_night, is_night_work, night_overlap, night_workers

from .helpers import dt, shift


def hours_of(s):
    return night_overlap(s).total_seconds() / 3600


def test_overlap_with_23_to_06():
    assert hours_of(shift("a", "2026-03-02 22:00", "06:00")) == 7
    assert hours_of(shift("a", "2026-03-02 14:00", "22:00")) == 0
    assert hours_of(shift("a", "2026-03-02 05:00", "13:00")) == 1
    assert hours_of(shift("a", "2026-03-02 00:00", "08:00")) == 6


def test_night_work_means_more_than_two_hours_of_night_time():
    assert not is_night_work(shift("a", "2026-03-02 15:00", "01:00"))  # exactly 2 h
    assert is_night_work(shift("a", "2026-03-02 15:00", "01:01"))
    assert is_night_work(shift("a", "2026-03-02 22:00", "06:00"))


def nights(n, name="a"):
    start, out = dt("2026-01-01 22:00"), []
    for i in range(n):
        out.append(shift(name, (start + timedelta(days=i)).strftime("%Y-%m-%d %H:%M"), "06:00"))
    return out


def test_48_days_of_night_work_in_a_year_make_a_night_worker():
    assert night_workers(nights(47)) == {}
    assert night_workers(nights(48)) == {"a": "48 night-work days in 2026"}


def test_declared_night_workers_are_kept():
    assert night_workers(nights(3), frozenset({"a", "z"})) == {"a": "declared", "z": "declared"}


def test_only_people_in_the_roster_are_reported():
    found = check_night(nights(3), frozenset({"a", "z"}))
    assert [(f.rule, f.employee, f.severity) for f in found] == [("NIGHT_WORKER", "a", "info")]


def test_day_shifts_never_make_a_night_worker():
    days = [shift("a", f"2026-01-{d:02d} 06:00", "14:00") for d in range(1, 29)]
    assert night_workers(days) == {}
