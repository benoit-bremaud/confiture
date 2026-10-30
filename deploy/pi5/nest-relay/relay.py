"""Speak Yuki's spoken replies on the Nest Mini (benoit-bremaud/confiture#18, ADR-0008).

The Pi 5 satellite has no speaker, and an Assist pipeline returns its audio to the satellite
only. The satellite announces each reply as a `tts_text` event; the relay hands the text to
the Home Assistant script `yuki_speak`, which speaks it on the Nest with Piper.
"""

import json
from typing import Protocol


class Speaker(Protocol):
    """Port: anything that can speak a reply (Home Assistant in production, a fake in tests)."""

    def speak(self, text: str) -> None: ...


def reply_text(message: str) -> str | None:
    """The reply carried by a satellite event, or None for any other event."""
    try:
        event = json.loads(message)
    except ValueError:
        return None
    if not isinstance(event, dict) or event.get("event") != "tts_text":
        return None
    data = event.get("data")
    text = data.get("text") if isinstance(data, dict) else None
    if not isinstance(text, str):
        return None
    return text.strip() or None


def relay(message: str, speaker: Speaker) -> bool:
    """Speak the reply carried by `message`, if any; True when something was spoken."""
    text = reply_text(message)
    if text is None:
        return False
    speaker.speak(text)
    return True
