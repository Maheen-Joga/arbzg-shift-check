from datetime import timedelta

from arbzg_check.averaging import check_averages

from .helpers import dt, shift


def weekly(weeks, hours_by_weekday, start="2026-01-05", name="a", clock="06:00"):
    """Mon-Fri shifts of the given lengths in hours, repeated for `weeks` weeks."""
    monday, out = dt(start + " " + clock), []
    for w in range(weeks):
        for i, h in enumerate(hours_by_weekday):
            begin = monday + timedelta(days=7 * w + i)
            end = begin + timedelta(hours=h)
            out.append(shift(name, begin.strftime("%Y-%m-%d %H:%M"), end.strftime("%H:%M")))
    return out


def rules(findings):
    return sorted({(f.rule, f.severity) for f in findings})


def test_long_days_balanced_by_short_days_pass_the_24_week_average():
    roster = weekly(26, [10, 10, 10, 6, 4])  # 40 h a week over 6 working days
    assert rules(check_averages(roster, "DE")) == []


def test_ten_hour_days_every_week_fail_the_average():
    roster = weekly(26, [10] * 5)  # 50 h a week: 8.33 h per working day
    found = check_averages(roster, "DE")
    assert rules(found) == [("DAILY_AVERAGE_NOT_MET", "violation")]
    assert len(found) == 26 * 5 and "no 24 weeks window" in found[0].message


def test_a_short_roster_cannot_be_assessed_and_says_so():
    found = check_averages(weekly(3, [9, 8, 8, 8, 8]), "DE")
    assert rules(found) == [("AVERAGING_NOT_ASSESSED", "info")] and len(found) == 3


def test_days_of_8_hours_or_less_and_over_10_hours_are_not_averaged():
    assert check_averages(weekly(26, [8] * 5), "DE") == []
    assert check_averages(weekly(26, [11] * 5), "DE") == []  # DAILY_OVER_10 handles these


def test_a_window_only_has_to_exist_once_for_the_day_to_pass():
    # six weeks of 10 h days, then 20 weeks of 4 h days: the 24-week window around the busy
    # weeks averages (6*50 + 18*20) / (24*6) = 4.6 h, well under 8
    roster = weekly(6, [10] * 5) + weekly(20, [4] * 5, start="2026-02-16")
    assert check_averages(roster, "DE") == []


def test_a_nine_hour_day_is_balanced_when_the_week_stays_under_the_limit():
    # a free Saturday still counts as a working day with 0 h; 41 h over 6 working days is 6.8 h
    roster = weekly(26, [9, 8, 8, 8, 8])  # 41 h over 6 working days
    assert check_averages(roster, "DE") == []


def test_night_workers_use_a_four_week_period():
    nights = weekly(8, [10] * 5, name="nina", clock="20:00")  # 20:00-06:00
    assert rules(check_averages(nights, "BE", {"nina"})) == [("NIGHT_DAILY_AVERAGE_NOT_MET", "violation")]
    assert rules(check_averages(nights, "BE", set())) == [("AVERAGING_NOT_ASSESSED", "info")]


def test_nine_hour_nights_in_a_five_day_week_pass_the_four_week_average():
    nights = weekly(8, [9] * 5, name="nina", clock="21:00")  # 45 h over 6 working days: 7.5 h
    assert check_averages(nights, "BE", {"nina"}) == []


def test_nothing_to_check_without_shifts():
    assert check_averages([]) == []
