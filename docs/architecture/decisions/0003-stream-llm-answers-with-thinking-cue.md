# ADR-0003 — Stream LLM answers with a thinking cue

- **Status**: accepted
- **Date**: 2026-10-27
- **Deciders**: owner
- **Resolves**: Q7 of [`voice-assistant-needs.md`](../specs/voice-assistant-needs.md)

## Context

Known commands answer within 3 s (NFR-2). Requests no intent matches go to an LLM (REQ-2),
which is slow on recycled hardware. The latency budget bounds the model size, hence the
assistant's intelligence.

## Decision drivers (weights /100)

Perceived responsiveness 35 · possible intelligence 30 · feasibility on recycled hardware 25 ·
learning value 10.

## Options considered (MCDA, totals /500)

| Option | Total |
|---|---|
| A — Under 5 s, no cue (tiny model) | 240 |
| **B — "Let me think" cue after 2 s, sentence-by-sentence streamed speech, full answer ≤ 15 s** | **410** |
| C — Up to 30 s, no cue (largest model) | 330 |

Sensitivity: with responsiveness weighted 70, B still leads (405 vs 326 vs 206).
Feasibility scores are estimates — to confirm with a benchmark on the real brain host.

## Decision outcome

**B**. NFR-2 is completed with **NFR-5 — LLM path**: a spoken thinking cue if no answer
starts within 2 s; speech starts as soon as the first sentence is generated; the full answer
completes within 15 s (initial values, to tune after benchmark).

## Consequences

- The brain must stream LLM tokens into text-to-speech sentence by sentence.
- Model choice (Q2/Q6) is bounded by the 15 s budget on the chosen host.
- Fallback: C (330) — drop cue and streaming; simpler, no design change.
