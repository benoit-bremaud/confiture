# ADR-0001 — Allow internet for online services, keep voice local

- **Status**: accepted
- **Date**: 2026-10-27
- **Deciders**: owner

## Context

The household wants the weather (UC10), music (UC11) and answers to general questions (UC1).
A strictly offline assistant cannot provide forecasts or streaming, and general answers would
depend only on a local LLM. Privacy remains the main reason to build confiture instead of
buying a commercial assistant.

## Decision drivers

- Useful features (weather, music, general knowledge).
- Privacy: household voices must not leave the home.
- Recycled, low-power hardware (NFR-4).

## Options considered

- **A — Fully offline**: no internet at all.
- **B — Internet for online services, voice local**: speech-to-text, intent handling and
  text-to-speech run at home; only minimal, intent-level queries go out.
- **C — Cloud voice pipeline**: send audio to a cloud speech service.

## Decision outcome

**B**, chosen by the owner: it unlocks UC10 and UC11 while keeping NFR-1 (no audio and no full
transcript leaves the home network). C is rejected because it breaks the project's privacy
promise; A is rejected because it cannot deliver UC10 and UC11.

## Consequences

- Every online call sends only what the service needs (place and date, track name…).
- The brain needs outbound internet access; satellites and sensor nodes do not.
- The data-flow diagram (phase 1) must show each outbound flow and its fields.
