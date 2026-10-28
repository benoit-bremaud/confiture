# ADR-0002 — Restrict child access per satellite, with phone unlock and night schedule

- **Status**: accepted
- **Date**: 2026-10-27
- **Deciders**: owner
- **Resolves**: Q1 of [`voice-assistant-needs.md`](../specs/voice-assistant-needs.md)

## Context

REQ-3 gives children a restricted profile, but speaker recognition (REQ-4) is deferred: the
assistant cannot tell who speaks. A rule is needed for the meantime.

## Decision drivers (weights /100)

Child protection 30 · adult convenience 25 · implementation simplicity 20 ·
forward compatibility with REQ-4 15 · learning value 10.

## Options considered (MCDA, totals /500)

| Option | Total |
|---|---|
| A — Restricted by default, adult unlock from phone | 375 |
| B — Restriction per satellite only | 355 |
| C — Full rights, spoken PIN for sensitive actions | 320 |
| D — No restriction until REQ-4 | eliminated (child protection 0) |
| E — A + B: children's room satellite always restricted | 375 |
| **F — E + night schedule (adult mode while children sleep)** | **405** |

Sensitivity: with child protection weighted 60, E leads (393 vs 381); with convenience
weighted 50, F still leads. Spoken PINs are rejected everywhere (overheard and repeated).

## Decision outcome

**F**:

- Each satellite has a **profile policy**: `always-restricted` (children's room) or
  `restricted-by-default` (shared rooms).
- On a `restricted-by-default` satellite, an adult switches to adult mode from the Home
  Assistant mobile app (device unlock required); adult mode **expires automatically**
  (initial value 15 min, to tune).
- A schedule switches `restricted-by-default` satellites to adult mode while children sleep
  (initial window 21:00–07:00, to tune).
- When REQ-4 lands, speaker recognition replaces the phone unlock; the policy model stays.

## Consequences

- The brain must know, per request, which satellite it came from and the current mode.
- Mode switching and schedules live in Home Assistant (reuse, REQ-8).
- Fallback: E (375) — disable the schedule; no design change.
