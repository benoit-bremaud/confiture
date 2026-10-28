# confiture 🍓

A personal voice assistant for the home whose voice processing stays local, built from recycled Raspberry Pis.
Old fruit, turned into something that keeps.

## Vision

- Custom wake word (our own "Alexa"), trained with openWakeWord.
- Voice stays local: no audio and no full transcript leaves the house; online services
  (weather, radio) only receive minimal queries (ADR-0001).
- Old Pis get a second life as voice satellites and room sensors.

## Architecture

Detail in [`docs/architecture/`](docs/architecture/README.md).

- **Brain** split over two hosts (ADR-0004): the homelab Pi 5 runs the voice pipeline (Home
  Assistant Assist: wake word, speech-to-text, intents, text-to-speech); an old laptop runs the
  local LLM with Ollama (ADR-0005).
- **Listening**: in iteration 1 the Pi 5 itself listens through a USB microphone in the living
  room (REQ-15); answers play on a Nest Mini used as an output only (REQ-12, REQ-16).
- **Satellites** (Raspberry Pi 3 and later nodes): extra listening points in other rooms.
- **Sensors** (Raspberry Pi 1 ×2): room data (temperature, humidity…) the assistant can query.

Tool candidates (versions to be verified before use): Home Assistant Assist, Wyoming protocol,
openWakeWord, Whisper, Piper, Ollama.

## Hardware inventory

| # | Model | Power | Boot | SD card | Next step |
|---|---|---|---|---|---|
| 1 | Raspberry Pi 1 | ✅ | ✅ | 2015 Raspbian (4 GB SD) | SSH diagnostic (needs Ethernet) |
| 2 | Raspberry Pi 1 | ✅ | ✅ | original card | SSH diagnostic (needs Ethernet) |
| 3 | Raspberry Pi 3 | ? | ? | Raspberry Pi OS Lite 32-bit trixie 2026-10-06 (32 GB microSD) | add Wi-Fi config, then diagnostic |

## Scripts

- [`scripts/configure-sd.sh`](scripts/configure-sd.sh) — writes the cloud-init user (hashed password)
  and optional Wi-Fi onto a freshly flashed boot partition. Run it interactively; never commit secrets.
