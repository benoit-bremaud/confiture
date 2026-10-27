# voice-assistant — use case specifications

Textual specifications of [`01-use-case.md`](../diagrams/voice-assistant/01-use-case.md)
(Cockburn). Fully dressed for non-trivial cases, one-line briefs otherwise.

## Non-functional requirements

- **NFR-1 — Voice stays local**: no audio and no full transcript leaves the home network; only
  the minimal query an online service needs (e.g. a city for the weather, a track name) may go
  out (ADR-0001).
- **NFR-2 — Responsiveness**: for a known command (local intent, REQ-2) the spoken answer
  starts within 3 s of the end of the request; the LLM path's target is open (Q7).
  Estimates, to be measured on real hardware.
- **NFR-3 — Wake reliability**: at most one false wake per day in normal household noise
  (estimate, to be measured).
- **NFR-4 — Recycled hardware**: runs on the existing Raspberry Pi 1 ×2 and Pi 3; only the
  brain may need a more powerful machine.

## UC1 — Ask a question   (status: planned)

- **Level**: user goal
- **Primary actor**: Household member
- **Stakeholders & interests**: Household member — a useful spoken answer; everyone at home —
  their voice is not recorded or sent outside (NFR-1).
- **Preconditions**: the satellite is running and not muted.
- **Minimal guarantee**: no audio is stored or leaves the home network.
- **Success guarantee**: the member hears an answer to the question.
- **Trigger**: the member says the wake word.

**Main success scenario**
1. Household member wakes the assistant (UC5).
2. Household member asks a question.
3. System transcribes the question.
4. System produces an answer.
5. System speaks the answer.

**Extensions**
- 3a. Speech is not understood:
  - 3a1. System asks the member to repeat; resumes at step 2 (once), then ends in failure.
- 4a. The question cannot be answered locally:
  - 4a1. System queries an online source with the minimal query (NFR-1); resumes at step 5.
  - 4a2. No online answer either: System says it does not know; use case ends.
- *a. At any time, the member says "stop": System stops speaking; use case ends.

**Relationships**: includes UC5.
**Business rules / NFR**: NFR-1, NFR-2.

## UC2 — Control a home device   (status: planned)

- **Level**: user goal
- **Primary actor**: Adult · **Supporting actor**: Home device
- **Stakeholders & interests**: Household member — the device does what was asked;
  household — no unintended action.
- **Preconditions**: the target device is known to the system.
- **Minimal guarantee**: a device is never actuated on an ambiguous command.
- **Success guarantee**: the device is in the requested state and the system confirms it.
- **Trigger**: the member says the wake word.

**Main success scenario**
1. Household member wakes the assistant (UC5).
2. Household member states the command (device + action).
3. System identifies the device and the action.
4. System sends the action to the Home device.
5. Home device reports its new state.
6. System confirms aloud.

**Extensions**
- 3a. Device or action is ambiguous:
  - 3a1. System asks which device; resumes at step 3.
- 5a. Home device does not respond:
  - 5a1. System reports the failure aloud; use case ends in failure.

**Relationships**: includes UC5.
**Business rules / NFR**: NFR-1, NFR-2.

## UC3 — Check a room's conditions   (status: planned)

Brief: the member asks for a room's temperature or humidity; the system reads the latest
measurement from that room's sensor node and speaks it, or says the sensor is unavailable.
Includes UC5. NFR-1, NFR-4.

## UC4 — Set a timer or reminder   (status: planned)

Brief: the member asks for a timer or a reminder; the system confirms it and later plays it on
the satellite where it was set. Includes UC5. NFR-1.

## UC10 — Check the weather   (status: planned)

Brief: the member asks for the weather (today, tomorrow, a place); the system queries the
Weather service with only the place and date, and speaks the forecast; if the service is
unreachable it says so. Includes UC5. Supporting actor: Weather service. NFR-1, NFR-2.

## UC11 — Play music   (status: planned)

Brief: the member asks for an artist, a track, a playlist or a radio; the system finds it on
the Music source and plays it on the satellite where it was asked. Extensions: nothing found —
the system says so; "pause", "next", "louder" while playing — the system adjusts playback;
the wake word still works during playback. Includes UC5. Supporting actor: Music source. NFR-1.

## UC5 — Wake the assistant   (subfunction)

Brief: the member says the wake word; the satellite detects it and signals it is listening
(sound or LED). Extension: no request follows within a few seconds — the satellite goes back
to waiting. NFR-3.

## UC6 — Mute the microphones   (status: planned)

Brief: the member mutes a satellite (button or voice); the satellite stops listening, shows a
visible muted state, and listens again only when unmuted. NFR-1.

## UC7 — Train a custom wake word   (status: planned)

Brief: the maintainer chooses the assistant's name, trains a wake-word model for it, tests it
against recorded household noise and deploys it to the satellites. NFR-3.

## UC8 — Enrol a node   (status: planned)

Brief: the maintainer prepares a recycled Pi (flash, configure, join the network) and registers
it as a satellite or a sensor node; the system then lists it as available. NFR-4.

## UC9 — Check node health   (status: planned)

Brief: the maintainer consults the state of every node (online, temperature, under-voltage,
storage) and identifies the one needing attention. NFR-4.
