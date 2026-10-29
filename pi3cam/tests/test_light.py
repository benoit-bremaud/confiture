"""Light sensor tests: lux equation, auto-gain, TSL25911 register traffic (confiture#8)."""

from __future__ import annotations

import json

import pytest

from adapters import Tsl2591Sensor
from domain import SATURATED, LightMeter, discovery_configs, lux, next_gain


class FakeBus:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload, retain=False):
        self.published.append((topic, payload, retain))


class FakeSensor:
    """Answers each read with the next (full, ir) counts, recording the gain asked."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.gains = []

    def read(self, gain):
        self.gains.append(gain)
        return self.answers.pop(0)


def test_lux_reference_equation():
    # cpl = 100 ms × 25 / 408; lux = (1000 − 200) × (1 − 200/1000) / cpl
    assert lux(1000, 200, 25) == pytest.approx(800 * 0.8 / (2500 / 408))


def test_lux_scales_inversely_with_gain():
    assert lux(1000, 200, 1) == pytest.approx(25 * lux(1000, 200, 25))


def test_lux_is_zero_in_the_dark_and_never_negative():
    assert lux(0, 0, 428) == 0.0
    assert lux(100, 150, 25) == 0.0  # infrared above full spectrum (noise)


@pytest.mark.parametrize(
    ("gain", "full", "expected"),
    [
        (25, SATURATED, 1),
        (1, SATURATED, None),  # lowest gain: nothing lower to try
        (25, 99, 428),
        (428, 5, None),  # highest gain: nothing higher to try
        (25, 5000, None),
    ],
)
def test_next_gain(gain, full, expected):
    assert next_gain(gain, full) == expected


def test_meter_publishes_lux_at_medium_gain():
    bus = FakeBus()
    LightMeter(FakeSensor((1000, 200)), bus).report()
    assert bus.published == [
        ("confiture/pi3/illuminance", f"{lux(1000, 200, 25):.1f}", False)
    ]


def test_meter_drops_gain_when_saturated_and_keeps_it():
    sensor = FakeSensor((SATURATED, 9000), (2000, 300), (2000, 300))
    meter = LightMeter(sensor, FakeBus())
    assert meter.read_lux() == pytest.approx(lux(2000, 300, 1))
    meter.read_lux()
    assert sensor.gains == [25, 1, 1]


def test_meter_raises_gain_in_the_dark():
    sensor = FakeSensor((10, 2), (4000, 800))
    assert LightMeter(sensor, FakeBus()).read_lux() == pytest.approx(
        lux(4000, 800, 428)
    )


def test_meter_publishes_nothing_when_saturated_at_lowest_gain():
    bus = FakeBus()
    LightMeter(FakeSensor((SATURATED, 0), (SATURATED, 0)), bus).report()
    assert bus.published == []


def test_meter_gives_up_on_a_flickering_light():
    sensor = FakeSensor((SATURATED, 0), (10, 0), (SATURATED, 0))
    assert LightMeter(sensor, FakeBus()).read_lux() is None
    assert len(sensor.gains) == 3


def test_meter_publishes_nothing_on_sensor_failure():
    bus = FakeBus()
    LightMeter(FakeSensor(None), bus).report()
    assert bus.published == []


def test_discovery_declares_an_illuminance_sensor():
    cfg = json.loads(discovery_configs()["homeassistant/sensor/pi3_illuminance/config"])
    assert cfg["device_class"] == "illuminance"
    assert cfg["unit_of_measurement"] == "lx"
    assert cfg["state_topic"] == "confiture/pi3/illuminance"


class FakeSMBus:
    def __init__(self, block=(0, 0, 0, 0), fail=False):
        self.writes, self.reads, self.block, self.fail = [], [], list(block), fail

    def write_byte_data(self, addr, reg, value):
        self.writes.append((addr, reg, value))

    def read_i2c_block_data(self, addr, reg, length):
        self.reads.append((addr, reg, length))
        if self.fail:
            raise OSError("bus error")
        return self.block


def test_sensor_powers_on_with_als_enabled():
    bus = FakeSMBus()
    Tsl2591Sensor(bus, wait=lambda _s: None)
    assert bus.writes == [(0x29, 0xA0, 0x03)]  # ENABLE: PON | AEN


def test_sensor_sets_gain_once_and_decodes_little_endian_counts():
    bus = FakeSMBus(block=(0x34, 0x12, 0x78, 0x00))
    waits = []
    sensor = Tsl2591Sensor(bus, wait=waits.append)
    assert sensor.read(428) == (0x1234, 0x78)
    sensor.read(428)
    assert bus.writes[1:] == [(0x29, 0xA1, 0x20)]  # CONTROL: high gain, 100 ms
    assert bus.reads == [(0x29, 0xB4, 4)] * 2  # C0DATAL..C1DATAH
    assert len(waits) == 3  # extra cycle skipped after the gain change only


def test_sensor_returns_none_and_rewrites_gain_after_a_bus_error():
    bus = FakeSMBus(fail=True)
    sensor = Tsl2591Sensor(bus, wait=lambda _s: None)
    assert sensor.read(25) is None
    sensor.read(25)
    assert bus.writes[1:] == [(0x29, 0xA1, 0x10)] * 2
