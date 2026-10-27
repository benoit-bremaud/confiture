# voice-assistant — needs (phase 1 brainstorming, 2026-10-27)

Outcome of the owner brainstorming that precedes phase 1. Feeds the sequence, component,
deployment and data-flow diagrams. Use cases and NFR-1 to NFR-4:
[`voice-assistant-use-cases.md`](voice-assistant-use-cases.md).

## Context

- **Household**: the owner and children; nobody else. French only.
- **Rooms**: 2 satellites at start (Pi 3 + one to find).
- **Budget**: close to zero — recycled and second-hand hardware only.
- **Owner priorities**: responsiveness, intelligence, learning. Music and home control later.

## Existing infrastructure (read from `bb-homelab`, not modified)

- Raspberry Pi 5 homelab (4 or 8 GB RAM — to check with `free -h`): n8n, Vaultwarden, Caddy,
  Cloudflared, Uptime Kuma, Homepage, Jellyfin.
- Home automation stack outside that repo (`~/home-assistant`): Home Assistant 2026.6,
  zigbee2mqtt, Mosquitto. Runs as root, data not backed up (bb-homelab security audit).
- Old laptop, under 8 years, at least 8 GB RAM — candidate helper for the LLM.
- Recycled nodes: Raspberry Pi 1 ×2 (sensors), Raspberry Pi 3 (first satellite).

## Requirements

- **REQ-1 — Easy satellite enrolment**: adding a satellite takes flash + plug + one
  confirmation; no manual per-node configuration (realises UC8).
- **REQ-2 — Hybrid understanding**: known commands are handled instantly by local intents;
  anything else goes to an LLM (owner choice "Mixte").
- **REQ-3 — Child profile** (actor *Child*): a child may ask filtered questions, play music/radio with a
  capped volume, set timers, later watch a film/video; a child may not control home devices.
- **REQ-4 — Speaker recognition (iteration 2)**: the assistant recognises the owner's voice
  (voice embedding enrolled once); not in the first iteration, but promoted to iteration 2
  by the owner. Replaces the phone unlock of ADR-0002.
- **REQ-5 — Listening feedback**: the satellite plays a short sound on wake and shows its state
  with an LED (listening, thinking, muted).
- **REQ-6 — Ducking**: while the assistant listens or answers, connected devices that play
  sound (music, TV) lower their volume, then restore it.
- **REQ-7 — Music sources**: local library and web radios first; streaming deferred.
- **REQ-8 — Home Assistant integration**: reuse the existing Home Assistant and Mosquitto
  rather than a parallel stack; home control itself is deferred.

- **REQ-9 — Personality**: kind, gentle and educational first, playful with the children,
  a little empathetic — without overdoing it.
- **REQ-10 — Voices**: one female and one male voice to choose from (the children decide);
  occasionally a fun accent to make the household laugh (available accents to verify).
- **REQ-11 — Wake word chosen by the children**: shortlist by MCDA, final vote by the children.

## Open questions (to settle with MCDA, then ADR)

- ~~**Q1 — Child restrictions before speaker recognition**~~ — resolved by ADR-0002
  (per-satellite policy, phone unlock with expiry, night schedule).
- **Q2 — Brain host**: Pi 5 alone, Pi 5 + old laptop for the LLM, or the laptop alone?
  Depends on the Pi 5 RAM and on the homelab load.
- **Q3 — Second satellite**: which recycled hardware (Pi 1 is too weak for wake word)?
- **Q4 — Wake word**: shortlist done (MCDA, weights: wake reliability 30, fun 25, English-like
  pronunciation for training 20, personality fit 15, link to confiture 10): **Pépito 425**,
  Gribouille 355, Pépé 335 (nobody is called "pépé" at home), Ziggy 335; Kiwi 320 and
  Biscotte 315 dropped. **Pending: the children's vote**; the runner-up is the fallback if the
  winner trains badly (NFR-3).
- **Q5 — Prerequisite**: secure and back up the Home Assistant stack before relying on it.
- **Q6 — Local or cloud LLM** (REQ-2 vs NFR-1): a cloud LLM would receive the full transcript,
  which NFR-1 forbids. Either the LLM is local (limited by the hardware), or ADR-0001 gets an
  explicit exception for it. Strongly coupled with Q2.
- ~~**Q7 — LLM-path latency**~~ — resolved by ADR-0003 (thinking cue, streamed speech,
  ≤ 15 s; NFR-5).
