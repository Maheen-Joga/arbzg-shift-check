import pytest

from arbzg_check import RosterFormatError, loads
from arbzg_check.loader import load

from .helpers import dt

HEADER = "employee,date,start,end,breaks,break_min\n"


def test_reads_a_simple_roster():
    shifts = loads(HEADER + "anna,2026-03-02,06:00,14:30,10:00-10:30,\n")
    s = shifts[0]
    assert (s.employee, s.start, s.end, s.line) == ("anna", dt("2026-03-02 06:00"), dt("2026-03-02 14:30"), 2)
    assert [(b.start, b.end) for b in s.breaks] == [(dt("2026-03-02 10:00"), dt("2026-03-02 10:30"))]
    assert not s.breaks_assumed


def test_semicolon_delimiter_german_dates_and_bom():
    text = "﻿Employee;Date;Start;End;Breaks\nanna;02.03.2026;06:00;14:30;10:00-10:30\n"
    assert loads(text)[0].start == dt("2026-03-02 06:00")


def test_end_before_start_means_next_day():
    s = loads(HEADER + "ben,2026-03-02,22:00,06:00,01:00-01:30,\n")[0]
    assert s.end == dt("2026-03-03 06:00")
    assert s.breaks[0].start == dt("2026-03-03 01:00")


def test_several_breaks():
    s = loads(HEADER + "anna,2026-03-02,06:00,15:00,09:00-09:15|12:00-12:30,\n")[0]
    assert len(s.breaks) == 2 and s.break_time.total_seconds() == 45 * 60


def test_no_breaks_is_allowed_and_means_none():
    assert loads("employee,date,start,end\nanna,2026-03-02,06:00,10:00\n")[0].breaks == ()


def test_break_min_places_one_assumed_break_in_the_middle():
    s = loads(HEADER + "anna,2026-03-02,06:00,14:30,,30\n")[0]
    assert s.breaks_assumed
    assert (s.breaks[0].start, s.breaks[0].end) == (dt("2026-03-02 10:00"), dt("2026-03-02 10:30"))


def test_break_min_zero_means_no_break():
    s = loads(HEADER + "anna,2026-03-02,06:00,14:30,,0\n")[0]
    assert s.breaks == () and not s.breaks_assumed


def test_blank_lines_are_skipped_and_line_numbers_stay_true():
    shifts = loads(HEADER + "\nanna,2026-03-02,06:00,14:30,,\n\nanna,2026-03-03,06:00,14:30,,\n")
    assert [s.line for s in shifts] == [3, 5]


def problems(text):
    with pytest.raises(RosterFormatError) as e:
        loads(text)
    return e.value.problems


def test_missing_column():
    assert problems("employee,date,start\nanna,2026-03-02,06:00\n") == [(1, "missing column(s): end")]


def test_every_bad_row_is_reported_with_its_line():
    found = problems(HEADER + "anna,2026-03-02,6am,14:30,,\n"
                              "ben,2026-13-40,06:00,14:30,,\n"
                              "cy,2026-03-02,06:00,14:30,10:00-10:30,30\n"
                              "dee,2026-03-02,06:00,14:30,10:00,\n"
                              ",2026-03-02,06:00,14:30,,\n")
    assert [n for n, _ in found] == [2, 3, 4, 5, 6]
    assert "not HH:MM" in found[0][1] and "not YYYY-MM-DD" in found[1][1]
    assert "either breaks or break_min" in found[2][1] and "not HH:MM-HH:MM" in found[3][1]
    assert "no employee" in found[4][1]


def test_break_outside_the_shift_is_rejected():
    assert "inside the shift" in problems(HEADER + "anna,2026-03-02,06:00,10:00,11:00-11:30,\n")[0][1]


def test_equal_start_and_end_is_rejected_not_read_as_24_hours():
    assert problems(HEADER + "anna,2026-03-02,06:00,06:00,,\n") == [(2, "start and end are the same time")]


def test_non_numeric_and_oversized_break_min():
    found = problems(HEADER + "a,2026-03-02,06:00,10:00,,half\nb,2026-03-02,06:00,10:00,,240\n")
    assert "whole number" in found[0][1] and "as long as the whole shift" in found[1][1]


def test_overlapping_shifts_are_a_roster_error():
    found = problems(HEADER + "anna,2026-03-02,06:00,14:00,,\nanna,2026-03-02,13:00,20:00,,\n")
    assert "overlap" in found[0][1] and "rows 2 and 3" in found[0][1]


def test_empty_file_and_header_only():
    assert problems("") == [(0, "the file is empty")]
    assert problems(HEADER) == [(0, "the roster has no shifts")]


def test_load_reads_a_file(tmp_path):
    f = tmp_path / "r.csv"
    f.write_text(HEADER + "anna,2026-03-02,06:00,14:30,10:00-10:30,\n", encoding="utf-8")
    assert load(f)[0].employee == "anna"
    assert load(str(f))[0].employee == "anna"
