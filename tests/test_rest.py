from datetime import timedelta

import pytest

from arbzg_check.rules_rest import check_rest

from .helpers import dt, shift


def run(shifts, sector=None):
    return [(f.rule, f.severity) for f in check_rest(shifts, sector)]


def test_exactly_11_hours_is_fine():
    assert run([shift("a", "2026-03-02 06:00", "14:00"), shift("a", "2026-03-03 01:00", "09:00")]) == []


def test_ten_hours_fifty_nine_is_a_violation():
    found = check_rest([shift("a", "2026-03-02 14:00", "22:00"), shift("a", "2026-03-03 08:59", "16:00")])
    assert [f.rule for f in found] == ["REST_UNDER_11H"]
    assert "10:59" in found[0].message and "0:01 h short" in found[0].message


def test_late_to_early_rotation_is_caught():
    found = check_rest([shift("a", "2026-03-02 14:00", "22:00"), shift("a", "2026-03-03 06:00", "14:00")])
    assert [f.rule for f in found] == ["REST_UNDER_11H"]
    assert "8:00" in found[0].message


def test_night_shift_into_afternoon_shift():
    # night shift ends 06:00 Tuesday, next starts 16:00 the same day: 10 h
    assert run([shift("a", "2026-03-02 22:00", "06:00"), shift("a", "2026-03-03 16:00", "22:00")]) == [("REST_UNDER_11H", "violation")]
    assert run([shift("a", "2026-03-02 22:00", "06:00"), shift("a", "2026-03-03 17:00", "22:00")]) == []


def test_rest_is_checked_per_person():
    assert run([shift("a", "2026-03-02 14:00", "22:00"), shift("b", "2026-03-03 06:00", "14:00")]) == []


def test_two_shifts_on_one_day_are_two_rest_periods():
    split = [shift("a", "2026-03-02 06:00", "10:00"), shift("a", "2026-03-02 14:00", "18:00"),
             shift("a", "2026-03-03 04:00", "08:00")]
    assert run(split) == [("REST_UNDER_11H", "violation")] * 2


SECTOR_BASE = [shift("a", "2026-03-02 14:00", "22:00"), shift("a", "2026-03-03 08:30", "16:30")]  # 10:30 rest


def test_without_a_sector_a_ten_and_a_half_hour_rest_is_a_violation():
    assert run(SECTOR_BASE) == [("REST_UNDER_11H", "violation")]


def test_sector_may_cut_the_rest_if_a_12_hour_rest_follows():
    later = SECTOR_BASE + [shift("a", "2026-03-05 08:30", "16:30")]
    assert run(later, "hospitality") == [("REST_REDUCED", "info")]


def test_sector_cut_without_compensation_is_a_violation():
    assert run(SECTOR_BASE, "hospitality") == [("REST_REDUCTION_NOT_COMPENSATED", "violation")]


def daily(n):
    """n daily shifts, 11:00 to 23:30, with 11 h 30 min of rest in between (too short to compensate)."""
    base = dt("2026-03-02 11:00")
    return [shift("a", (base + timedelta(days=i)).strftime("%Y-%m-%d %H:%M"), "23:30") for i in range(n)]


def test_compensating_rest_must_start_within_four_weeks():
    cut = shift("a", "2026-03-01 12:00", "00:30")  # ends 00:30; the first daily shift starts 11:00: 10 h 30 min rest
    soon = [cut, *daily(20), shift("a", "2026-03-24 11:00", "19:00")]
    late = [cut, *daily(31), shift("a", "2026-04-03 11:00", "19:00")]
    assert run(soon, "transport") == [("REST_REDUCED", "info")]
    assert run(late, "transport") == [("REST_REDUCTION_NOT_COMPENSATED", "violation")]


def test_each_compensating_rest_is_used_once():
    seq = [shift("a", "2026-03-02 14:00", "22:00"), shift("a", "2026-03-03 08:30", "16:30"),
           shift("a", "2026-03-04 03:00", "11:00"), shift("a", "2026-03-06 11:00", "19:00")]
    assert run(seq, "transport") == [("REST_REDUCED", "info"), ("REST_REDUCTION_NOT_COMPENSATED", "violation")]


def test_even_a_sector_cannot_go_below_10_hours():
    found = check_rest([shift("a", "2026-03-02 14:00", "22:00"), shift("a", "2026-03-03 07:30", "15:30")], "hospitality")
    assert [f.rule for f in found] == ["REST_UNDER_11H"]
    assert "10 h even where" in found[0].message


def test_unknown_sector_is_rejected():
    with pytest.raises(ValueError, match="unknown sector"):
        check_rest([], "warehouse")
