# Use case diagram — voice-assistant — who wants what

> **Feature**: voice-assistant (epic issue to be created)
> **Source specs**: [`voice-assistant-use-cases.md`](../../specs/voice-assistant-use-cases.md)
> **Related ADRs**: ADR-0001
> **See also**: `02-sequence-*.md`, `03-component.md`, `08-deployment.md` (next phase)

## Context

Phase 0 view of confiture: the goals people pursue with a fully local home voice assistant.
It does not show how the system is split (satellite / brain / sensor nodes) — that is the
component and deployment diagrams' job.

## Diagram

```mermaid
---
title: uc — confiture — voice assistant
---
flowchart LR
  Household["👤 Household member"]
  Maintainer["👤 Maintainer"]
  HomeDevice["«actor» Home device"]
  WeatherSvc["«actor» Weather service"]
  MusicSrc["«actor» Music source"]

  subgraph SUBJECT ["confiture"]
    subgraph Voice ["Voice interaction domain"]
      UC1(["UC1 Ask a question"])
      UC2(["UC2 Control a home device"])
      UC3(["UC3 Check a room's conditions"])
      UC4(["UC4 Set a timer or reminder"])
      UC5(["UC5 Wake the assistant"])
      UC10(["UC10 Check the weather"])
      UC11(["UC11 Play music"])
    end
    subgraph Privacy ["Privacy domain"]
      UC6(["UC6 Mute the microphones"])
    end
    subgraph Admin ["Administration domain"]
      UC7(["UC7 Train a custom wake word"])
      UC8(["UC8 Enrol a node"])
      UC9(["UC9 Check node health"])
    end
  end

  Household --- UC1
  Household --- UC2
  Household --- UC3
  Household --- UC4
  Household --- UC6
  Household --- UC10
  Household --- UC11
  UC2 --- HomeDevice
  UC10 --- WeatherSvc
  UC11 --- MusicSrc
  Maintainer --- UC7
  Maintainer --- UC8
  Maintainer --- UC9

  UC1 -.->|"«include»"| UC5
  UC2 -.->|"«include»"| UC5
  UC3 -.->|"«include»"| UC5
  UC4 -.->|"«include»"| UC5
  UC10 -.->|"«include»"| UC5
  UC11 -.->|"«include»"| UC5
```

## Notes

- **UC5 Wake the assistant** is a subfunction (🐟): every spoken goal starts with the wake word,
  so it is shared by UC1–UC4, UC10 and UC11 through «include». It is never a goal on its own.
- The timer firing is **not** a use case (system event): it is the success guarantee of UC4.
- Room sensors (the two Pi 1 boards) are **inside** the subject: they are part of confiture, not
  actors. External systems: *Home device* (lights, plugs…), *Weather service* and *Music source*
  (streaming service or local library — to choose in phase 1).
- `Maintainer` is a role, today played by the owner; a household member may also play it.
- Internet is allowed for online services, voice stays local (ADR-0001).
