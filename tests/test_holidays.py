from datetime import date

import pytest

from arbzg_check.holidays import easter, holiday_name, holidays


@pytest.mark.parametrize("year, expected", [
    (2000, date(2000, 4, 23)), (2019, date(2019, 4, 21)), (2024, date(2024, 3, 31)),
    (2025, date(2025, 4, 20)), (2026, date(2026, 4, 5)), (2038, date(2038, 4, 25)),
])
def test_easter_sunday(year, expected):
    assert easter(year) == expected


def test_berlin_2026():
    h = holidays(2026, "BE")
    assert len(h) == 10
    assert h[date(2026, 4, 3)] == "Karfreitag" and h[date(2026, 4, 6)] == "Ostermontag"
    assert h[date(2026, 5, 14)] == "Christi Himmelfahrt" and h[date(2026, 5, 25)] == "Pfingstmontag"
    assert date(2026, 3, 8) in h  # International Women's Day, a Sunday in 2026


def test_berlin_one_off_holidays():
    assert date(2025, 5, 8) in holidays(2025, "BE") and len(holidays(2025, "BE")) == 11
    assert date(2020, 5, 8) in holidays(2020, "BE")
    assert date(2028, 6, 18) in holidays(2028, "BE")
    assert date(2026, 5, 8) not in holidays(2026, "BE")


def test_womens_day_starts_in_2019():
    assert date(2018, 3, 8) not in holidays(2018, "BE")
    assert date(2019, 3, 8) in holidays(2019, "BE")


def test_national_list_has_no_berlin_extras():
    h = holidays(2025, "DE")
    assert len(h) == 9 and date(2025, 3, 8) not in h and date(2025, 5, 8) not in h


def test_holiday_name_and_unknown_region():
    assert holiday_name(date(2026, 10, 3)) == "Tag der Deutschen Einheit"
    assert holiday_name(date(2026, 10, 4)) is None
    with pytest.raises(ValueError, match="unknown region"):
        holidays(2026, "BY")
