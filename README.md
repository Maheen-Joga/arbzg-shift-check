# arbzg-check

[![tests](https://github.com/Maheen-Joga/arbzg-shift-check/actions/workflows/tests.yml/badge.svg)](https://github.com/Maheen-Joga/arbzg-shift-check/actions/workflows/tests.yml)

Check a shift roster against the German Working Hours Act ([ArbZG](https://www.gesetze-im-internet.de/arbzg/)).
Give it a CSV of who works when, and it reports daily hours over the limit, missing breaks, rest periods
under 11 hours, Sunday and holiday work, and night-work averages, each with the section it comes from.

Standard library only, Python 3.10 or newer. It is a screening tool, **not legal advice**: collective
agreements, works agreements and permits can change what is allowed. See [what it does not cover](#limits).

```bash
pip install .
arbzg-check examples/roster_violations.csv
```

```text
8 shifts, 6 employees
2026-03-02  chris  VIOLATION  DAILY_OVER_10  [ArbZG §3]
    11:00 h of work on one day; the limit is 10 h even with averaging
2026-03-02  dana  VIOLATION  WORK_STRETCH_OVER_6H  [ArbZG §4 Satz 3] (row 3)
    7:00 h of work in a row without a break; the limit is 6 h
2026-03-03  fatima  VIOLATION  REST_UNDER_11H  [ArbZG §5 Abs. 1] (row 6)
    rest of 8:00 h after the shift ending 2026-03-02 22:00; the minimum is 11 h (3:00 h short of 11 h)
2026-03-08  gabor  warning  SUNDAY_WORK  [ArbZG §9 Abs. 1] (row 8)
    8:30 h of work on Sunday (Internationaler Frauentag) 2026-03-08; lawful only with an exemption (§10, §13 to §15) or a permit
7 violations, 2 warnings (3 info hidden, use --show-info)
```

(The full output also lists the other findings; four are shown here.) The exit status is 0 when there are
no violations, 1 when there are, and 2 when the roster file cannot be read. That makes it usable in a
pipeline that exports rosters.

## What it checks

| Section | Rule |
|---|---|
| §3 | At most 10 h a day, and a day over 8 h needs a 24-week average of 8 h per working day |
| §4 | 30 min of break above 6 h of work, 45 min above 9 h, blocks of at least 15 min, never more than 6 h in a row |
| §5 | 11 h of rest between shifts; the five sectors in Abs. 2 may cut it to 10 h with compensation |
| §6, §2 | Night work and night workers, with a 4-week average |
| §9, §11 | Sunday and holiday work, a substitute rest day, 15 free Sundays a year |

Every rule identifier, its severity and the interpretation chosen are in [docs/RULES.md](docs/RULES.md).

## Roster format

```csv
employee,date,start,end,breaks
anna,2026-03-02,06:00,14:30,10:00-10:30
ben,2026-03-02,22:00,06:00,01:00-01:30
```

`date` is `2026-03-02` or `02.03.2026`. An `end` at or before `start` means the shift ends the next day.
`breaks` are `HH:MM-HH:MM`, several separated by `|`. If only a total is known, use a `break_min` column
instead; the break is then placed mid-shift and the 6-hour rule cannot be checked. A semicolon delimiter is
detected automatically, so German spreadsheet exports work. A bad file is reported with every faulty row:

```text
error: bad.csv is not a valid roster
  line 2: time '6am' is not HH:MM
  line 3: date 'nope' is not YYYY-MM-DD or DD.MM.YYYY
```

## Options

| Option | Effect |
|---|---|
| `--sector healthcare\|hospitality\|transport\|broadcasting\|agriculture` | allow the 10 h rest with compensation (§5 Abs. 2) |
| `--region BE\|DE` | public holidays: Berlin (default) or national only |
| `--sunday-offset HOURS` | move the Sunday rest window by up to 6 h (§9 Abs. 2) |
| `--year 2026` | also check for 15 work-free Sundays in that year |
| `--night-worker NAME` | treat a person as a night worker; repeatable |
| `--format json` | machine-readable output |
| `--show-info`, `--fail-on warning` | print informational findings; fail on warnings too |

## As a library

```python
from arbzg_check import Options, check, load

findings = check(load("roster.csv"), Options(region="BE"))
for f in findings:
    print(f.severity, f.rule, f.employee, f.when, f.message)
```

## Design

- **Findings, not booleans.** Every result names the rule, the section, the person, the time and the
  source row, so a planner can fix the roster without reading the law.
- **Three severities.** Work on a Sunday is lawful with an exemption the roster cannot show, so it is a
  warning, not a violation. A roster too short to judge an averaging period gives an info, never a false alarm.
- **No data files.** Public holidays are computed from the date of Easter; the tests pin Easter for six
  years and the holiday counts for Berlin in 2025 and 2026.
- **Interpretations are written down.** Where the statute is open to reading, the choice is in
  [docs/RULES.md](docs/RULES.md) and covered by a test, so it can be argued with.

## Limits

Not covered: young workers (JArbSchG), pregnant and nursing employees (MuSchG), collective and works
agreements under §7, exemptions and permits under §§10 and 13 to 15, managers excluded by §18, on-call
duty, holidays outside Berlin and the national list, and daylight-saving changes. Times are naive local
times. The examples are invented. I am not a lawyer; check anything that matters with the works council
or an employment lawyer.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
