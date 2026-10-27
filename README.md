# confiture 🍓

A fully local, personal voice assistant for the home, built from recycled Raspberry Pis.
Old fruit, turned into something that keeps.

## Vision

- Custom wake word (our own "Alexa"), trained with openWakeWord.
- 100 % local: no voice data leaves the house.
- Old Pis get a second life as voice satellites and room sensors.

## Architecture (draft — to be formalised in UML)

- **Satellite** (Raspberry Pi 3): microphone + speaker, wake-word detection, streams audio to the brain.
- **Brain** (PC or second-hand mini-PC): speech-to-text, intent handling, text-to-speech, optional local LLM.
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
