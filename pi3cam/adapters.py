"""Infrastructure adapters for the pan-tilt agent: PCA9685 servos, rpicam, paho, JSON files."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable

import paho.mqtt.client as mqtt
from smbus2 import SMBus

log = logging.getLogger(__name__)

PCA_ADDR = 0x40
PERIOD_US = 20000  # 50 Hz servo frame
MODE1, PRESCALE = 0x00, 0xFE
SLEEP, AUTO_INCREMENT, RESTART = 0x10, 0x20, 0x80  # MODE1 bits
PRESCALE_50HZ = 121  # round(25 MHz / (4096 × 50 Hz)) − 1
LED0_ON_L = 0x06  # first channel register; 4 registers per channel
FULL_OFF = 0x10  # bit 4 of LEDn_OFF_H


class Pca9685Servos:
    """Waveshare Pan-Tilt HAT servos through the PCA9685 PWM chip on I²C bus 1.

    The chip forgets its prescale on power loss, so every start sets 50 Hz (prescale is
    writable only while asleep) and enables register auto-increment for block writes.
    """

    def __init__(self, bus: SMBus, wait: Callable[[float], None] = time.sleep) -> None:
        self.bus = bus
        bus.write_byte_data(PCA_ADDR, MODE1, SLEEP)
        bus.write_byte_data(PCA_ADDR, PRESCALE, PRESCALE_50HZ)
        bus.write_byte_data(PCA_ADDR, MODE1, AUTO_INCREMENT)
        wait(0.0005)  # oscillator start-up (datasheet: 500 µs)
        bus.write_byte_data(PCA_ADDR, MODE1, AUTO_INCREMENT | RESTART)

    def write_pulse(self, channel: int, us: int) -> None:
        off = round(us * 4096 / PERIOD_US)
        self.bus.write_i2c_block_data(
            PCA_ADDR, LED0_ON_L + 4 * channel, [0, 0, off & 0xFF, off >> 8]
        )

    def cut(self, channel: int) -> None:
        # FULL_OFF sends no signal at all: the servo stops holding (no current, no jitter).
        self.bus.write_i2c_block_data(
            PCA_ADDR, LED0_ON_L + 4 * channel, [0, 0, 0, FULL_OFF]
        )


class RpicamCamera:
    """Camera Module 3 through rpicam-still, mounted upside down."""

    def capture(self, width: int, height: int, quality: int) -> bytes:
        # -n: no preview window; -t 1: shoot at once; 30 s timeout covers a busy camera.
        cmd = [
            "rpicam-still",
            "-n",
            "-t",
            "1",
            "--rotation",
            "180",
            "--width",
            str(width),
            "--height",
            str(height),
            "-q",
            str(quality),
            "-o",
            "-",
        ]
        try:
            shot = subprocess.run(cmd, capture_output=True, timeout=30, check=False)
        except subprocess.TimeoutExpired:
            log.warning("rpicam-still timed out")
            return b""
        if shot.returncode != 0:
            log.warning(
                "rpicam-still failed: %s", shot.stderr.decode(errors="replace")[-200:]
            )
            return b""
        return shot.stdout


class MqttBus:
    """paho client publishing the agent's topics."""

    def __init__(self, client: mqtt.Client) -> None:
        self.client = client

    def publish(self, topic: str, payload: str | bytes, retain: bool = False) -> None:
        self.client.publish(topic, payload, retain=retain)


class JsonStore:
    """One JSON file per name in the agent's config folder (created mode 700 at install).

    Writes are atomic (temp file then rename), so a power cut never leaves a corrupt
    file; a corrupt file still loads as None so the agent starts on defaults.
    """

    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def load(self, name: str) -> dict | None:
        path = self.folder / f"{name}.json"
        try:
            data = json.loads(path.read_text())
        except FileNotFoundError:
            return None
        except (json.JSONDecodeError, UnicodeDecodeError):
            log.warning("%s is corrupt, using defaults", path)
            return None
        return data if isinstance(data, dict) else None

    def save(self, name: str, data: dict) -> None:
        fd, tmp = tempfile.mkstemp(dir=self.folder, suffix=".tmp")  # mode 600
        try:
            with os.fdopen(fd, "w") as file:
                json.dump(data, file, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(tmp, self.folder / f"{name}.json")
        except OSError:
            Path(tmp).unlink(missing_ok=True)
            raise
