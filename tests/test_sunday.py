from datetime import timedelta

import pytest

from arbzg_check.rules_sunday import check_sunday

from .helpers import dt, shift


def rules(shifts, **kw):
    return [(f.rule, f.severity) for f in check_sunday(shifts, **kw)]


def run_of_days(first, last, skip=()):
    """Daily 08:00-16:00 shifts for 'a' from first to last (YYYY-MM-DD), leaving out the dates in skip."""
    day, out = dt(first + " 08:00"), []
    while day <= dt(last + " 08:00"):
        if day.strftime("%Y-%m-%d") not in skip:
            out.append(shift("a", day.strftime("%Y-%m-%d %H:%M"), "16:00"))
        day += timedelta(days=1)
    return out


def test_weekday_work_raises_nothing():
    assert rules([shift("a", "2026-03-03 08:00", "16:00")]) == []


def test_sunday_work_is_a_warning_with_the_hours():
    found = check_sunday([shift("a", "2026-03-15 08:00", "16:30", ("12:00", "12:30")), shift("b", "2026-03-16 08:00", "16:00")])
    sunday = [f for f in found if f.rule == "SUNDAY_WORK"]
    assert len(sunday) == 1 and sunday[0].severity == "warning" and "8:30 h" in sunday[0].message


def test_a_saturday_night_shift_reaching_into_sunday_counts_the_overlap():
    found = check_sunday([shift("a", "2026-03-14 22:00", "06:00")])
    assert [f.rule for f in found if f.rule == "SUNDAY_WORK"] == ["SUNDAY_WORK"]
    assert "6:00 h" in found[0].message


def test_moving_the_rest_window_six_hours_frees_that_night_shift():
    night = [shift("a", "2026-03-14 22:00", "06:00")]
    assert [r for r, _ in rules(night, offset_hours=6)] == []
    assert [r for r, _ in rules(night, offset_hours=0)].count("SUNDAY_WORK") == 1


def test_a_shift_that_ends_monday_morning_falls_into_a_shifted_window():
    sunday_night = [shift("a", "2026-03-15 22:00", "06:00")]
    assert [r for r, _ in rules(sunday_night, offset_hours=6)].count("SUNDAY_WORK") == 1
    assert [r for r, _ in rules(sunday_night, offset_hours=0)].count("SUNDAY_WORK") == 1


def test_offset_must_be_within_six_hours():
    with pytest.raises(ValueError, match="between -6 and 6"):
        check_sunday([], offset_hours=7)


def test_weekday_holiday_is_reported_as_holiday_work():
    found = check_sunday([shift("a", "2026-05-01 08:00", "16:00")])
    assert found[0].rule == "HOLIDAY_WORK" and "Tag der Arbeit" in found[0].message


def test_region_decides_what_is_a_holiday():
    march8 = [shift("a", "2026-03-09 08:00", "16:00")]  # a Monday, not a holiday in either region
    womens_day_2027 = [shift("a", "2027-03-08 08:00", "16:00")]  # a Monday
    assert rules(womens_day_2027, region="BE")[0][0] == "HOLIDAY_WORK"
    assert rules(womens_day_2027, region="DE") == []
    assert rules(march8) == []


def test_a_sunday_that_is_also_a_holiday_is_named_once():
    found = [f for f in check_sunday([shift("a", "2026-03-08 08:00", "16:00")]) if f.rule.endswith("_WORK")]
    assert len(found) == 1 and found[0].rule == "SUNDAY_WORK" and "Internationaler Frauentag" in found[0].message


def test_missing_substitute_rest_day_is_a_violation():
    # works every day from Sunday 15 March to Saturday 28 March: 14 days with no free day
    found = check_sunday(run_of_days("2026-03-15", "2026-03-28"))
    assert ("SUBSTITUTE_REST_MISSING", "violation") in [(f.rule, f.severity) for f in found]


def test_one_free_day_in_the_window_is_enough():
    assert "SUBSTITUTE_REST_MISSING" not in [f.rule for f in check_sunday(run_of_days("2026-03-15", "2026-03-28", skip=("2026-03-20",)))]


def test_free_day_on_day_14_still_counts_but_day_15_does_not():
    ok = run_of_days("2026-03-15", "2026-03-29", skip=("2026-03-28",))
    late = run_of_days("2026-03-15", "2026-03-29", skip=("2026-03-29",))
    assert "SUBSTITUTE_REST_MISSING" not in [f.rule for f in check_sunday(ok)]
    assert "SUBSTITUTE_REST_MISSING" in [f.rule for f in check_sunday(late)]


def test_substitute_day_is_not_judged_when_the_roster_ends_too_soon():
    found = check_sunday(run_of_days("2026-03-15", "2026-03-20"))
    assert ("SUBSTITUTE_REST_NOT_ASSESSED", "info") in [(f.rule, f.severity) for f in found]
    assert "SUBSTITUTE_REST_MISSING" not in [f.rule for f in found]


def missing_on(findings, day):
    return [f for f in findings if f.rule == "SUBSTITUTE_REST_MISSING" and f.when.date().isoformat() == day]


def test_weekday_holiday_gets_eight_weeks():
    # Friday 1 May is a holiday; its window is 56 days, 1 May to 25 June
    free_on_day_56 = run_of_days("2026-05-01", "2026-06-26", skip=("2026-06-25",))
    free_on_day_57 = run_of_days("2026-05-01", "2026-06-26", skip=("2026-06-26",))
    assert missing_on(check_sunday(free_on_day_56, region="DE"), "2026-05-01") == []
    assert len(missing_on(check_sunday(free_on_day_57, region="DE"), "2026-05-01")) == 1


def sundays_2026(n_worked):
    day, out = dt("2026-01-04 08:00"), []
    for _ in range(n_worked):
        out.append(shift("a", day.strftime("%Y-%m-%d %H:%M"), "16:00"))
        day += timedelta(days=7)
    return out


def test_fifteen_free_sundays_are_required_in_a_year():
    ok, bad = sundays_2026(37), sundays_2026(38)  # 2026 has 52 Sundays
    assert "FREE_SUNDAYS_UNDER_15" not in [f.rule for f in check_sunday(ok, assess_year=2026)]
    found = [f for f in check_sunday(bad, assess_year=2026) if f.rule == "FREE_SUNDAYS_UNDER_15"]
    assert len(found) == 1 and "14 work-free Sundays in 2026" in found[0].message


def test_free_sundays_are_not_assessed_unless_a_year_is_given():
    assert "FREE_SUNDAYS_UNDER_15" not in [f.rule for f in check_sunday(sundays_2026(52))]
