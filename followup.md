# Follow-ups

## Morning startup: force full refresh at most once per day

### Problem
`is_morning_startup()` in `src/services/run_policy.py:12` returns `True` for every run where `now.hour == quiet_hours_end and now.minute < 30`. With the default 5-minute systemd timer (`deploy/dashboard.timer`), this triggers up to 6 full refreshes per morning (06:00/05/10/15/20/25). Each one:
- flashes the eInk panel,
- bypasses the `image_changed` suppression in `OutputService.publish()` (`src/services/output.py:96`),
- shortens panel lifespan.

The name implies "first run after quiet hours"; the implementation is "any run in the first 30 minutes".

### Proposed design

**New state file**: `state/morning_refresh_state.json`
```json
{"last_refresh_date": "2026-04-23"}
```

**`src/services/run_policy.py`** — split the window check from the "already done today" check:
```python
def is_morning_startup_window(now: datetime, quiet_hours_end: int) -> bool:
    return now.hour == quiet_hours_end and now.minute < 30

def should_force_full_refresh(now, quiet_hours_end, force_full_refresh_flag, state_dir) -> bool:
    if force_full_refresh_flag:
        return True
    if not is_morning_startup_window(now, quiet_hours_end):
        return False
    return _load_last_morning_refresh(state_dir) != now.date()

def record_morning_refresh(now, state_dir) -> None: ...
```

**`src/app.py`** — pass `cfg.state_dir` into `should_force_full_refresh()`. After a successful `publish()` where `force_full` fired via the morning path (not `--force-full-refresh`), call `record_morning_refresh(now, cfg.state_dir)`.

### Semantics
- **Late boot** (e.g. Pi powers on at 06:12): marker absent → force-full fires → marker written → subsequent ticks skip. Same slack as today.
- **Write failure**: silently re-force-full on next tick. Self-healing.
- **Read failure / missing file / malformed JSON**: treat as "never" → force-full (correct on first boot).
- **`--force-full-refresh` CLI**: stays stateless, does not update the marker.
- **DST**: date-based marker de-dupes correctly across "fall back" (06:00 occurs twice on same date); "spring forward" unaffected since 06:00 still exists.

### Tests
- `tests/test_run_policy.py` — add: marker absent → True; marker == today → False; marker == yesterday → True; `--force-full-refresh` wins regardless of marker.
- New test for `record_morning_refresh` write path (including OSError branch).
- Existing `tests/test_main_entry.py::TestMainLiveDataPath` fixture patches `src.app.should_force_full_refresh` at the import site — no changes needed.

### Not included
- No config knob to tune/disable the window. Keep the existing behavior, just fix the "6 refreshes instead of 1" bug.
- No migration — new file, nothing to move from `output/`.

### CLAUDE.md updates
- Update the "Morning startup" gotcha to reflect the new once-per-day semantics.
- Add `morning_refresh_state.json` to the state files inventory in the Gotchas section.
