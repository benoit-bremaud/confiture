"""Speak Yuki's spoken replies on the Nest Mini (benoit-bremaud/confiture#18, #25, ADR-0008).

The Pi 5 satellite has no speaker, and an Assist pipeline returns its audio to the satellite
only. The satellite announces each reply as a `tts_text` event; `Turn` decides what to speak
and `main` hands each text to the Home Assistant script `yuki_speak` (Nest, Piper).

On the slow LLM path the relay also speaks a thinking cue, and a friendly fallback when the
run fails or never answers (05-sequence-thinking-cue-and-fallback.md, NFR-5, ADR-0004).
"""

import json
from typing import Protocol

THINKING_CUE = "Hmm, je réfléchis…"
FALLBACK = "Je n'arrive pas à réfléchir pour l'instant, réessaie un peu plus tard."
CUE_AFTER_S = 2.0
GIVE_UP_AFTER_S = 15.0


class Speaker(Protocol):
    """Port: anything that can speak a reply (Home Assistant in production, a fake in tests)."""

    def speak(self, text: str) -> None: ...


def parse_event(message: str) -> tuple[str, str | None] | None:
    """(event name, stripped text or None) of a satellite message, or None if malformed."""
    try:
        event = json.loads(message)
    except ValueError:
        return None
    if not isinstance(event, dict) or not isinstance(event.get("event"), str):
        return None
    data = event.get("data")
    text = data.get("text") if isinstance(data, dict) else None
    if isinstance(text, str):
        text = text.strip() or None
    else:
        text = None
    return event["event"], text


class Turn:
    """Tracks the current question's lifecycle; pure, the caller passes the time (seconds, monotonic).

    `thinking` (the satellite's intent start) opens a turn, resetting any turn in progress;
    `idle` (end of the run) clears it. `on_message` and `tick` return the texts to speak.
    """

    def __init__(self) -> None:
        self._started_at: float | None = None
        self._cue_spoken = False
        self._closed = False

    def on_message(self, message: str, now: float) -> list[str]:
        """Handle one satellite message."""
        parsed = parse_event(message)
        if parsed is None:
            return []
        name, text = parsed
        if name == "thinking":
            self._started_at, self._cue_spoken, self._closed = now, False, False
            return []
        if name == "tts_text" and text is not None:
            if self._closed:
                self._closed = False
                return []  # the one late reply of the abandoned turn
            self._started_at = None
            return [text]
        if name == "idle":
            self._started_at, self._closed = None, False
            return []
        if name == "pipeline_error" and self._started_at is not None:
            self._started_at = None  # the run ended: no late reply will come
            return [FALLBACK]
        return []

    def tick(self, now: float) -> list[str]:
        """Speak the cue or the fallback when their deadline has passed."""
        if self._started_at is None:
            return []
        elapsed = now - self._started_at
        if elapsed >= GIVE_UP_AFTER_S:
            return self._give_up()
        if elapsed >= CUE_AFTER_S and not self._cue_spoken:
            self._cue_spoken = True
            return [THINKING_CUE]
        return []

    def _give_up(self) -> list[str]:
        self._started_at, self._closed = None, True
        return [FALLBACK]
