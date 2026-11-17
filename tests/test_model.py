from datetime import timedelta

import pytest

from arbzg_check import Break, RosterError, Shift
from arbzg_check.model import by_employee, hours

from .helpers import dt, shift


def test_work_time_subtracts_only_breaks_of_15_minutes_or_more():
    s = shift("a", "2026-03-02 06:00", "14:30", ("09:00", "09:10"), ("12:00", "12:30"))
    assert s.span == timedelta(hours=8, minutes=30)
    assert s.break_time == timedelta(minutes=30)
    assert s.work_time == timedelta(hours=8)


def test_work_stretches_split_at_counted_breaks():
    s = shift("a", "2026-03-02 06:00", "15:00", ("10:00", "10:30"), ("13:00", "13:15"))
    assert s.work_stretches() == [timedelta(hours=4), timedelta(hours=2, minutes=30), timedelta(hours=1, minutes=45)]


def test_short_pause_does_not_split_a_stretch():
    s = shift("a", "2026-03-02 06:00", "12:00", ("09:00", "09:10"))
    assert s.work_stretches() == [timedelta(hours=6)]


def test_overnight_shift_belongs_to_its_start_day():
    s = shift("a", "2026-03-02 22:00", "06:00")
    assert s.end == dt("2026-03-03 06:00") and s.day.isoformat() == "2026-03-02"


def test_shift_must_end_after_it_starts():
    with pytest.raises(RosterError):
        Shift("a", dt("2026-03-02 10:00"), dt("2026-03-02 10:00"))


def test_breaks_must_lie_inside_the_shift_and_not_overlap():
    with pytest.raises(RosterError):
        Shift("a", dt("2026-03-02 06:00"), dt("2026-03-02 10:00"), (Break(dt("2026-03-02 09:30"), dt("2026-03-02 10:30")),))
    with pytest.raises(RosterError):
        Shift("a", dt("2026-03-02 06:00"), dt("2026-03-02 14:00"),
              (Break(dt("2026-03-02 09:00"), dt("2026-03-02 09:30")), Break(dt("2026-03-02 09:15"), dt("2026-03-02 09:45"))))


def test_overlapping_shifts_of_one_person_are_a_roster_error():
    a = shift("a", "2026-03-02 06:00", "14:00", line=2)
    b = shift("a", "2026-03-02 13:00", "20:00", line=3)
    with pytest.raises(RosterError, match="rows 2 and 3"):
        by_employee([a, b])


def test_same_times_for_different_people_are_fine():
    groups = by_employee([shift("a", "2026-03-02 06:00", "14:00"), shift("b", "2026-03-02 06:00", "14:00")])
    assert set(groups) == {"a", "b"}


@pytest.mark.parametrize("minutes, text", [(0, "0:00"), (510, "8:30"), (65, "1:05"), (-90, "-1:30")])
def test_hours_format(minutes, text):
    assert hours(timedelta(minutes=minutes)) == text
