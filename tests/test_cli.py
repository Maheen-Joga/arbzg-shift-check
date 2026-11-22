import json
from pathlib import Path

import pytest

from arbzg_check.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
OK, VIOLATIONS = str(EXAMPLES / "roster_ok.csv"), str(EXAMPLES / "roster_violations.csv")


def test_clean_roster_exits_zero(capsys):
    assert main([OK]) == 0
    out = capsys.readouterr().out
    assert "10 shifts, 2 employees" in out and "0 violations, 0 warnings" in out and "not legal advice" in out


def test_violations_exit_one_and_are_listed(capsys):
    assert main([VIOLATIONS]) == 1
    out = capsys.readouterr().out
    assert "VIOLATION  REST_UNDER_11H  [ArbZG §5 Abs. 1] (row 6)" in out
    assert "7 violations, 2 warnings (3 info hidden, use --show-info)" in out
    assert "DAILY_OVER_8" not in out


def test_show_info_prints_everything(capsys):
    main([VIOLATIONS, "--show-info"])
    out = capsys.readouterr().out
    assert "DAILY_OVER_8" in out and "7 violations, 2 warnings, 3 info" in out


def test_json_output_has_a_summary_and_findings(capsys):
    assert main([VIOLATIONS, "--format", "json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["shifts"] == 8 and data["employees"] == 6
    assert data["summary"] == {"violation": 7, "warning": 2, "info": 3}
    first = data["findings"][0]
    assert set(first) == {"rule", "section", "severity", "employee", "when", "row", "message"}


@pytest.fixture
def sunday_only(tmp_path):
    f = tmp_path / "r.csv"
    f.write_text("employee,date,start,end,breaks\nanna,2026-03-15,08:00,16:30,12:00-12:30\n")
    return str(f)


def test_fail_on_warning_makes_warnings_fail_the_run(sunday_only, capsys):
    assert main([sunday_only]) == 0
    assert main([sunday_only, "--fail-on", "warning"]) == 1


def test_sector_and_night_worker_options_are_passed_on(tmp_path, capsys):
    f = tmp_path / "r.csv"
    f.write_text("employee,date,start,end,breaks\n"
                 "a,2026-03-02,14:00,22:00,18:00-18:30\n"
                 "a,2026-03-03,08:30,16:30,12:00-12:30\n"
                 "a,2026-03-05,08:30,16:30,12:00-12:30\n")
    assert main([str(f)]) == 1
    assert main([str(f), "--sector", "hospitality"]) == 0
    main([str(f), "--night-worker", "a", "--show-info"])
    assert "NIGHT_WORKER" in capsys.readouterr().out


def test_missing_file_exits_two(capsys):
    assert main(["/nonexistent/roster.csv"]) == 2
    assert "cannot read" in capsys.readouterr().err


def test_invalid_roster_exits_two_and_lists_every_problem(tmp_path, capsys):
    f = tmp_path / "bad.csv"
    f.write_text("employee,date,start,end\nanna,2026-03-02,6am,14:00\nben,nope,06:00,14:00\n")
    assert main([str(f)]) == 2
    err = capsys.readouterr().err
    assert "line 2:" in err and "line 3:" in err


def test_bad_option_value_exits_two(capsys):
    assert main([OK, "--sunday-offset", "9"]) == 2
    assert "between -6 and 6" in capsys.readouterr().err


def test_unknown_sector_is_rejected_by_the_parser():
    with pytest.raises(SystemExit) as e:
        main([OK, "--sector", "warehouse"])
    assert e.value.code == 2


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    assert "arbzg-check 0.1.0" in capsys.readouterr().out
