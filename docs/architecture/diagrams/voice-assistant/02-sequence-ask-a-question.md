# Sequence diagram — voice-assistant — UC1 Ask a question

> **Feature**: voice-assistant (epic issue to be created)
> **Source specs**: [`voice-assistant-use-cases.md`](../../specs/voice-assistant-use-cases.md)
> **Related ADRs**: ADR-0004, ADR-0005, ADR-0006
> **See also**: [`01-use-case.md`](01-use-case.md)

## Context

How a free question reaches the local LLM, and what happens when the LLM host is down. Known
commands never leave the Pi 5 (ADR-0004); the LLM never leaves the home (ADR-0005). Shown with
text input; the reply is then spoken on the Nest Mini by Piper (ADR-0006, REQ-12, REQ-16).
An Assist pipeline returns its audio to the caller only, so until the Pi 5 satellite exists
the script `yuki_say` glues the agent to the Nest (owner choice, MCDA 415). Wake word and
speech-to-text will wrap the same exchange later.

## Diagram

```mermaid
---
title: sd — UC1 Ask a question — local intents first, LLM fallback
---
sequenceDiagram
  actor Member as Household member
  participant HA as Home Assistant (Pi 5)<br/>conversation agent "Yuki"
  participant Intents as Built-in intents (Pi 5)
  participant LLM as Ollama "yuki" (ProBook)
  participant Piper as Piper TTS (Pi 5)<br/>Wyoming, loopback
  participant Nest as Nest Mini<br/>(Cast)

  Member->>HA: run script yuki_say(sentence)<br/>(text; later the satellite, speech)
  HA->>HA: conversation.process(agent Yuki)
  HA->>Intents: match sentence
  alt known command
    Intents-->>HA: intent handled
    Note over HA: reply text = confirmation
  else no intent matches
    HA->>LLM: chat(sentence, French system prompt)
    alt ProBook up
      LLM-->>HA: short French answer
      Note over HA: reply text = answer
    else ProBook down or timeout
      LLM--xHA: no answer
      Note over HA: reply text = error message (to make friendly)
    end
  end
  HA->>Piper: tts.speak → synthesize(reply text, French voice)
  Piper-->>HA: audio (WAV)
  HA->>Nest: play_media(TTS URL on HA)
  Nest->>HA: GET audio
  HA-->>Nest: audio
  Nest-->>Member: spoken answer
```

## Notes

- "Prefer handling commands locally" on the Yuki agent is what gives the first `alt`: the LLM
  only sees sentences no intent matches.
- The LLM gets no control of home devices (Ollama "control Home Assistant" off), so a wrong
  answer can never act on the house.
- Time to first audio (NFR-2, NFR-5) runs from the sentence to the Nest starting to play:
  it includes Piper synthesis and the Cast fetch, measured in ADR-0006.
- The friendly "I can't think right now" message of ADR-0004 is not yet built: today the
  down-host branch returns Home Assistant's own error.
