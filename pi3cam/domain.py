"""Pan-tilt camera domain: servo safety, saved positions and MQTT commands (confiture#3).

Pure Python: no hardware, MQTT or file access here. Adapters implementing the protocols
below are injected by main.py (ADR-0007).
"""

from __future__ import annotations

import json
import queue
import threading
from typing import Callable, Protocol

BASE = "confiture/pi3"
LIGHT = (640, 360, 70)  # width, height, JPEG quality: light stream every INTERVAL s
HD = (1280, 720, 85)  # on demand only (MCDA option E, 425/500)
INTERVAL = 2

# Calibration 2026-10-28 (PROJECT_LOG): pulse widths in µs; position -100..100.
# Pan +100 = left (camera's point of view); tilt +100 = up. Tilt-down limit provisional.
AXES = {
    "pan": {"channel": 1, "minus": 500, "centre": 1625, "plus": 2750},
    "tilt": {"channel": 0, "minus": 2300, "centre": 1650, "plus": 500},
}
STEP_US = 20  # ramp: 20 µs every 20 ms = 1000 µs/s
STEP_DELAY = 0.02
SETTLE = 0.3  # hold the final pulse before cutting the signal

DEFAULT = "Position par défaut"
DELETE_PREFIX = "🗑 Supprimer « "
TRASH = "🗑"  # reserved for the delete option (QA 2026-10-28: name collision)
NAME_MAX = 30

DEVICE = {
    "availability_topic": f"{BASE}/status",
    "device": {
        "identifiers": ["pi3-pitest"],
        "name": "Pi 3",
        "model": "Raspberry Pi 3 B + Camera Module 3 + Waveshare Pan-Tilt HAT",
        "manufacturer": "Raspberry Pi",
    },
}
# Entities dropped for a minimal UI: an empty retained config removes them from HA.
RETIRED = [
    "button/pi3_recentre",
    "button/pi3_set_default",
    "button/pi3_preset_save",
    "button/pi3_preset_delete",
    "button/pi3_snapshot",
]
SUBSCRIPTIONS = [
    f"{BASE}/{t}"
    for t in (
        "pan/set",
        "tilt/set",
        "snapshot_hd",
        "privacy/set",
        "preset/set",
        "preset_name/set",
    )
]


class Servos(Protocol):
    def write_pulse(self, channel: int, us: int) -> None: ...
    def cut(self, channel: int) -> None: ...


class Camera(Protocol):
    def capture(self, width: int, height: int, quality: int) -> bytes: ...


class Publisher(Protocol):
    def publish(
        self, topic: str, payload: str | bytes, retain: bool = False
    ) -> None: ...


class Store(Protocol):
    def load(self, name: str) -> dict | None: ...
    def save(self, name: str, data: dict) -> None: ...


def clamp(position: float) -> int:
    return max(-100, min(100, round(position)))


def pulse_for(axis: str, position: float) -> int:
    """Pulse width in µs for a position; always inside the calibrated limits."""
    a = AXES[axis]
    position = clamp(position)
    end = a["plus"] if position >= 0 else a["minus"]
    return round(a["centre"] + (end - a["centre"]) * abs(position) / 100)


def ramp(current: int, goal: int) -> list[int]:
    """Pulse widths from current to goal in STEP_US steps, goal included."""
    step = STEP_US if goal > current else -STEP_US
    return [*range(current, goal, step), goal]


def discovery_configs() -> dict[str, str]:
    """Retained MQTT Discovery payloads, topic -> JSON (empty string retires an entity)."""
    entities = {
        "camera/pi3": {
            "name": "Caméra",
            "unique_id": "pi3_camera",
            "topic": f"{BASE}/camera",
        },
        "camera/pi3_hd": {
            "name": "Photo HD",
            "unique_id": "pi3_camera_hd",
            "topic": f"{BASE}/camera_hd",
        },
        "button/pi3_snapshot_hd": {
            "name": "Prendre une photo HD",
            "unique_id": "pi3_snapshot_hd",
            "command_topic": f"{BASE}/snapshot_hd",
            "icon": "mdi:camera-iris",
        },
        "number/pi3_pan": {
            "name": "Pan (gauche +)",
            "unique_id": "pi3_pan",
            "command_topic": f"{BASE}/pan/set",
            "state_topic": f"{BASE}/pan/state",
            "min": -100,
            "max": 100,
            "step": 5,
            "mode": "slider",
            "icon": "mdi:pan-horizontal",
        },
        "number/pi3_tilt": {
            "name": "Tilt (haut +)",
            "unique_id": "pi3_tilt",
            "command_topic": f"{BASE}/tilt/set",
            "state_topic": f"{BASE}/tilt/state",
            "min": -100,
            "max": 100,
            "step": 5,
            "mode": "slider",
            "icon": "mdi:pan-vertical",
        },
        "text/pi3_preset_name": {
            "name": "＋ Enregistrer la position sous…",
            "unique_id": "pi3_preset_name",
            "command_topic": f"{BASE}/preset_name/set",
            "state_topic": f"{BASE}/preset_name/state",
            "min": 0,
            "max": NAME_MAX,
            "icon": "mdi:map-marker-plus-outline",
        },
        "switch/pi3_privacy": {
            "name": "Caméra active",
            "unique_id": "pi3_privacy",
            "command_topic": f"{BASE}/privacy/set",
            "state_topic": f"{BASE}/privacy/state",
            "icon": "mdi:cctv",
        },
    }
    configs = {
        f"homeassistant/{path}/config": json.dumps({**DEVICE, **cfg})
        for path, cfg in entities.items()
    }
    configs.update({f"homeassistant/{path}/config": "" for path in RETIRED})
    return configs


class Agent:
    """Serialises moves, keeps state and saved positions, answers HA commands."""

    def __init__(
        self,
        servos: Servos,
        camera: Camera,
        bus: Publisher,
        store: Store,
        sleep: Callable[[float], None],
        run_later: Callable[[Callable[[], None]], None],
    ):
        self.servos, self.camera, self.bus, self.store = servos, camera, bus, store
        self.sleep, self.run_later = sleep, run_later
        self.moves: queue.Queue[tuple[str, int]] = queue.Queue()
        self.shoot_now = threading.Event()
        self.want_hd = threading.Event()
        self.state = {
            "pan": 0,
            "tilt": 0,
            "camera": "ON",
            **(store.load("state") or {}),
        }
        self.presets = {DEFAULT: [0, 0], **(store.load("presets") or {})}
        self.selected = DEFAULT

    # --- servos -------------------------------------------------------------------------
    def move(self, axis: str, target: float) -> None:
        """Ramp to target, hold, then cut the PWM signal (no position feedback)."""
        channel = AXES[axis]["channel"]
        for us in ramp(pulse_for(axis, self.state[axis]), pulse_for(axis, target)):
            self.servos.write_pulse(channel, us)
            self.sleep(STEP_DELAY)
        self.sleep(SETTLE)
        self.servos.cut(channel)
        self.state[axis] = clamp(target)

    def next_move(self) -> None:
        """Run one queued move, report it and trigger a snapshot (mover thread)."""
        axis, target = self.moves.get()
        self.move(axis, target)
        self.save_and_report()
        self.shoot_now.set()

    # --- state and presets --------------------------------------------------------------
    def save_and_report(self) -> None:
        self.store.save("state", self.state)
        for key in ("pan", "tilt"):
            self.bus.publish(f"{BASE}/{key}/state", str(self.state[key]), retain=True)
        self.bus.publish(f"{BASE}/privacy/state", self.state["camera"], retain=True)

    def delete_option(self) -> str:
        return f"{DELETE_PREFIX}{self.selected} »"

    def preset_options(self) -> list[str]:
        extra = [self.delete_option()] if self.selected != DEFAULT else []
        return [*self.presets, *extra]

    def go_to(self, name: str) -> None:
        pan, tilt = self.presets[name]
        self.moves.put(("pan", pan))
        self.moves.put(("tilt", tilt))
        self.selected = name

    def report_presets(self) -> None:
        # Off the MQTT network thread: the pause below must not block it.
        self.run_later(self._report_presets)

    def _report_presets(self) -> None:
        # The select's options live in its discovery config, so republish it on every change.
        self.bus.publish(
            "homeassistant/select/pi3_preset/config",
            json.dumps(
                {
                    "name": "Position",
                    "unique_id": "pi3_preset",
                    "options": self.preset_options(),
                    "command_topic": f"{BASE}/preset/set",
                    "state_topic": f"{BASE}/preset/state",
                    "icon": "mdi:map-marker-outline",
                    **DEVICE,
                }
            ),
            retain=True,
        )
        self.sleep(0.5)  # let HA apply the new options before the state
        self.bus.publish(f"{BASE}/preset/state", self.selected, retain=True)
        self.bus.publish(f"{BASE}/preset_name/state", "", retain=True)

    def save_presets(self) -> None:
        self.store.save("presets", self.presets)
        self.report_presets()

    # --- MQTT ---------------------------------------------------------------------------
    def on_connect(self) -> None:
        """(Re)announce everything: runs on every (re)connection, so Wi-Fi drops heal."""
        self.bus.publish(f"{BASE}/status", "online", retain=True)
        for topic, payload in discovery_configs().items():
            self.bus.publish(topic, payload, retain=True)
        self.save_and_report()
        self.report_presets()

    def handle(self, topic: str, payload: str) -> None:
        """Apply one HA command; malformed or unknown commands are ignored."""
        topic, payload = topic.removeprefix(BASE + "/"), payload.strip()
        if topic in ("pan/set", "tilt/set"):
            try:
                self.moves.put((topic.split("/")[0], round(float(payload))))
            except ValueError:
                return
        elif topic == "preset/set" and payload in self.presets:
            self.go_to(payload)
            self.report_presets()
        elif topic == "preset/set" and payload == self.delete_option():
            self.presets.pop(self.selected, None)
            self.selected = DEFAULT
            self.save_presets()
        elif topic == "preset_name/set" and payload and not payload.startswith(TRASH):
            # Typing a name saves the current position under it (the default can be redefined).
            name = payload[:NAME_MAX]
            self.presets[name] = [self.state["pan"], self.state["tilt"]]
            self.selected = name
            self.save_presets()
        elif topic == "snapshot_hd":
            self.want_hd.set()
            self.shoot_now.set()
        elif topic == "privacy/set" and payload in ("ON", "OFF"):
            self.state["camera"] = payload
            self.save_and_report()
            self.shoot_now.set()

    # --- camera -------------------------------------------------------------------------
    def shoot(self) -> None:
        """One capture cycle: HD if asked, then the light image; privacy publishes blanks."""
        if self.state["camera"] != "ON":
            self.want_hd.clear()
            self.bus.publish(f"{BASE}/camera", b"")
            self.bus.publish(f"{BASE}/camera_hd", b"")
            return
        if self.want_hd.is_set():
            self.want_hd.clear()
            if image := self.camera.capture(*HD):
                self.bus.publish(f"{BASE}/camera_hd", image)
        if image := self.camera.capture(*LIGHT):
            self.bus.publish(f"{BASE}/camera", image)
