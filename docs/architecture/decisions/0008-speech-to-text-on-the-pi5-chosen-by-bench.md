# ADR-0008 — Speech-to-text on the Pi 5, model chosen by a recorded bench

- **Status**: proposed (owner, 2026-10-30): adult bench done, young-child bench pending
- **Date**: 2026-10-30
- **Deciders**: owner
- **Resolves**: benoit-bremaud/confiture#18; realises REQ-15 for iteration 1

## Context

Yuki can think (ADR-0004, ADR-0005) and speak (ADR-0006) but cannot listen. Questions are
free-form, so the engine needs an open vocabulary. The 2026-10-30 brainstorming chose
faster-whisper in a Wyoming container on the Pi 5 (415/500, over the laptop 380 and Vosk 350),
the model size to be picked by a bench: about 20 French sentences, adult and young child,
recorded with the USB webcam microphone on the Pi 5 at real living-room distance. Acceptance:
the smallest model with at least 8/10 correct child transcriptions and STT latency of 3 s or
less. Recordings are family voices and stay on the Pi 5 (`~/stt-bench/`), never here.

## Bench (adult, 10 sentences, 2026-10-30)

Run with `sttbench/` against the `rhasspy/wyoming-whisper:3.8.1` image on the Pi 5. Latency runs
from `audio-stop` to the transcript. "Correct" means an exact word match after normalisation,
so a verb spelling ("Traduit" for "Traduis") counts as wrong.

| Model | WER | Correct | Latency (max) | Memory |
|---|---|---|---|---|
| faster-whisper tiny-int8 | 55.2 % | 0/10 | 6.5 s | 340 MiB |
| faster-whisper base-int8 | 40.3 % | 0/10 | 10.9 s | 690 MiB |
| faster-whisper small-int8 | 22.4 % | 1/10 | 5.7 s | 600 MiB |
| sherpa Parakeet TDT 0.6B v3 int8 | 9.0 % | 6/10 | 0.8 s | ~1.4 GiB |
| sherpa Kroko FR streaming | 4.5 % | 7/10 | 0.7 s | 210 MiB |

No faster-whisper size meets the latency bound on the Pi 5 CPU, and none is accurate enough.
The same image ships a sherpa-onnx backend; both sherpa models answer in under 1 s.

A web review (Open ASR Leaderboard multilingual track, 2026 open-source STT roundups,
Wyoming STT projects) found no other French model that runs on a Pi 5 CPU: Moonshine and
Oread have no French model, Voxtral and Whisper large need a GPU, Vosk reports 10-15 % WER.
Parakeet TDT v3 scores 5.4 % French WER on the leaderboard; Kroko publishes no figures.
Studies on children's speech agree that error rates rise sharply for children and that larger
models degrade less, which favours Parakeet (0.6 B parameters) over Kroko.

## Options considered (MCDA, scores 0–5, totals /500)

Drivers: adult quality 30 · chance to hold with the child 25 · latency and memory 20 ·
licence and longevity 15 · simplicity 10.

| Option | Total |
|---|---|
| A — Kroko FR streaming only | 365 |
| B — Parakeet TDT v3 only | 425 |
| **C — Parakeet by default, Kroko one setting away, the child bench decides** | **435** |

Sensitivity: with adult quality 45 and child 10, A rises to 420 and C stays first (440).

## Decision

**C.** The `whisper` service runs the sherpa backend with Parakeet TDT v3 (`STT_LIBRARY=sherpa`);
`STT_STREAMING=1` switches to Kroko. The backend is always pinned: the image's default `auto`
picks one on its own. `mem_limit: 2g` (Parakeet ~1.4 GiB resident).

This departs from the faster-whisper engine named in #18: the bench showed it cannot meet the
acceptance on this hardware, and the Wyoming image, port and pipeline wiring are unchanged.

## Pending

- Young-child bench (10 sentences of `sttbench/sentences.tsv`), both sherpa models; keep the
  one with at least 8/10 child sentences correct, then set this ADR to accepted.

## Consequences

- Spoken end to end on 2026-10-30: wake word "Okay Nabu" on the satellite, "Quelle heure
  est-il ?" transcribed 0.36 s after the end of speech, answer spoken on the Nest through
  `nest-relay` and `script.yuki_speak` (the pipeline returns audio to the satellite only).
- Audio never leaves the Pi 5 and is never stored by the pipeline (REQ-20).
- Parakeet costs ~1.4 GiB of RAM next to Home Assistant; Kroko would free most of it.
- Kroko community models are CC-BY-SA with no published accuracy; prefer Parakeet on a tie.
