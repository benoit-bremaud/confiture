"""Pan-tilt camera domain: servo safety, saved positions and MQTT commands (confiture#3).

Pure Python: no hardware, MQTT or file access here. Adapters implementing the protocols
below are injected by main.py (ADR-0007).
"""

from __future__ import annotations

import json
import math
import queue
import threading
from typing import Callable, Protocol

BASE = "confiture/pi3"
PAN_SET, TILT_SET = "pan/set", "tilt/set"
PRESET_SET, PRESET_NAME_SET = "preset/set", "preset_name/set"
SNAPSHOT_HD, PRIVACY_SET = "snapshot_hd", "privacy/set"
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
TRASH = "🗑"  # reserved for the delete option (QA 2026-10-28: name collision)
DELETE_PREFIX = f"{TRASH} Supprimer « "
HA_APPLY_DELAY = 0.5  # let HA apply new select options before the state
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
    for t in (PAN_SET, TILT_SET, SNAPSHOT_HD, PRIVACY_SET, PRESET_SET, PRESET_NAME_SET)
]


class Servos(Protocol):
    """Raw servo output: write_pulse sets a pulse width in µs on a channel; cut stops
    the PWM signal so the servo neither holds nor jitters."""

    def write_pulse(self, channel: int, us: int) -> None: ...
    def cut(self, channel: int) -> None: ...


class Camera(Protocol):
    """Still-image source: JPEG bytes, or b"" on failure (callers skip empty images)."""

    def capture(self, width: int, height: int, quality: int) -> bytes: ...


class Publisher(Protocol):
    """Fire-and-forget MQTT publish; retained messages survive reconnections."""

    def publish(
        self, topic: str, payload: str | bytes, retain: bool = False
    ) -> None: ...


class Store(Protocol):
    """Named JSON persistence: load returns None when nothing valid was saved."""

    def load(self, name: str) -> dict | None: ...
    def save(self, name: str, data: dict) -> None: ...


def clamp(position: float) -> int:
    """Round a position into -100..100."""
    return max(-100, min(100, round(position)))


def pulse_for(axis: str, position: float) -> int:
    """Pulse width in µs for a position; always inside the calibrated limits."""
    a = AXES[axis]
    position = clamp(position)
    end = a["plus"] if position >= 0 else a["minus"]
    return round(a["centre"] + (end - a["centre"]) * abs(position) / 100)


def is_position(value: object) -> bool:
    """True for a finite number (bool excluded): guards commands and stored data."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


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
        # One lock for the paho, mover and report threads that share state and presets.
        self.lock = threading.RLock()
        self.state: dict[str, int | str] = {"pan": 0, "tilt": 0, "camera": "ON"}
        saved = store.load("state") or {}
        for axis in AXES:
            if is_position(saved.get(axis)):
                self.state[axis] = clamp(saved[axis])
        if saved.get("camera") in ("ON", "OFF"):
            self.state["camera"] = saved["camera"]
        self.presets: dict[str, list[int]] = {DEFAULT: [0, 0]}
        for name, pos in (store.load("presets") or {}).items():
            if isinstance(pos, list) and len(pos) == 2 and all(map(is_position, pos)):
                self.presets[str(name)[:NAME_MAX]] = [clamp(v) for v in pos]
        self.selected = DEFAULT

    def move(self, axis: str, target: float) -> None:
        """Ramp to target, hold, then cut the PWM signal (no position feedback).

        The signal is cut even if the move fails, so a stalled servo never keeps a pulse.
        """
        channel = AXES[axis]["channel"]
        try:
            for us in ramp(pulse_for(axis, self.state[axis]), pulse_for(axis, target)):
                self.servos.write_pulse(channel, us)
                self.sleep(STEP_DELAY)
            self.sleep(SETTLE)
        finally:
            self.servos.cut(channel)
        self.state[axis] = clamp(target)

    def next_move(self) -> None:
        """Run one queued move, report it and trigger a snapshot (mover thread)."""
        axis, target = self.moves.get()
        self.move(axis, target)
        with self.lock:
            self.save_and_report()
        self.shoot_now.set()

    def wait_for_shot(self, timeout: float) -> None:
        """Block until a command asks for a picture or the interval elapses."""
        self.shoot_now.wait(timeout)
        self.shoot_now.clear()

    def save_and_report(self) -> None:
        """Persist the state and publish it, retained, so HA shows it after a restart."""
        self.store.save("state", self.state)
        for key in ("pan", "tilt"):
            self.bus.publish(f"{BASE}/{key}/state", str(self.state[key]), retain=True)
        self.bus.publish(f"{BASE}/privacy/state", self.state["camera"], retain=True)

    def delete_option(self) -> str:
        """Select option that deletes the selected saved position."""
        return f"{DELETE_PREFIX}{self.selected} »"

    def preset_options(self) -> list[str]:
        """Saved positions, plus the delete option unless the default is selected."""
        extra = [self.delete_option()] if self.selected != DEFAULT else []
        return [*self.presets, *extra]

    def go_to(self, name: str) -> None:
        """Queue both axes to a saved position and make it the selected one."""
        pan, tilt = self.presets[name]
        self.moves.put(("pan", pan))
        self.moves.put(("tilt", tilt))
        self.selected = name

    def report_presets(self) -> None:
        """Republish the preset select asynchronously (returns at once).

        Runs off the MQTT network thread, which the HA_APPLY_DELAY pause must not block.
        """
        with self.lock:
            options, selected = self.preset_options(), self.selected
        self.run_later(lambda: self._report_presets(options, selected))

    def _report_presets(self, options: list[str], selected: str) -> None:
        # The select's options live in its discovery config, so republish it on every change.
        self.bus.publish(
            "homeassistant/select/pi3_preset/config",
            json.dumps(
                {
                    "name": "Position",
                    "unique_id": "pi3_preset",
                    "options": options,
                    "command_topic": f"{BASE}/{PRESET_SET}",
                    "state_topic": f"{BASE}/preset/state",
                    "icon": "mdi:map-marker-outline",
                    **DEVICE,
                }
            ),
            retain=True,
        )
        self.sleep(HA_APPLY_DELAY)
        self.bus.publish(f"{BASE}/preset/state", selected, retain=True)
        self.bus.publish(f"{BASE}/preset_name/state", "", retain=True)

    def save_presets(self) -> None:
        """Persist the presets, then republish the select."""
        self.store.save("presets", self.presets)
        self.report_presets()

    def on_connect(self) -> None:
        """(Re)announce everything: runs on every (re)connection, so Wi-Fi drops heal."""
        self.bus.publish(f"{BASE}/status", "online", retain=True)
        for topic, payload in discovery_configs().items():
            self.bus.publish(topic, payload, retain=True)
        with self.lock:
            self.save_and_report()
        self.report_presets()

    def handle(self, topic: str, payload: str) -> None:
        """Apply one HA command; malformed or unknown commands are ignored."""
        with self.lock:
            self._handle(topic.removeprefix(BASE + "/"), payload.strip())

    def _handle(self, topic: str, payload: str) -> None:
        if topic in (PAN_SET, TILT_SET):
            try:
                target = float(payload)
            except ValueError:
                return
            if is_position(target):
                self.moves.put((topic.split("/")[0], clamp(target)))
        elif topic == PRESET_SET and payload in self.presets:
            self.go_to(payload)
            self.report_presets()
        elif (
            topic == PRESET_SET
            and self.selected != DEFAULT
            and payload == self.delete_option()
        ):
            self.presets.pop(self.selected, None)
            self.selected = DEFAULT
            self.save_presets()
        elif topic == PRESET_NAME_SET and payload and not payload.startswith(TRASH):
            # Typing a name saves the current position under it (the default can be redefined).
            name = payload[:NAME_MAX]
            self.presets[name] = [self.state["pan"], self.state["tilt"]]
            self.selected = name
            self.save_presets()
        elif topic == SNAPSHOT_HD:
            self.want_hd.set()
            self.shoot_now.set()
        elif topic == PRIVACY_SET and payload in ("ON", "OFF"):
            self.state["camera"] = payload
            self.save_and_report()
            self.shoot_now.set()

    def shoot(self) -> None:
        """One capture cycle: HD if asked, then the light image; privacy publishes blanks."""
        with self.lock:
            camera_on = self.state["camera"] == "ON"
        if not camera_on:
            self.want_hd.clear()
            self.bus.publish(f"{BASE}/camera", b"")
            self.bus.publish(f"{BASE}/camera_hd", b"")
            return
        if self.want_hd.is_set():
            self.want_hd.clear()
            self._publish_image("camera_hd", self.camera.capture(*HD))
        with self.lock:
            if self.state["camera"] != "ON":  # switched off during the HD capture
                return
        self._publish_image("camera", self.camera.capture(*LIGHT))

    def _publish_image(self, topic: str, image: bytes) -> None:
        # A capture can take seconds: recheck privacy under the lock, so an image taken
        # before "camera off" is never published after it.
        with self.lock:
            if image and self.state["camera"] == "ON":
                self.bus.publish(f"{BASE}/{topic}", image)
