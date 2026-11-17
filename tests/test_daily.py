import pytest

from arbzg_check.rules_daily import check_daily, daily_totals

from .helpers import shift


def rules(shifts):
    return [f.rule for f in check_daily(shifts)]


def test_exactly_8_hours_is_fine():
    assert rules([shift("a", "2026-03-02 06:00", "14:00")]) == []


def test_over_8_hours_is_information_not_a_violation():
    found = check_daily([shift("a", "2026-03-02 06:00", "14:01")])
    assert [(f.rule, f.severity) for f in found] == [("DAILY_OVER_8", "info")]


def test_exactly_10_hours_is_not_a_violation():
    assert rules([shift("a", "2026-03-02 06:00", "16:00")]) == ["DAILY_OVER_8"]


def test_over_10_hours_is_a_violation():
    found = check_daily([shift("a", "2026-03-02 06:00", "16:01")])
    assert [(f.rule, f.severity) for f in found] == [("DAILY_OVER_10", "violation")]


def test_two_shifts_on_one_day_are_added_up():
    ten = [shift("a", "2026-03-02 06:00", "11:00"), shift("a", "2026-03-02 14:00", "19:00")]
    eleven = [shift("a", "2026-03-02 06:00", "11:00"), shift("a", "2026-03-02 14:00", "20:00")]
    assert rules(ten) == ["DAILY_OVER_8"]
    assert rules(eleven) == ["DAILY_OVER_10"]


def test_overnight_shift_is_counted_whole_on_its_start_day():
    totals = daily_totals([shift("a", "2026-03-02 22:00", "06:00")])
    assert list(totals["a"].values())[0].total_seconds() == 8 * 3600
    assert len(totals["a"]) == 1


def test_people_are_counted_separately():
    assert rules([shift("a", "2026-03-02 06:00", "11:00"), shift("b", "2026-03-02 14:00", "19:00")]) == []


def test_unpaid_break_time_is_not_working_time():
    # 06:00-16:30 is 10.5 h on the clock, 10 h of work after a 30 min break
    assert rules([shift("a", "2026-03-02 06:00", "16:30", ("10:00", "10:30"))]) == ["DAILY_OVER_8"]
