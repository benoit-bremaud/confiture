# ADR-0005 — Keep the LLM local

- **Status**: accepted (owner, 2026-10-28)
- **Date**: 2026-10-28
- **Deciders**: owner
- **Resolves**: Q6 of [`voice-assistant-needs.md`](../specs/voice-assistant-needs.md)

## Context

Requests no intent matches go to an LLM (REQ-2). NFR-1 forbids sending audio or a full
transcript outside the home; ADR-0001 allows the internet only for minimal queries (weather,
music). A cloud LLM answers better and faster, but would receive the household's full
sentences, children's included. ADR-0004 gives a local host that meets NFR-5 with a 3B model.

## Decision drivers (weights /100)

Privacy (NFR-1) 40 · answer quality 25 · cost and independence from providers 20 ·
responsiveness 15.

## Options considered (MCDA, scores 0–5, totals /500)

| Criterion | **A — Local LLM only** | B — Cloud LLM (exception to ADR-0001) | C — Local by default, cloud on explicit request |
|---|---|---|---|
| Privacy (40) | 5 | 1 — every LLM sentence leaves home | 4 — only when the user asks |
| Answer quality (25) | 2 — 3B model, factual errors | 5 | 4 |
| Cost and independence (20) | 5 | 2 — subscription, API key, provider changes | 3 |
| Responsiveness (15) | 3 — 8.7 s | 5 | 4 |
| **Total** | **395** | **280** | **380** |

Sensitivity: the result flips if answer quality outweighs privacy (quality 40, privacy 25:
C 380 vs A 350). A leads only while privacy is the top driver, which matches the project's
reason to exist (ADR-0001).

## Decision outcome

**A**. The LLM runs on the brain host (ADR-0004); no transcript goes to a cloud LLM. NFR-1
stays without exception.

## Consequences

- Answer quality is bounded by local hardware; the system prompt favours short answers and
  "I don't know".
- Revisit when the GPU host arrives (larger local model), or switch to C if the household
  ranks answer quality above privacy — C would need a new ADR amending ADR-0001.
