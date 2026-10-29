# pi3cam — Pan-Tilt camera agent

Agent that lets Home Assistant look through and aim the Pi 3 camera over MQTT (issue #3).

## What it does

- Publishes a light JPEG (640×360, rotated 180°) every 2 s and right after each move, and a
  1280×720 photo on demand (MCDA option E, 425/500). Use `camera_view: live` in the HA card:
  the default `auto` view only refreshes every 10 s.
- Exposes through MQTT Discovery: camera, pan and tilt sliders (−100…100), an HD photo button,
  and a privacy switch (off = no new capture is started, an image still being captured is
  dropped, and HA's image is blanked).
- Saved positions, minimal UI (MCDA option A, 440/500): one `select` "Position" goes to a saved
  position; it also offers "🗑 Supprimer « name »" for the current one. One `text` field saves
  the current position under the typed name (typing the default name redefines it). Unlimited,
  stored in `~/.config/pi3cam/presets.json` on the Pi.
- Illuminance (issue #8): the HAT's TSL25911 light sensor, published in lux every 30 s on
  `confiture/pi3/illuminance` (`sensor`, `device_class: illuminance`). The gain is
  auto-ranged (1×, 25×, 428×, MCDA option B, 450/500); a saturated or failed reading is
  skipped.
- Servo safety stays in the agent: calibrated limits, 1000 µs/s ramp, PWM cut after each move.
  The position is the last commanded one; there is no feedback.

Decision: [ADR-0007](../docs/architecture/decisions/0007-pan-tilt-camera-mqtt-agent-on-the-pi3.md)
(MQTT agent, 430/500; domain + adapters, 445/500).

## Code layout

- `domain.py` — pure logic: servo limits and ramp, saved positions, HA commands, Discovery,
  lux conversion and auto-gain.
- `adapters.py` — PCA9685 servos and TSL25911 light sensor (smbus2), `rpicam-still`, paho-mqtt, JSON files.
- `main.py` — reads `~/.config/pi3cam`, wires the adapters, runs the mover thread and the
  capture loop.

## Tests

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest --cov=. --cov-report=xml:coverage.xml
```

## Install on the Pi 3

Prerequisites: Camera Module 3, Waveshare Pan-Tilt HAT, I²C enabled, user in `i2c,gpio,video`,
a dedicated MQTT user on the hub broker.

```bash
python3 -m venv ~/pi3cam && ~/pi3cam/bin/pip install paho-mqtt smbus2
cp main.py domain.py adapters.py run.sh ~/pi3cam/ && chmod 700 ~/pi3cam/run.sh
umask 077 && mkdir -p ~/.config/pi3cam
printf '%s\n' '<broker-ip>' > ~/.config/pi3cam/mqtt-broker
printf '%s\n' '<mqtt-user>' > ~/.config/pi3cam/mqtt-user
read -rs PW && printf '%s\n' "$PW" > ~/.config/pi3cam/mqtt-password
(crontab -l 2>/dev/null; echo '@reboot sleep 30 && $HOME/pi3cam/run.sh') | crontab -
```

`run.sh` restarts the agent if it exits. Logs: `~/pi3cam/pi3cam.log`.

## Known limits

- Started from crontab, not systemd (no sudo when it was set up).
- Tilt-down limit (2300 µs) is provisional; recalibrate once the Pi is mounted high.
- The first move after a restart may jump: the real servo position is unknown.
- Very bright direct sunlight (above ~88 000 lx) saturates the sensor: no value then.
