import json

from relay import (
    CUE_AFTER_S,
    FALLBACK,
    GIVE_UP_AFTER_S,
    THINKING_CUE,
    Turn,
    reply_text,
)


def event(name: str, data: object = None) -> str:
    return json.dumps(
        {"event": name, "data": data} if data is not None else {"event": name}
    )


def reply(text: str) -> str:
    return event("tts_text", {"text": text})


def test_reply_text_reads_tts_text():
    assert reply_text(reply(" Il est 10:49 ")) == "Il est 10:49"


def test_reply_text_ignores_other_events():
    assert reply_text(event("stt_text", {"text": "Quelle heure est-il ?"})) is None
    assert reply_text(event("idle")) is None


def test_reply_text_ignores_malformed_messages():
    assert reply_text("not json") is None
    assert reply_text(json.dumps(["tts_text"])) is None
    assert reply_text(json.dumps({"event": 3})) is None
    assert reply_text(event("tts_text", "text")) is None
    assert reply_text(event("tts_text", {"text": 42})) is None
    assert reply_text(reply("   ")) is None


def test_fast_reply_is_spoken_without_cue():
    turn = Turn()
    assert turn.on_message(event("thinking"), 0.0) == []
    assert turn.on_message(reply("Il est 10:49"), 0.3) == ["Il est 10:49"]
    assert turn.tick(GIVE_UP_AFTER_S + 1) == []


def test_slow_reply_gets_the_cue_once_then_the_reply():
    turn = Turn()
    turn.on_message(event("thinking"), 10.0)
    assert turn.tick(10.0 + CUE_AFTER_S - 0.1) == []
    assert turn.tick(10.0 + CUE_AFTER_S) == [THINKING_CUE]
    assert turn.tick(10.0 + CUE_AFTER_S + 1) == []
    assert turn.on_message(reply("Le ciel est bleu."), 18.0) == ["Le ciel est bleu."]
    assert turn.tick(10.0 + GIVE_UP_AFTER_S + 1) == []


def test_no_reply_gives_up_and_drops_the_late_reply():
    turn = Turn()
    turn.on_message(event("thinking"), 0.0)
    turn.tick(CUE_AFTER_S)
    assert turn.tick(GIVE_UP_AFTER_S) == [FALLBACK]
    assert turn.tick(GIVE_UP_AFTER_S + 1) == []
    assert turn.on_message(reply("trop tard"), 20.0) == []


def test_pipeline_error_during_the_turn_speaks_the_fallback_once():
    turn = Turn()
    turn.on_message(event("thinking"), 0.0)
    assert turn.on_message(event("pipeline_error"), 0.1) == [FALLBACK]
    assert turn.on_message(event("pipeline_error"), 0.2) == []
    assert turn.tick(CUE_AFTER_S) == []


def test_pipeline_error_outside_a_turn_stays_silent():
    turn = Turn()
    assert turn.on_message(event("pipeline_error"), 0.0) == []
    turn.on_message(event("thinking"), 1.0)
    turn.on_message(reply("Il est 10:49"), 1.2)
    assert turn.on_message(event("pipeline_error"), 1.5) == []


def test_next_turn_reopens_after_a_fallback():
    turn = Turn()
    turn.on_message(event("thinking"), 0.0)
    turn.on_message(event("pipeline_error"), 0.1)
    turn.on_message(event("thinking"), 30.0)
    assert turn.on_message(reply("Bonjour"), 30.5) == ["Bonjour"]


def test_reply_without_thinking_is_still_spoken():
    assert Turn().on_message(reply("Minuteur terminé"), 0.0) == ["Minuteur terminé"]


def test_malformed_and_other_events_are_ignored():
    turn = Turn()
    assert turn.on_message("not json", 0.0) == []
    assert turn.on_message(event("idle"), 0.0) == []
