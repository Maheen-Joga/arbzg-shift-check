from datetime import timedelta

import pytest

from arbzg_check.rules_breaks import check_breaks, required_break

from .helpers import shift


def rules(*shifts):
    return sorted(f.rule for f in check_breaks(list(shifts)))


@pytest.mark.parametrize("minutes, need", [(360, 0), (361, 30), (540, 30), (541, 45), (600, 45), (0, 0)])
def test_required_break_boundaries(minutes, need):
    assert required_break(timedelta(minutes=minutes)) == timedelta(minutes=need)


def test_six_hours_exactly_needs_no_break():
    assert rules(shift("a", "2026-03-02 06:00", "12:00")) == []


def test_just_over_six_hours_without_break_breaks_two_rules():
    assert rules(shift("a", "2026-03-02 06:00", "12:01")) == ["BREAK_TOO_SHORT", "WORK_STRETCH_OVER_6H"]


def test_standard_eight_hour_shift_with_30_minutes_is_fine():
    assert rules(shift("a", "2026-03-02 06:00", "14:30", ("10:00", "10:30"))) == []


def test_nine_hours_of_work_needs_30_minutes_but_not_45():
    assert rules(shift("a", "2026-03-02 06:00", "15:30", ("10:00", "10:30"))) == []


def test_over_nine_hours_of_work_needs_45_minutes():
    short = shift("a", "2026-03-02 06:00", "15:40", ("10:00", "10:30"))  # 9:10 of work
    enough = shift("a", "2026-03-02 06:00", "15:45", ("10:00", "10:45"))  # 9:00 of work
    assert rules(short) == ["BREAK_TOO_SHORT"]
    assert rules(enough) == []


def test_break_may_be_split_into_blocks_of_15_minutes():
    s = shift("a", "2026-03-02 06:00", "14:30", ("09:00", "09:15"), ("12:00", "12:15"))
    assert rules(s) == []


def test_pauses_under_15_minutes_do_not_count_and_are_reported():
    s = shift("a", "2026-03-02 06:00", "14:30", ("09:00", "09:10"), ("12:00", "12:20"))
    found = check_breaks([s])
    assert sorted(f.rule for f in found) == ["BREAK_SEGMENT_UNDER_15", "BREAK_TOO_SHORT"]
    assert next(f for f in found if f.rule == "BREAK_TOO_SHORT").message.endswith("found 20 min")


def test_more_than_six_hours_before_the_break_is_a_violation():
    s = shift("a", "2026-03-02 06:00", "15:00", ("12:30", "13:15"))  # 6:30 then 1:45 of work
    found = check_breaks([s])
    assert [f.rule for f in found] == ["WORK_STRETCH_OVER_6H"]
    assert "6:30" in found[0].message


def test_exactly_six_hours_before_the_break_is_fine():
    assert rules(shift("a", "2026-03-02 06:00", "15:00", ("12:00", "12:45"))) == []


def test_overnight_shift_is_checked_across_midnight():
    assert rules(shift("a", "2026-03-02 22:00", "06:30", ("01:00", "01:30"))) == []
    assert rules(shift("a", "2026-03-02 22:00", "06:30", ("04:15", "04:45"))) == ["WORK_STRETCH_OVER_6H"]


def test_assumed_break_position_skips_the_stretch_rule_and_says_so():
    s = shift("a", "2026-03-02 06:00", "14:30", ("10:00", "10:30"), assumed=True)
    assert rules(s) == ["BREAK_POSITION_UNKNOWN"]


def test_assumed_break_is_still_checked_for_length():
    s = shift("a", "2026-03-02 06:00", "14:30", ("10:00", "10:20"), assumed=True)
    assert rules(s) == ["BREAK_POSITION_UNKNOWN", "BREAK_TOO_SHORT"]


def test_findings_carry_the_source_row():
    f = check_breaks([shift("a", "2026-03-02 06:00", "13:00", line=7)])[0]
    assert f.line == 7 and f.section.startswith("ArbZG §4")
