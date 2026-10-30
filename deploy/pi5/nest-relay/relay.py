"""Speak Yuki's spoken replies on the Nest Mini (benoit-bremaud/confiture#18, #25, ADR-0008).

The Pi 5 satellite has no speaker, and an Assist pipeline returns its audio to the satellite
only. The satellite announces each reply as a `tts_text` event; the relay hands the text to
the Home Assistant script `yuki_speak`, which speaks it on the Nest with Piper.

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
    text = text.strip() or None if isinstance(text, str) else None
    return event["event"], text


def reply_text(message: str) -> str | None:
    """The reply carried by a satellite event, or None for any other event."""
    parsed = parse_event(message)
    if parsed is None or parsed[0] != "tts_text":
        return None
    return parsed[1]


class Turn:
    """One question's lifecycle; pure, the caller passes the time (seconds, monotonic).

    `on_message` and `tick` return the sentences to speak, in order.
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
                return []  # late reply after the fallback
            self._started_at = None
            return [text]
        if name == "pipeline_error" and self._started_at is not None:
            return self._give_up()
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
