#!/usr/bin/env python3
"""Pi 3 Pan-Tilt camera agent for Home Assistant over MQTT (prototype, confiture#3).

Publishes a JPEG snapshot every INTERVAL seconds and right after each move, and exposes
pan / tilt sliders, saved positions, an HD photo and a privacy switch through MQTT Discovery.
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
INTERVAL = 2  # light stream; HD only on demand (MCDA option E, 425/500)
# Local, never committed (mode 600): broker host, MQTT user, MQTT password — one per file.
CONF = Path.home() / ".config/pi3cam"
BROKER = (CONF / "mqtt-broker").read_text().strip()
USER = (CONF / "mqtt-user").read_text().strip()
PASSWORD = (CONF / "mqtt-password").read_text().strip()
STATE_FILE = CONF / "state.json"
LIGHT = (640, 360, 70)   # width, height, JPEG quality
HD = (1280, 720, 85)

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
want_hd = threading.Event()
state = {"pan": 0, "tilt": 0, "camera": "ON"}
if STATE_FILE.exists():
    state.update(json.loads(STATE_FILE.read_text()))

# Saved positions (MCDA option A, 440/500): name -> [pan, tilt], kept on the Pi.
PRESETS_FILE = CONF / "presets.json"
DEFAULT = "Position par défaut"
presets = {DEFAULT: [0, 0]}
if PRESETS_FILE.exists():
    presets.update(json.loads(PRESETS_FILE.read_text()))
selected = {"preset": DEFAULT}
# Minimal UI: one select (go to / delete) and one text field (save under a name).
DELETE_PREFIX = "🗑 Supprimer « "


def delete_option():
    return f"{DELETE_PREFIX}{selected['preset']} »"


def preset_options():
    extra = [delete_option()] if selected["preset"] != DEFAULT else []
    return list(presets) + extra


def go_to(name):
    pan, tilt = presets[name]
    moves.put(("pan", pan))
    moves.put(("tilt", tilt))
    selected["preset"] = name


def report_presets():
    # Off the MQTT network thread: the pause below must not block it.
    threading.Thread(target=_report_presets, daemon=True).start()


def _report_presets():
    # The select's options live in its discovery config, so republish it on every change.
    client.publish("homeassistant/select/pi3_preset/config", json.dumps({
        "name": "Position", "unique_id": "pi3_preset", "options": preset_options(),
        "command_topic": f"{BASE}/preset/set", "state_topic": f"{BASE}/preset/state",
        "icon": "mdi:map-marker-outline", **DEVICE}), retain=True)
    time.sleep(0.5)  # let HA apply the new options before the state
    client.publish(f"{BASE}/preset/state", selected["preset"], retain=True)
    client.publish(f"{BASE}/preset_name/state", "", retain=True)


def save_presets():
    PRESETS_FILE.write_text(json.dumps(presets, ensure_ascii=False))
    report_presets()


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


DEVICE = {"availability_topic": f"{BASE}/status",
          "device": {"identifiers": ["pi3-pitest"], "name": "Pi 3",
                     "model": "Raspberry Pi 3 B + Camera Module 3 + Waveshare Pan-Tilt HAT",
                     "manufacturer": "Raspberry Pi"}}
# Entities dropped for a minimal UI: an empty retained config removes them from HA.
RETIRED = ["button/pi3_recentre", "button/pi3_set_default", "button/pi3_preset_save",
           "button/pi3_preset_delete", "button/pi3_snapshot"]


def discovery():
    entities = {
        "camera/pi3": {"name": "Caméra", "unique_id": "pi3_camera", "topic": f"{BASE}/camera"},
        "camera/pi3_hd": {"name": "Photo HD", "unique_id": "pi3_camera_hd", "topic": f"{BASE}/camera_hd"},
        "button/pi3_snapshot_hd": {"name": "Prendre une photo HD", "unique_id": "pi3_snapshot_hd",
                                   "command_topic": f"{BASE}/snapshot_hd", "icon": "mdi:camera-iris"},
        "number/pi3_pan": {"name": "Pan (gauche +)", "unique_id": "pi3_pan",
                           "command_topic": f"{BASE}/pan/set", "state_topic": f"{BASE}/pan/state",
                           "min": -100, "max": 100, "step": 5, "mode": "slider", "icon": "mdi:pan-horizontal"},
        "number/pi3_tilt": {"name": "Tilt (haut +)", "unique_id": "pi3_tilt",
                            "command_topic": f"{BASE}/tilt/set", "state_topic": f"{BASE}/tilt/state",
                            "min": -100, "max": 100, "step": 5, "mode": "slider", "icon": "mdi:pan-vertical"},
        "text/pi3_preset_name": {"name": "＋ Enregistrer la position sous…", "unique_id": "pi3_preset_name",
                                 "command_topic": f"{BASE}/preset_name/set",
                                 "state_topic": f"{BASE}/preset_name/state", "min": 0, "max": 30,
                                 "icon": "mdi:map-marker-plus-outline"},
        "switch/pi3_privacy": {"name": "Caméra active", "unique_id": "pi3_privacy",
                               "command_topic": f"{BASE}/privacy/set", "state_topic": f"{BASE}/privacy/state",
                               "icon": "mdi:cctv"},
    }
    for path, cfg in entities.items():
        client.publish(f"homeassistant/{path}/config", json.dumps({**DEVICE, **cfg}), retain=True)
    for path in RETIRED:
        client.publish(f"homeassistant/{path}/config", "", retain=True)


def on_connect(c, *_):
    c.publish(f"{BASE}/status", "online", retain=True)
    discovery()
    c.subscribe([(f"{BASE}/{t}", 0) for t in ("pan/set", "tilt/set", "snapshot_hd", "privacy/set",
                                                    "preset/set", "preset_name/set")])
    save_and_report()
    report_presets()


def on_message(c, userdata, msg):
    topic, payload = msg.topic.removeprefix(BASE + "/"), msg.payload.decode().strip()
    try:
        if topic in ("pan/set", "tilt/set"):
            moves.put((topic.split("/")[0], round(float(payload))))
        elif topic == "preset/set" and payload in presets:
            go_to(payload)
            report_presets()
        elif topic == "preset/set" and payload == delete_option():
            presets.pop(selected["preset"], None)
            selected["preset"] = DEFAULT
            save_presets()
        elif topic == "preset_name/set" and payload and not payload.startswith("🗑"):
            # The 🗑 prefix is reserved for the delete option (QA 2026-10-28: name collision).
            # Typing a name saves the current position under it (the default can be redefined too).
            presets[payload[:30]] = [state["pan"], state["tilt"]]
            selected["preset"] = payload[:30]
            save_presets()
        elif topic == "snapshot_hd":
            want_hd.set()
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

def capture(width, height, quality):
    cmd = ["rpicam-still", "-n", "-t", "1", "--rotation", "180", "--width", str(width),
           "--height", str(height), "-q", str(quality), "-o", "-"]
    shot = subprocess.run(cmd, capture_output=True, timeout=30)
    return shot.stdout if shot.returncode == 0 else b""


while True:
    if state["camera"] == "ON":
        if want_hd.is_set():
            want_hd.clear()
            if image := capture(*HD):
                client.publish(f"{BASE}/camera_hd", image)
        if image := capture(*LIGHT):
            client.publish(f"{BASE}/camera", image)
    else:
        want_hd.clear()
        client.publish(f"{BASE}/camera", b"")
        client.publish(f"{BASE}/camera_hd", b"")
    shoot_now.wait(INTERVAL)
    shoot_now.clear()
