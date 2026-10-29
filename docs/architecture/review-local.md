# Local review — confiture (branch feat/3-pan-tilt-mqtt-agent)

- Date: 2026-10-29
- Commit: ade7a67
- Scope: branch diff origin/main...HEAD (pi3cam/, docs/architecture/)
- Checks run: design · docs · tests · security · correctness
- Verdict: Must and Should fixed; ship  ·  Must 5 · Should 6 · Nice 5

## Pre-merge gate (after fixes, working tree on top of ade7a67)
| Step | Result |
|---|---|
| 1 Tests | ✅ 67 unit (pytest, 0.1 s); no integration/E2E suite (hardware agent) |
| 2 Coverage | tests 91 % lines+branches overall; domain.py 99 %, adapters.py 95 %; SonarQube new code 98.5 % (main.py wiring excluded) · docs 28/28 public symbols (100 %; Protocol and adapter methods documented at class level, nested closures excluded) |
| 3 SonarQube | ✅ PASSED (S1192 fixed with topic constants) |
| 4 Secrets | ✅ gitleaks clean (origin/main..HEAD + staged) · no tracked .env · diff read: no IP, MAC, name or key |
| 5 QA pass | ✅ hardware smoke on the Pi 3, 2026-10-29: new agent deployed (prototype backed up), 19/19 MQTT checks — online, light and HD images, pan/tilt to both limits, 500 clamped to 100, `inf` and invalid UTF-8 ignored with the agent alive, save / go to / delete a preset, privacy OFF blanks the image and ON restores it, recentre; no error in the agent log |
- Gate: **GREEN once the PR reviews are handled**

## Resolution
All Must and Should items below are fixed in the follow-up commit, except where marked Nice or Disagree.

## 🔴 Must Have
- `pi3cam/domain.py` `handle` `[security|correctness]` · `inf` in pan/tilt raises OverflowError on the paho thread, killing command handling while the process lives on · parse with `math.isfinite`, catch `(ValueError, OverflowError)`.
- `pi3cam/main.py` `on_message` `[security|correctness]` · invalid UTF-8 payload raises in the paho callback, same effect · `decode(errors="replace")` and log-and-continue around the handler.
- `pi3cam/adapters.py` `JsonStore` `[design|correctness]` · non-atomic writes from two threads; a corrupt `state.json` makes `Agent.__init__` crash at every restart · temp file + `os.replace`, corrupt file loads as `None`, test it.
- `pi3cam/domain.py` Protocols, adapters `[docs]` · public contract undocumented (b"" on capture failure, `None` on missing store, PCA9685 50 Hz precondition, rpicam flags) · add docstrings; reach the 90 % doc floor.
- `pi3cam/domain.py` `[tests|sonar]` · S1192 and servo-safety gaps: no move from a non-centre position, clamp checked on one axis/end only · topic constants; parametrised tests.

## 🟡 Should Have
- `pi3cam/domain.py` `Agent` `[design|correctness]` · shared `presets`/`state` mutated from paho, mover and report threads without a lock (dict-changed-size during iteration) · one `RLock`, snapshot before publishing.
- `pi3cam/domain.py` delete branch `[correctness]` · the default position can be deleted by a crafted payload · guard `selected != DEFAULT`.
- `pi3cam/domain.py` `Agent.__init__` `[correctness]` · stored data not validated; mover thread dies on bad data · validate on load, log-and-continue in mover.
- `pi3cam/main.py` capture loop `[design|correctness]` · `main` reaches into `shoot_now` · `Agent.wait_for_shot` (a set between wait and clear is still served by the next shot, so no image is lost).
- `pi3cam/tests/test_domain.py` `[tests]` · weak asserts (privacy reject, truncation, preset republish, retain flags, rpicam arg positions) · tighten.
- `docs/architecture/diagrams/pan-tilt-camera/01-sequence-aim-and-look.md` `[docs]` · privacy branch omits the blanked `camera_hd` · add it.

## 🔵 Nice to Have
- `pi3cam/domain.py` `[design]` · Discovery payloads share the safety file (divergent change) · move to `discovery.py` later.
- `pi3cam/domain.py` `[design]` · `AXES` nested dicts → frozen dataclass.
- `pi3cam/domain.py` `[design]` · `DELETE_PREFIX` repeats `TRASH`; name the 0.5 s pause · done.
- `pi3cam/domain.py` `[security]` · unbounded move queue and preset count · cap presets.
- `pi3cam/adapters.py` `[security]` · files rely on cron's umask · done: `os.umask(0o077)` in `main`, `mkstemp` writes mode 600.

## ⚪ Disagree / Intentional
- `pi3cam/adapters.py` `MqttBus` `[design]` · flagged as Middle Man; kept: it pins `retain` as keyword and keeps paho's `qos`-third signature out of the domain contract (ADR-0007).
- Four Protocols with one adapter each · testability seams, ADR-0007 option A.

## Per-dimension summary
- Design: dependency rule holds; store atomicity and locking to fix · Docs: contracts missing, docs match code · Tests: lean and fast, critical servo paths need two more cases · Security: two crash-the-thread inputs, no injection, no personal data · Correctness: races and corrupt-file crash loop.
