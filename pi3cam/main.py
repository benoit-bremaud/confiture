#!/usr/bin/env python3
"""Pi 3 Pan-Tilt camera agent entry point: wires the adapters to the domain (confiture#3)."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable

import paho.mqtt.client as mqtt
from smbus2 import SMBus

from adapters import JsonStore, MqttBus, Pca9685Servos, RpicamCamera
from domain import BASE, INTERVAL, SUBSCRIPTIONS, Agent

# Local, never committed (mode 600): broker host, MQTT user, MQTT password — one per file.
CONF = Path.home() / ".config/pi3cam"


def run_in_thread(task: Callable[[], None]) -> None:
    threading.Thread(target=task, daemon=True).start()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    broker, user, password = (
        (CONF / f).read_text().strip()
        for f in ("mqtt-broker", "mqtt-user", "mqtt-password")
    )
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pi3-camera")
    agent = Agent(
        Pca9685Servos(SMBus(1)),
        RpicamCamera(),
        MqttBus(client),
        JsonStore(CONF),
        sleep=time.sleep,
        run_later=run_in_thread,
    )

    def on_connect(c, *_):
        agent.on_connect()
        c.subscribe([(t, 0) for t in SUBSCRIPTIONS])

    client.username_pw_set(user, password)
    client.will_set(f"{BASE}/status", "offline", retain=True)
    client.on_connect = on_connect
    client.on_message = lambda _c, _u, msg: agent.handle(
        msg.topic, msg.payload.decode()
    )
    client.connect_async(broker)
    client.loop_start()

    def mover():
        while True:
            agent.next_move()

    run_in_thread(mover)
    while True:
        agent.shoot()
        agent.shoot_now.wait(INTERVAL)
        agent.shoot_now.clear()


if __name__ == "__main__":
    main()
