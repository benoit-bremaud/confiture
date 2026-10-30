# Sequence diagram — voice-assistant — UC1 Ask a question by voice

> **Feature**: voice-assistant (benoit-bremaud/confiture#18)
> **Source specs**: [`voice-assistant-needs.md`](../../specs/voice-assistant-needs.md) (REQ-14, REQ-15, REQ-16, REQ-20)
> **Related ADRs**: ADR-0004, ADR-0005, ADR-0006, ADR-0008
> **See also**: [`02-sequence-ask-a-question.md`](02-sequence-ask-a-question.md)

## Context

Adds the listening half to UC1: a spoken question, captured by the USB microphone on the Pi 5
(REQ-15), is turned into text by a Wyoming speech-to-text container on the Pi 5 (ADR-0008), then
follows the exchange of `02-sequence-ask-a-question.md` unchanged. The wake word is a later
brick: until then a listening turn is started by hand (one turn, then the satellite waits).

## Diagram

```mermaid
---
title: sd — UC1 Ask a question by voice — STT on the Pi 5, answer on the Nest
---
sequenceDiagram
  actor Member as Household member
  participant Sat as Voice satellite (Pi 5)<br/>USB microphone
  participant HA as Home Assistant (Pi 5)<br/>Assist pipeline "Yuki"
  participant STT as Speech-to-text (Pi 5)<br/>Wyoming, loopback
  participant Agent as Conversation agent "Yuki"
  participant Piper as Piper TTS (Pi 5)
  participant Nest as Nest Mini (Cast)

  Member->>Sat: start a listening turn (by hand, until the wake word)
  Sat->>HA: run pipeline (stage stt → tts)
  loop while the member speaks
    Member->>Sat: speech
    Sat->>HA: audio chunk (16 kHz mono PCM)
    HA->>STT: audio chunk
  end
  Note over Sat,HA: end of speech detected (silence)
  HA->>STT: audio-stop
  STT-->>HA: transcript (French)
  alt empty transcript
    Note over HA: turn ends, nothing said
  else text recognised
    HA->>Agent: conversation.process(transcript)
    Note over Agent: ref 02-sequence-ask-a-question — intents first, LLM fallback
    Agent-->>HA: reply text
    HA->>Piper: synthesize(reply text)
    Piper-->>HA: audio (WAV)
    HA->>Nest: play_media(TTS URL on HA)
    Nest-->>Member: spoken answer
  end
```

## Notes

- Audio never leaves the Pi 5 and is never stored (REQ-20: the question log keeps text only).
- STT latency (acceptance of benoit-bremaud/confiture#18, at most 3 s) runs from `audio-stop`
  to the transcript; the model is chosen by the bench, ADR-0008.
- Mermaid has no `ref` fragment: the interaction use is drawn as a note.
