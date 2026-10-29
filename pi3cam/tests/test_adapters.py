"""Adapter tests: bytes sent to the PCA9685, rpicam failures, JSON files."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

from adapters import JsonStore, MqttBus, Pca9685Servos, RpicamCamera


class FakeSMBus:
    def __init__(self):
        self.writes = []

    def write_i2c_block_data(self, addr, reg, data):
        self.writes.append((addr, reg, data))


def test_pulse_register_and_bytes():
    bus = FakeSMBus()
    Pca9685Servos(bus).write_pulse(1, 1500)  # 1500 µs of 20 ms -> 307 ticks of 4096
    assert bus.writes == [(0x40, 0x0A, [0, 0, 307 & 0xFF, 307 >> 8])]


def test_cut_sets_full_off():
    bus = FakeSMBus()
    Pca9685Servos(bus).cut(0)
    assert bus.writes == [(0x40, 0x06, [0, 0, 0, 0x10])]


def test_capture_returns_jpeg_on_success(monkeypatch):
    seen = {}

    def run(cmd, **_kwargs):
        seen["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout=b"jpeg", stderr=b"")

    monkeypatch.setattr(subprocess, "run", run)
    assert RpicamCamera().capture(640, 360, 70) == b"jpeg"
    cmd = seen["cmd"]
    assert cmd[cmd.index("--rotation") + 1] == "180"
    assert cmd[cmd.index("--width") + 1] == "640"
    assert cmd[cmd.index("--height") + 1] == "360"
    assert cmd[cmd.index("-q") + 1] == "70"


def test_capture_failure_returns_empty(monkeypatch):
    def failed(*_args, **_kwargs):
        return SimpleNamespace(returncode=1, stdout=b"x", stderr=b"busy")

    monkeypatch.setattr(subprocess, "run", failed)
    assert RpicamCamera().capture(1, 1, 1) == b""


def test_capture_timeout_returns_empty(monkeypatch):
    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("rpicam-still", 30)

    monkeypatch.setattr(subprocess, "run", timeout)
    assert RpicamCamera().capture(1, 1, 1) == b""


def test_mqtt_bus_forwards_retain():
    sent = []
    client = SimpleNamespace(publish=lambda t, p, retain: sent.append((t, p, retain)))
    MqttBus(client).publish("a/b", "x", retain=True)
    assert sent == [("a/b", "x", True)]


def test_json_store_round_trip(tmp_path):
    store = JsonStore(tmp_path)
    assert store.load("presets") is None
    store.save("presets", {"Entrée": [1, 2]})
    assert store.load("presets") == {"Entrée": [1, 2]}
    assert "Entrée" in (tmp_path / "presets.json").read_text()


def test_json_store_treats_a_corrupt_file_as_missing(tmp_path):
    (tmp_path / "state.json").write_text('{"pan": 1')
    (tmp_path / "presets.json").write_text("[1, 2]")
    store = JsonStore(tmp_path)
    assert store.load("state") is None
    assert store.load("presets") is None


def test_json_store_save_is_atomic_and_private(tmp_path):
    store = JsonStore(tmp_path)
    store.save("state", {"pan": 1})
    store.save("state", {"pan": 2})
    assert store.load("state") == {"pan": 2}
    assert [p.name for p in tmp_path.iterdir()] == ["state.json"]
    assert (tmp_path / "state.json").stat().st_mode & 0o077 == 0
