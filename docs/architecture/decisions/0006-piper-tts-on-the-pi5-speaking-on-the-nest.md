# ADR-0006 — Piper text-to-speech on the Pi 5, speaking on the Nest Mini

- **Status**: accepted (owner, 2026-10-28)
- **Date**: 2026-10-28
- **Deciders**: owner
- **Resolves**: issue #4; realises REQ-12 and REQ-16 for iteration 1

## Context

Yuki answers in text only. Speech must stay local (NFR-1, ADR-0001), so a cloud voice is out;
Piper is the local French text-to-speech engine Home Assistant supports through the Wyoming
protocol. Answers play on the Nest Mini (REQ-16). Three questions remained: where Piper runs,
how an answer reaches the Nest before the Pi 5 satellite exists, and how the Nest fetches the
audio while the Pi 5 firewall keeps Home Assistant off the LAN.

## Decision drivers (weights /100)

Privacy and security 35 · reliability 30 · simplicity 20 · fit with the existing repos 15.

## Options considered (MCDA, scores 0–5, totals /500)

Where Piper runs, as a container on the Pi 5:

| Option | Total |
|---|---|
| **A — Compose project owned by this repository (`deploy/pi5/`)** | **480** |
| B — Plain `docker run` documented in a README | 415 |
| C — A new service in bb-homelab | 320 |

How an answer reaches the Nest (an Assist pipeline returns its audio to the caller only): the
script `yuki_say` runs `conversation.process`, then `tts.speak` on the Nest (owner, 415).

How the Nest fetches the audio (UFW drops 8123 from the LAN):

| Option | Total |
|---|---|
| **A — UFW allows 8123 from the Nest only; `internal_url` is the Pi LAN URL** | **435** |
| C — Open 8123 to the whole LAN | 330 |
| B — Serve Home Assistant through Caddy in HTTPS on the LAN (the Nest rejects the internal CA) | 265 |

Sensitivity: the firewall choice stays A when security drops from 35 to 20.

## Decision outcome

Piper runs as `wyoming-piper` 2.5.2 on the Pi 5 in this repository's compose project, published
on the loopback only, voice `fr_FR-siwis-medium`. The script `yuki_say` glues the Yuki agent to
the Nest until the satellite exists. bb-homelab#162 adds the UFW rule and home-assistant#32
loads scripts and moves `internal_url` to the LAN URL; the Nest and Pi 5 addresses are reserved
on the box.

## Measurements (2026-10-28)

| Step | Time |
|---|---|
| Question to answer text, warm model | 2.0 s |
| Question to the Nest starting playback, warm model | 2.2 s |
| Question to answer text, first question after Ollama starts | 16.6 s |

## Consequences

- Home Assistant asks Piper for `fr_FR`, not `fr`. Piper lists every language it could
  download, so the voice is chosen on purpose in `yuki_say`.
- Every other client still reaches Home Assistant over the tailnet; a companion app set to use
  the LAN URL at home would now hit the firewall.
- Ollama must be up: the ProBook now starts Docker at boot (it was socket-activated only).
- Revisit when the Pi 5 satellite exists: the pipeline will then speak directly and `yuki_say`
  can go.
