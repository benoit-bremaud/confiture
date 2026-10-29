# Deployment diagram — pan-tilt-camera — iteration 1

> **Feature**: pan-tilt-camera (issue #3)
> **Source specs**: [`voice-assistant-needs.md`](../../specs/voice-assistant-needs.md) REQ-13
> **Related ADRs**: ADR-0007
> **See also**: [`01-sequence-aim-and-look.md`](01-sequence-aim-and-look.md)

## Context

Where the camera agent runs and what it talks to. The Pi 3 opens no port: it only connects out
to the broker on the Pi 5.

## Diagram

```mermaid
---
title: Deployment — pan-tilt camera iteration 1
---
flowchart LR
  subgraph PI3["«device» Raspberry Pi 3 B"]
    AGENT["«execution environment» Python venv ~/pi3cam<br/>«artifact» main.py, domain.py, adapters.py<br/>started by crontab @reboot → run.sh"]
    CONF["«artifact» ~/.config/pi3cam (mode 600)<br/>broker, MQTT user and password,<br/>state.json, presets.json"]
    HAT["«device» Waveshare Pan-Tilt HAT<br/>PCA9685 @0x40, 2 servos,<br/>TSL25911 light sensor @0x29"]
    CAMERA["«device» Camera Module 3"]
  end
  subgraph PI5["«device» Raspberry Pi 5 (Docker)"]
    BROKER["«container» MQTT broker"]
    HA["«container» homeassistant<br/>MQTT integration, Discovery"]
  end

  AGENT -- "file read/write" --> CONF
  AGENT -- "I²C bus 1" --> HAT
  AGENT -- "rpicam-still / CSI" --> CAMERA
  AGENT -- "MQTT / TCP, Wi-Fi LAN, user + password, last will" --> BROKER
  HA -- "MQTT" --> BROKER
```

## Notes

- Secrets stay on the Pi in `~/.config/pi3cam`, never in the repository.
- Crontab instead of systemd: set up without sudo; `run.sh` restarts the agent if it exits.
