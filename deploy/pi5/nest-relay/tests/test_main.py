from main import speak_all


class FlakySpeaker:
    """Fails on the texts it is told to, records the others."""

    def __init__(self, failures: dict[str, Exception]) -> None:
        self.failures = failures
        self.spoken: list[str] = []

    def speak(self, text: str) -> None:
        if text in self.failures:
            raise self.failures[text]
        self.spoken.append(text)


def test_speak_all_speaks_in_order():
    speaker = FlakySpeaker({})
    speak_all(["cue", "reply"], speaker)
    assert speaker.spoken == ["cue", "reply"]


def test_speak_all_keeps_going_when_home_assistant_fails():
    speaker = FlakySpeaker({"cue": OSError("down"), "reply": ValueError("bug")})
    speak_all(["cue", "reply", "next"], speaker)
    assert speaker.spoken == ["next"]
