# arbzg-check

Check shift rosters against the German Working Hours Act ([ArbZG](https://www.gesetze-im-internet.de/arbzg/)).
A screening tool, not legal advice. Standard library only.

**Status: early development.** Built in small steps; checked items exist and are tested.

- [x] Daily working time and breaks (ArbZG §3, §4)
- [x] Rest period between shifts (§5), with the sector exception
- [x] CSV roster loader with row-level error messages
- [x] Sundays and public holidays (§9, §11), Berlin holidays computed from Easter
- [ ] Night work and averaging periods (§3, §6)
- [ ] Command-line tool, rules reference and final README

```python
from arbzg_check import check, load
findings = check(load("roster.csv"))
```

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
