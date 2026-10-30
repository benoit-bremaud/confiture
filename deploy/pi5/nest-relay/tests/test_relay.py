import json

from relay import relay, reply_text


class FakeSpeaker:
    def __init__(self) -> None:
        self.spoken: list[str] = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)


def event(name: str, data: object = None) -> str:
    return json.dumps(
        {"event": name, "data": data} if data is not None else {"event": name}
    )


def test_reply_text_reads_tts_text():
    assert reply_text(event("tts_text", {"text": " Il est 10:49 "})) == "Il est 10:49"


def test_reply_text_ignores_other_events():
    assert reply_text(event("stt_text", {"text": "Quelle heure est-il ?"})) is None
    assert reply_text(event("idle")) is None


def test_reply_text_ignores_malformed_messages():
    assert reply_text("not json") is None
    assert reply_text(json.dumps(["tts_text"])) is None
    assert reply_text(event("tts_text", "text")) is None
    assert reply_text(event("tts_text", {"text": 42})) is None
    assert reply_text(event("tts_text", {"text": "   "})) is None


def test_relay_speaks_replies_only():
    speaker = FakeSpeaker()
    assert relay(event("tts_text", {"text": "Bonjour"}), speaker)
    assert not relay(event("thinking"), speaker)
    assert speaker.spoken == ["Bonjour"]
