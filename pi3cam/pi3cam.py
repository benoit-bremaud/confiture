#!/usr/bin/env python3
"""Pi 3 Pan-Tilt camera agent for Home Assistant over MQTT (prototype, confiture#3).

Publishes a JPEG snapshot every INTERVAL seconds and right after each move, and exposes
pan / tilt sliders, a recentre button and a privacy switch through MQTT Discovery.
Servo safety lives here, never in HA: positions are clamped to the calibrated limits,
moves are ramped, and the PWM signal is cut after each move (no position feedback).
"""
import json
import queue
import subprocess
import threading
import time
from pathlib import Path

import paho.mqtt.client as mqtt
from smbus2 import SMBus

BASE = "confiture/pi3"
INTERVAL = 10
# Local, never committed (mode 600): broker host, MQTT user, MQTT password — one per file.
CONF = Path.home() / ".config/pi3cam"
BROKER = (CONF / "mqtt-broker").read_text().strip()
USER = (CONF / "mqtt-user").read_text().strip()
PASSWORD = (CONF / "mqtt-password").read_text().strip()
STATE_FILE = CONF / "state.json"
CAPTURE = ["rpicam-still", "-n", "-t", "1", "--rotation", "180",
           "--width", "1280", "--height", "720", "-q", "80", "-o", "-"]

# Calibration 2026-10-28 (PROJECT_LOG): pulse widths in µs; position -100..100.
# Pan +100 = left (camera's point of view); tilt +100 = up. Tilt-down limit provisional.
AXES = {
    "pan": {"channel": 1, "minus": 500, "centre": 1625, "plus": 2750},
    "tilt": {"channel": 0, "minus": 2300, "centre": 1650, "plus": 500},
}
PCA_ADDR = 0x40
STEP_US = 20       # ramp: 20 µs every 20 ms = 1000 µs/s
STEP_DELAY = 0.02
PERIOD_US = 20000  # 50 Hz, prescale 121 already set on the chip

bus = SMBus(1)
moves = queue.Queue()
shoot_now = threading.Event()
state = {"pan": 0, "tilt": 0, "camera": "ON"}
if STATE_FILE.exists():
    state.update(json.loads(STATE_FILE.read_text()))


def pulse_for(axis, position):
    a = AXES[axis]
    position = max(-100, min(100, position))
    end = a["plus"] if position >= 0 else a["minus"]
    return round(a["centre"] + (end - a["centre"]) * abs(position) / 100)


def write_pulse(channel, us):
    reg = 0x06 + 4 * channel
    off = round(us * 4096 / PERIOD_US)
    bus.write_i2c_block_data(PCA_ADDR, reg, [0, 0, off & 0xFF, off >> 8])


def cut_signal(channel):
    bus.write_i2c_block_data(PCA_ADDR, 0x06 + 4 * channel, [0, 0, 0, 0x10])  # full OFF


def move(axis, target):
    channel = AXES[axis]["channel"]
    current, goal = pulse_for(axis, state[axis]), pulse_for(axis, target)
    step = STEP_US if goal > current else -STEP_US
    for us in range(current, goal, step):
        write_pulse(channel, us)
        time.sleep(STEP_DELAY)
    write_pulse(channel, goal)
    time.sleep(0.3)
    cut_signal(channel)
    state[axis] = max(-100, min(100, target))


def save_and_report():
    STATE_FILE.write_text(json.dumps(state))
    for key in ("pan", "tilt"):
        client.publish(f"{BASE}/{key}/state", str(state[key]), retain=True)
    client.publish(f"{BASE}/privacy/state", state["camera"], retain=True)


def mover():
    while True:
        axis, target = moves.get()
        move(axis, target)
        save_and_report()
        shoot_now.set()


def discovery():
    device = {"identifiers": ["pi3-pitest"], "name": "Pi 3",
              "model": "Raspberry Pi 3 B + Camera Module 3 + Waveshare Pan-Tilt HAT",
              "manufacturer": "Raspberry Pi"}
    common = {"availability_topic": f"{BASE}/status", "device": device}
    entities = {
        "camera/pi3": {"name": "Caméra", "unique_id": "pi3_camera", "topic": f"{BASE}/camera"},
        "number/pi3_pan": {"name": "Pan (gauche +)", "unique_id": "pi3_pan",
                           "command_topic": f"{BASE}/pan/set", "state_topic": f"{BASE}/pan/state",
                           "min": -100, "max": 100, "step": 10, "mode": "slider", "icon": "mdi:pan-horizontal"},
        "number/pi3_tilt": {"name": "Tilt (haut +)", "unique_id": "pi3_tilt",
                            "command_topic": f"{BASE}/tilt/set", "state_topic": f"{BASE}/tilt/state",
                            "min": -100, "max": 100, "step": 10, "mode": "slider", "icon": "mdi:pan-vertical"},
        "button/pi3_recentre": {"name": "Recentrer", "unique_id": "pi3_recentre",
                                "command_topic": f"{BASE}/recentre", "icon": "mdi:image-filter-center-focus"},
        "button/pi3_snapshot": {"name": "Photo maintenant", "unique_id": "pi3_snapshot",
                                "command_topic": f"{BASE}/snapshot", "icon": "mdi:camera"},
        "switch/pi3_privacy": {"name": "Caméra active", "unique_id": "pi3_privacy",
                               "command_topic": f"{BASE}/privacy/set", "state_topic": f"{BASE}/privacy/state",
                               "icon": "mdi:cctv"},
    }
    for path, cfg in entities.items():
        client.publish(f"homeassistant/{path}/config", json.dumps({**common, **cfg}), retain=True)


def on_connect(c, *_):
    c.publish(f"{BASE}/status", "online", retain=True)
    discovery()
    c.subscribe([(f"{BASE}/{t}", 0) for t in ("pan/set", "tilt/set", "recentre", "snapshot", "privacy/set")])
    save_and_report()


def on_message(c, userdata, msg):
    topic, payload = msg.topic.removeprefix(BASE + "/"), msg.payload.decode().strip()
    try:
        if topic in ("pan/set", "tilt/set"):
            moves.put((topic.split("/")[0], round(float(payload))))
        elif topic == "recentre":
            moves.put(("pan", 0))
            moves.put(("tilt", 0))
        elif topic == "snapshot":
            shoot_now.set()
        elif topic == "privacy/set" and payload in ("ON", "OFF"):
            state["camera"] = payload
            save_and_report()
            shoot_now.set()
    except ValueError:
        pass  # ignore malformed commands


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pi3-camera")
client.username_pw_set(USER, PASSWORD)
client.will_set(f"{BASE}/status", "offline", retain=True)
client.on_connect = on_connect
client.on_message = on_message
client.connect_async(BROKER)
client.loop_start()
threading.Thread(target=mover, daemon=True).start()

while True:
    if state["camera"] == "ON":
        shot = subprocess.run(CAPTURE, capture_output=True, timeout=30)
        if shot.returncode == 0 and shot.stdout:
            client.publish(f"{BASE}/camera", shot.stdout)
    else:
        client.publish(f"{BASE}/camera", b"", retain=False)
    shoot_now.wait(INTERVAL)
    shoot_now.clear()
