# ADR-0004 — Split the brain: voice pipeline on the Pi 5, LLM on the laptop

- **Status**: accepted (owner, 2026-10-28)
- **Date**: 2026-10-28
- **Deciders**: owner
- **Resolves**: Q2 of [`voice-assistant-needs.md`](../specs/voice-assistant-needs.md)

## Context

The brain runs wake word, speech-to-text, intents, text-to-speech and the LLM (REQ-2). The
Pi 5 (8 GB) already hosts the homelab (Home Assistant, Mosquitto, zigbee2mqtt). A benchmark
on 2026-10-28 (Ollama 0.12.6, 3 French prompts, `PROJECT_LOG.md`) measured short answers:

| Host / model | First token | tok/s | Short answer |
|---|---|---|---|
| Pi 5 `qwen2.5:3b` | 3.0 s | 5.3 | 16 s |
| HP ProBook 450 G5 (i5-8250U, 8 GB) `qwen2.5:3b` | 1.4 s | 8.0 | 8.7 s |
| ProBook `qwen2.5:7b` | 3.2 s | 3.6 | 13.5 s |

Only the ProBook with a 3B model meets NFR-5 (≤ 15 s) with margin.

## Decision drivers (weights /100)

LLM responsiveness (NFR-5) 35 · resilience — known commands still work when the LLM host is
down 25 · load on the homelab Pi 5 15 · simplicity 15 · power use 10.

## Options considered (MCDA, scores 0–5, totals /500)

| Criterion | A — Pi 5 alone | **B — Pi 5 pipeline + laptop LLM** | C — Laptop alone |
|---|---|---|---|
| Responsiveness (35) | 1 — 16 s, misses NFR-5 | 4 — 8.7 s, STT runs in parallel on the Pi 5 | 3 — STT and LLM share one i5 |
| Resilience (25) | 5 | 5 — intents stay on the Pi 5 | 1 — laptop off = no assistant |
| Homelab load (15) | 2 | 3 | 5 |
| Simplicity (15) | 5 | 3 — two hosts | 4 |
| Power (10) | 5 | 3 | 3 |
| **Total** | **315** | **385** | **295** |

Sensitivity: with responsiveness 50 and resilience 10, B still leads (370 vs 325 vs 255).

## Decision outcome

**B**. The Pi 5 runs wake word, speech-to-text, intents and text-to-speech; the laptop runs
Ollama with `qwen2.5:3b`, reachable from the LAN only. If the laptop is down, the LLM path
answers "I can't think right now" and known commands keep working.

## Consequences

- Install Ollama on the laptop as a boot service bound to the LAN, with a fixed IP lease.
- A system prompt asks for short answers and "I don't know" over guessing (all models made
  factual errors in the benchmark).
- Never pull large images on the Pi 5 SD card (Docker root is on the SD; incident 2026-10-28).
- Evolution: replace the laptop with a PC with an NVIDIA GPU of 8 GB or more (MCDA 380, vs
  mini-PC without GPU 345, NAS 290) — same split, bigger model.
- Fallback: A (315) if the laptop is retired before a replacement — accept a slower LLM path.
