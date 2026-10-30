# Local review — confiture (feat/25-llm-thinking-cue-fallback)

Pre-push review of issue #25, thinking cue and friendly fallback in `nest-relay`; every Must and Should finding was fixed on the branch in the commit after the review.

- Date: 2026-10-30
- Commit: 08fe384 (review run), fixes in the next commit
- Scope: branch diff main...HEAD (`deploy/pi5/nest-relay/{relay,main}.py`, tests, `05-sequence-thinking-cue-and-fallback.md`, `02-sequence-ask-a-question.md`, `PROJECT_LOG.md`)
- Checks run: design · docs · tests · security · correctness (containers: Dockerfile and compose untouched, `docker-auditor` skipped)
- Verdict: ship after the fixes · Must 2 · Should 6 · Nice 3

## Pre-merge gate (head SHA of the fix commit)

| Step | Result |
|---|---|
| 1 Tests | ✅ nest-relay 18 unit + 2 `speak_all` · pi3cam 101 · sttbench 13 |
| 2 Coverage | `relay.py` 100 % (`main.py` wiring excluded in `sonar-project.properties`, `speak_all` tested) · docs: every public function and class has a docstring |
| 3 SonarQube | ✅ PASSED (new coverage 99.3 %, 0 new violations, 0 % duplication) |
| 4 Secrets | ✅ gitleaks clean (full history) · no tracked .env · diff read: placeholders only |
| 5 QA pass | ✅ spoken on the Pi 5 by the owner: "quelle heure est-il ?" local, no cue · free question cue at 2.0 s, answer at 11.9 s · Ollama stopped: fallback in 0.1 s |

- Gate: **GREEN** once the fix commit is redeployed and re-spoken (owner approval)

## 🔴 Must Have

- `deploy/pi5/nest-relay/relay.py:65` `[design|correctness]` · the "closed" latch dropped every reply until the next `thinking` · fixed: the latch drops only the one late reply, `pipeline_error` does not latch (the run ended), `idle` clears the turn; 3 tests.
- `deploy/pi5/nest-relay/main.py:43` `[tests]` · `speak_all` HA-failure path untested after `relay()` was removed · fixed: `tests/test_main.py`, and any other speaker exception is logged instead of stopping the relay.

## 🟡 Should Have

- `deploy/pi5/nest-relay/main.py:54` `[design]` · one `Turn` shared across reconnects spoke a stale fallback · fixed: new `Turn` per connection.
- `deploy/pi5/nest-relay/relay.py:40` `[design|tests]` · `reply_text` dead code and its tests · fixed: removed, parsing tested on `parse_event`.
- `deploy/pi5/nest-relay/tests/test_relay.py:58` `[tests]` · cue then fallback sequence not asserted · fixed, plus late tick, error after cue, second `thinking`.
- `deploy/pi5/nest-relay/relay.py:1` `[docs]` · module docstring stale · fixed.
- `docs/architecture/diagrams/voice-assistant/05-sequence-thinking-cue-and-fallback.md` `[docs]` · source of the `thinking` event, HA-down case, blocking speak · fixed in Notes (LVA 1.1.18 `peripheral_api.LVAEvent`; `yuki_speak` is `mode: queued`, checked in `config/homeassistant/yuki_speak.yaml`).
- `deploy/pi5/nest-relay/main.py:62` `[correctness]` · speaking blocks the loop up to 10 s · intentional (cue before reply), documented in `speak_all` and diagram 05.

## 🔵 Nice to Have

- `deploy/pi5/nest-relay/relay.py:36` `[design]` · strip expression precedence hard to read · fixed.
- `deploy/pi5/nest-relay/main.py:40` `[correctness]` · polling every 0.25 s instead of a computed deadline · kept (KISS).
- `deploy/pi5/nest-relay/main.py` `[security]` · reply length not capped before HA · not done; text comes from the local satellite.

## ⚪ Disagree / Intentional

- `deploy/pi5/nest-relay/relay.py` `[design]` · no State pattern for `Turn` · three fields, no present force (design-patterns gate).

## Per-dimension summary

- Design: pure state machine, one latch defect fixed · Docs: diagram 05 matches the code · Tests: pyramid of fast unit tests, wiring helper now tested · Security: no secret, text logged as length only, JSON body to a fixed URL · Correctness: `wait_for(ws.recv())` cancel-safe in websockets 17.3, `TimeoutError` right on Python 3.13.
