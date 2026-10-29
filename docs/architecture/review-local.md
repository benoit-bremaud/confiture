# Local review — confiture (feat/8-tsl25911-illuminance-sensor)

Pre-push review of issue #8, the TSL25911 illuminance sensor; all Must and Should findings were fixed on the branch.

- Date: 2026-10-29
- Commit: see the PR head (review run on c95672b, fixes in the next commit)
- Scope: branch diff main...HEAD
- Checks run: design · docs · tests · security · correctness
- Verdict: ship (after fixes) · Must 1 (fixed) · Should 9 (fixed) · Nice 4

## Pre-merge gate (head SHA of the fix commit)

| Step | Result |
|---|---|
| 1 Tests | ✅ 94 unit (pytest), ruff check and format clean |
| 2 Coverage | tests 100 % `domain.py`, 97 % `adapters.py` (branch coverage on; `main.py` excluded as wiring) · new public API docs 100 % after the fix (floor 90) |
| 3 SonarQube | ✅ PASSED |
| 4 Secrets | ✅ gitleaks clean on main..HEAD and the working tree · no tracked .env (only `.env.example`) · diff read: no IP, MAC, user or family name |
| 5 QA pass | ✅ hardware check on the Pi 3: Discovery config and states on the broker; same scene 30.7 lx at 25×, 31.1 lx at 428×; agent restarted cleanly, no errors in its log |

- Gate: **GREEN for push** (merge waits for CI, Codex review and owner approval)

## 🔴 Must Have

- `pi3cam/adapters.py` `Tsl2591Sensor.read` `[docs]` · no docstring for its contract (counts or None, blocking time) · fixed.

## 🟡 Should Have

- `pi3cam/adapters.py` `Tsl2591Sensor.__init__` `[security|correctness]` · the power-on write at construction could raise and stop the whole camera agent when the sensor is missing · fixed: no I²C access at construction, power-on at the first read.
- `pi3cam/adapters.py` `read` `[correctness]` · after a brown-out the sensor stays off and reports zeros · fixed: power-on rewritten after every I²C error.
- `pi3cam/adapters.py` `TSL_GAIN_BITS` `[design]` · unused 9876× entry · removed.
- `pi3cam/domain.py` / `adapters.py` `[design]` · integration time split across files · cross-reference comments added.
- `01-sequence-aim-and-look.md` `[docs]` · loop drawn on the Agent, not LightMeter; no-publish branch missing · fixed.
- `pi3cam/README.md` `[docs]` · 88 000 lx limit unsourced · now cited as the datasheet range.
- `pi3cam/tests/test_light.py` `[tests]` · IR high byte zero, no threshold boundaries, formula rebuilt in the test, payload rounding unchecked, failure mid-ranging untested · all fixed.

## 🔵 Nice to Have

- `pi3cam/domain.py` `lux` `[correctness]` · a strong infrared source reads as 0 lx; returning None would hold the last value · left as is (rare indoors; follow-up if seen).
- `pi3cam/domain.py` `SATURATED` `[correctness]` · 36863 vs 37888 at 100 ms · conservative, drops the gain slightly early; kept.
- `pi3cam/adapters.py` gains `[docs]` · 25/428 are the reference library's values, datasheet typicals are 24.5/400 · within the sensor's accuracy; kept.
- `pi3cam/main.py` `[design]` · a second `MqttBus` instance · stateless, harmless; kept.

## ⚪ Disagree / Intentional

- `pi3cam/domain.py` `[design]` · chip constants (LUX_DF, SATURATED) in the domain · pure arithmetic, no I/O; layering proportional (project CLAUDE.md).

## Per-dimension summary

- Design: no over-engineering, dependency rule held · Docs: one missing docstring, two stale docs, fixed · Tests: trustworthy, strengthened · Security: no secrets or personal data; boot-robustness fixed · Correctness: register map and lux equation match the datasheet.
