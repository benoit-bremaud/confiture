# confiture — architecture

## Method

UML-first, proportional: use cases (phase 0) are validated before any realisation diagram
(sequence, component, deployment), and before any code. Decisions go to `decisions/` (MADR).

## Scope and goals

A fully local personal voice assistant for the home, built on recycled Raspberry Pis
(see [specs](specs/voice-assistant-use-cases.md) for NFR-1 to NFR-4).

## Stakeholders

- Household member — talks to the assistant.
- Maintainer — sets up and runs the system (today: the owner).

## How to read this folder

1. [`diagrams/voice-assistant/01-use-case.md`](diagrams/voice-assistant/01-use-case.md) — who wants what.
2. [`specs/voice-assistant-use-cases.md`](specs/voice-assistant-use-cases.md) — use case texts and NFRs.
3. [`glossary.md`](glossary.md) and [`traceability-matrix.md`](traceability-matrix.md).
4. Next phase (after validation): sequence of the wake → answer flow, component and deployment diagrams.
