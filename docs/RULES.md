# Rules reference

Every rule has a stable identifier, the section it comes from, and a severity.

* **violation**: the roster breaks the rule as written.
* **warning**: lawful only with something the roster cannot show (an exemption or a permit).
* **info**: worth knowing, or the roster is too short to judge.

Statute text: [Arbeitszeitgesetz](https://www.gesetze-im-internet.de/arbzg/). Where the statute leaves
room for interpretation, the choice made here is written down next to the rule.

## Daily working time (section 3)

| Rule | Severity | Meaning |
|---|---|---|
| `DAILY_OVER_10` | violation | More than 10 h of work on one day. |
| `DAILY_OVER_8` | info | More than 8 h, up to 10 h. Allowed only if the average stays at 8 h per working day over 24 weeks; see the two average rules below. |

Working time is the time on the clock minus breaks of at least 15 minutes. A shift counts on the day
it starts, so a night shift from 22:00 to 06:00 is 8 h on the first day. Several shifts on one day
are added together.

## Breaks (section 4)

| Rule | Severity | Meaning |
|---|---|---|
| `BREAK_TOO_SHORT` | violation | More than 6 h of work needs 30 min of break; more than 9 h needs 45 min. |
| `WORK_STRETCH_OVER_6H` | violation | More than 6 h of work in a row without a break. |
| `BREAK_SEGMENT_UNDER_15` | warning | A pause shorter than 15 min does not count as a break. |
| `BREAK_POSITION_UNKNOWN` | info | Only a total (`break_min`) was given, so the 6 h stretch rule was not checked. |

Breaks may be split into blocks of at least 15 minutes. The break time needed depends on the work
time after breaks, so 9 h 30 min on the clock with a 30 min break is 9 h of work and needs 30 min.

## Rest period (section 5)

| Rule | Severity | Meaning |
|---|---|---|
| `REST_UNDER_11H` | violation | Less than 11 h between the end of one shift and the start of the next. With `--sector`, less than 10 h. |
| `REST_REDUCED` | info | A sector cut the rest to 10 h to 11 h and it is offset. |
| `REST_REDUCTION_NOT_COMPENSATED` | violation | A sector cut the rest and no later rest of 12 h or more starts within four weeks. |

Only the sectors named in section 5 Abs. 2 can cut the rest: `healthcare`, `hospitality`, `transport`,
`broadcasting`, `agriculture`. Each compensating rest is used for one cut only. Cuts of up to two
hours under a collective agreement (section 7) are not modelled.

## Sundays and public holidays (sections 9 and 11)

| Rule | Severity | Meaning |
|---|---|---|
| `SUNDAY_WORK` | warning | Work between 00:00 and 24:00 on a Sunday. |
| `HOLIDAY_WORK` | warning | The same on a public holiday. |
| `SUBSTITUTE_REST_MISSING` | violation | No work-free day within 14 days after Sunday work, or within 56 days after weekday holiday work. |
| `SUBSTITUTE_REST_NOT_ASSESSED` | info | The roster ends before that window does. |
| `FREE_SUNDAYS_UNDER_15` | violation | Fewer than 15 work-free Sundays in the year given with `--year`. |

Choices made here: the window for a substitute day counts the worked day as day 1 and looks forward only;
any day without work counts, and the roster must reach the end of the window or the check is skipped.
For `--year` the roster must cover the whole calendar year; days with no entry count as work-free.
`--sunday-offset` moves the 24 h window by up to 6 h in either direction (section 9 Abs. 2); that is
lawful only in plants that stand idle for the following 24 h, which the tool cannot check.

Public holidays are computed for Germany (`DE`) and Berlin (`BE`, the default), including Berlin's
Women's Day from 2019 and the one-off days on 8 May 2020, 8 May 2025 and 18 June 2028.

## Night work (sections 2 and 6) and averaging

| Rule | Severity | Meaning |
|---|---|---|
| `NIGHT_WORKER` | info | The person is treated as a night worker: named with `--night-worker`, or at least 48 days of night work in a calendar year. |
| `DAILY_AVERAGE_NOT_MET` | violation | A day over 8 h and no 24-week window containing it averages 8 h per working day. |
| `NIGHT_DAILY_AVERAGE_NOT_MET` | violation | The same for a night worker on a night-work day, with a 4-week window. |
| `AVERAGING_NOT_ASSESSED` | info | The roster is shorter than the reference period. |

Night time is 23:00 to 06:00; night work is a shift with more than two hours in that time. A working
day (Werktag) is any day except Sundays and public holidays, so a free Saturday counts as a day with
0 h. Hours worked on Sundays and holidays are added to the total but not to the day count, which is
the cautious reading. A day over 8 h passes if at least one window that contains it and lies fully
inside the roster averages 8 h or less. Rotating night shifts cannot be seen in a roster, so those
people need `--night-worker`.

## Not covered

Young workers (Jugendarbeitsschutzgesetz), pregnant and nursing employees (Mutterschutzgesetz),
collective agreements and works agreements under section 7, exemptions and permits under sections 10
and 13 to 15, managers excluded by section 18, on-call duty, public holidays outside Berlin and the
national list, and daylight-saving changes (a shift across the clock change is off by one hour).
