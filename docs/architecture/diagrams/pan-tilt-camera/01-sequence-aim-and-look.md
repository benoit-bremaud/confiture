# Sequence diagram — pan-tilt-camera — UC12 Look around remotely

> **Feature**: pan-tilt-camera (issue #3)
> **Source specs**: [`voice-assistant-use-cases.md`](../../specs/voice-assistant-use-cases.md) UC12
> **Related ADRs**: ADR-0007
> **See also**: [`02-deployment.md`](02-deployment.md)

## Context

How an aim command reaches the servos and how images come back. Home Assistant never drives
the hardware: it publishes commands on MQTT; the agent clamps, ramps and cuts the servo signal
(ADR-0007). Moves are serialised in a queue so two quick commands never fight.

## Diagram

```mermaid
---
title: sd — UC12 Aim and look
---
sequenceDiagram
  actor Adult
  participant HA as Home Assistant (Pi 5)
  participant MQ as MQTT broker (Pi 5)
  participant AG as pi3cam Agent (Pi 3)<br/>domain
  participant SV as Pca9685Servos
  participant CAM as RpicamCamera

  Note over AG,MQ: on (re)connect: status online, Discovery configs, states (retained)
  loop every 2 s, or at once when shoot_now is set
    alt camera ON
      AG->>CAM: capture(640×360)
      CAM-->>AG: JPEG
      AG-)MQ: confiture/pi3/camera
    else camera OFF (privacy)
      AG-)MQ: confiture/pi3/camera (empty)
    end
    MQ-)HA: image
  end
  Adult->>HA: move pan slider (or pick a saved position)
  HA-)MQ: confiture/pi3/pan/set "35"
  MQ-)AG: handle(topic, payload)
  alt payload is a number
    AG->>AG: queue move (pan, 35)
    AG->>SV: write_pulse(ch1, µs) every 20 ms, clamped to limits
    AG->>SV: cut(ch1) after 0.3 s
    AG-)MQ: pan/state "35" (retained), save state
    AG->>AG: shoot_now
  else malformed
    AG->>AG: ignore
  end
  opt HD photo
    Adult->>HA: press "Prendre une photo HD"
    HA-)MQ: confiture/pi3/snapshot_hd
    MQ-)AG: handle
    AG->>CAM: capture(1280×720)
    AG-)MQ: confiture/pi3/camera_hd
  end
  Note over MQ,HA: Pi 3 drops off Wi-Fi: last will "offline", entities unavailable
```

## Notes

- `-)` marks asynchronous MQTT publishes; there is no reply on the command path, the state
  topic is the acknowledgement.
- Position is commanded, not measured (no servo feedback).
