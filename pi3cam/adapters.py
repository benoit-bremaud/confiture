"""Infrastructure adapters for the pan-tilt agent: PCA9685 servos, rpicam, paho, JSON files."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

import paho.mqtt.client as mqtt
from smbus2 import SMBus

log = logging.getLogger(__name__)

PCA_ADDR = 0x40
PERIOD_US = 20000  # 50 Hz, prescale 121 already set on the chip
LED0_ON_L = 0x06  # first channel register; 4 registers per channel
FULL_OFF = 0x10  # bit 4 of LEDn_OFF_H


class Pca9685Servos:
    """Waveshare Pan-Tilt HAT servos through the PCA9685 PWM chip on I²C bus 1."""

    def __init__(self, bus: SMBus) -> None:
        self.bus = bus

    def write_pulse(self, channel: int, us: int) -> None:
        off = round(us * 4096 / PERIOD_US)
        self.bus.write_i2c_block_data(
            PCA_ADDR, LED0_ON_L + 4 * channel, [0, 0, off & 0xFF, off >> 8]
        )

    def cut(self, channel: int) -> None:
        self.bus.write_i2c_block_data(
            PCA_ADDR, LED0_ON_L + 4 * channel, [0, 0, 0, FULL_OFF]
        )


class RpicamCamera:
    """Camera Module 3 through rpicam-still, mounted upside down."""

    def capture(self, width: int, height: int, quality: int) -> bytes:
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
    """One JSON file per name in the agent's config folder (mode 600 folder)."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def load(self, name: str) -> dict | None:
        path = self.folder / f"{name}.json"
        return json.loads(path.read_text()) if path.exists() else None

    def save(self, name: str, data: dict) -> None:
        (self.folder / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False))
