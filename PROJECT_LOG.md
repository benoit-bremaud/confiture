# Project log

## 2026-10-27 — Project bootstrap

- Hardware triage (power + boot LEDs): Pi #1 (Pi 1) OK with the 2015 card; Pi #2 (Pi 1) OK with its
  original card (first failure was a card seating issue); Pi #3 (Pi 3) not yet observed.
- Decision (MCDA): test the Pi 1s with the existing 2015 card as-is (405/500) rather than reflash (380/500).
- Flashed a 32 GB microSD with Raspberry Pi OS Lite 32-bit trixie 2026-10-06 (SHA-256 verified),
  SSH enabled. First boot on Pi #3 had no network (no Ethernet, no Wi-Fi entered) — to redo at home.
- Decision (MCDA): project name `confiture` (410/500); fallback `pi-phoenix` (400/500).
- Scope decision: the project is a fully local personal voice assistant (satellite + brain architecture).
