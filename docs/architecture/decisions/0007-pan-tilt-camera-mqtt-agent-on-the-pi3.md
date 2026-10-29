# ADR-0007 — Pan-tilt camera as an MQTT agent on the Pi 3

- **Status**: accepted (owner, 2026-10-28; structure 2026-10-29)
- **Date**: 2026-10-29
- **Deciders**: owner
- **Resolves**: REQ-13 (camera part), issue #3

## Context

REQ-13 asks to look through the Pi 3 camera from anywhere and aim it with the Waveshare
Pan-Tilt HAT (PCA9685 PWM chip, two hobby servos, no position feedback). Home Assistant on the
Pi 5 already runs an MQTT broker. A servo driven past its mechanical end stalls and heats, and
Home Assistant can send any value, so the limits must be enforced next to the hardware.

## Decision drivers (weights /100)

Security, no listening port on the Pi 3 · bandwidth on a Pi 3 Wi-Fi link · simplicity ·
Home Assistant integration.

## Options considered (MCDA, totals /500)

Transport, owner session 2026-10-28:

| Option | Total |
|---|---|
| **A — one Python agent, MQTT Discovery, JPEG snapshots on an MQTT topic** | **430** |
| D — A plus a 2-minute on-demand live stream | 385 |
| C — mqtt-io plus a script | 360 |
| B — continuous go2rtc stream | 325 |

Image refresh, owner session 2026-10-28: light 640×360 image every 2 s plus HD 1280×720 on
demand (option E, 425). Saved positions in one `select` and one `text` (option A, 440).

Code structure, owner session 2026-10-29:

| Criterion (weight) | **A — domain + adapters** | B — single file + mocks | C — full hexagonal |
|---|---|---|---|
| Clean / dependency rule (30) | 5 | 2 | 5 |
| Testability (25) | 5 | 3 | 5 |
| KISS / YAGNI (25) | 4 | 5 | 1 |
| Effort, regression risk (20) | 3 | 4 | 2 |
| **Total** | **445** | **335** | **345** |

Sensitivity: with KISS at 40 and Clean at 15, A still leads (425 vs 370).

## Decision outcome

**A** on both counts. `pi3cam/domain.py` holds servo safety (clamp to the calibrated pulse
limits, 1000 µs/s ramp, PWM cut after each move), saved positions and the command handling,
behind four protocols (`Servos`, `Camera`, `Publisher`, `Store`). `pi3cam/adapters.py`
implements them with smbus2, `rpicam-still`, paho-mqtt and JSON files; `pi3cam/main.py` wires
them. The agent only connects out to the broker, with a dedicated MQTT user and a last will.

The "recentre" button of #3 is replaced by the saved position "Position par défaut" (one tap
in the same `select`; the default can be redefined). The TSL25911 light sensor moves to its own
issue: it cannot be checked on hardware before this merge.

## Consequences

- Position is the last commanded one; after a restart the first move may jump.
- Images ride MQTT: a few tens of kB every 2 s on the LAN; Home Assistant's card must use
  `camera_view: live` (the default view refreshes every 10 s).
- The agent runs from crontab through `run.sh`, not systemd; the tilt-down limit (2300 µs)
  stays provisional until the Pi is mounted high.
- Revisit with option D if live view becomes a frequent need.
