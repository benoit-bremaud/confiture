#!/usr/bin/env python3
"""Pi 3 Pan-Tilt camera agent entry point: wires the adapters to the domain (confiture#3)."""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Callable

import paho.mqtt.client as mqtt
from smbus2 import SMBus

from adapters import JsonStore, MqttBus, Pca9685Servos, RpicamCamera, Tsl2591Sensor
from domain import BASE, INTERVAL, LIGHT_PERIOD, SUBSCRIPTIONS, Agent, LightMeter

# Local, never committed (mode 600): broker host, MQTT user, MQTT password — one per file.
CONF = Path.home() / ".config/pi3cam"
log = logging.getLogger("pi3cam")


def run_in_thread(task: Callable[[], None]) -> None:
    """Run a task on a daemon thread (dies with the agent)."""
    threading.Thread(target=task, daemon=True).start()


def main() -> None:
    """Wire the adapters, then run the mover thread and the capture loop forever.

    Subscribing inside on_connect re-subscribes after every reconnection; the last will
    makes HA mark the entities unavailable when the Pi drops off the network.
    """
    os.umask(0o077)  # cron does not inherit the install shell's umask
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
    # Own bus handle: smbus2 keeps the slave address per handle, so two threads
    # sharing one could talk to the wrong chip.
    light = LightMeter(Tsl2591Sensor(SMBus(1)), MqttBus(client))

    def on_connect(c, *_):
        agent.on_connect()
        c.subscribe([(t, 0) for t in SUBSCRIPTIONS])

    def on_message(_c, _u, msg):
        # A bad command must never kill paho's network thread.
        try:
            agent.handle(msg.topic, msg.payload.decode(errors="replace"))
        except Exception:
            log.exception("command on %s failed", msg.topic)

    client.username_pw_set(user, password)
    client.will_set(f"{BASE}/status", "offline", retain=True)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect_async(broker)
    client.loop_start()

    def mover():
        while True:
            try:
                agent.next_move()
            except Exception:
                log.exception("move failed")

    def light_loop():
        while True:
            try:
                light.report()
            except Exception:
                log.exception("light reading failed")
            time.sleep(LIGHT_PERIOD)

    run_in_thread(mover)
    run_in_thread(light_loop)
    while True:
        agent.shoot()
        agent.wait_for_shot(INTERVAL)


if __name__ == "__main__":
    main()
