import json

from relay import (
    CUE_AFTER_S,
    FALLBACK,
    GIVE_UP_AFTER_S,
    THINKING_CUE,
    Turn,
    parse_event,
)


def event(name: str, data: object = None) -> str:
    return json.dumps(
        {"event": name, "data": data} if data is not None else {"event": name}
    )


def reply(text: str) -> str:
    return event("tts_text", {"text": text})


def test_parse_event_reads_name_and_stripped_text():
    assert parse_event(reply(" Il est 10:49 ")) == ("tts_text", "Il est 10:49")
    assert parse_event(event("idle")) == ("idle", None)


def test_parse_event_rejects_malformed_messages():
    assert parse_event("not json") is None
    assert parse_event(json.dumps(["tts_text"])) is None
    assert parse_event(json.dumps({"event": 3})) is None
    assert parse_event(event("tts_text", "text")) == ("tts_text", None)
    assert parse_event(event("tts_text", {"text": 42})) == ("tts_text", None)
    assert parse_event(reply("   ")) == ("tts_text", None)


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
    assert turn.tick(CUE_AFTER_S) == [THINKING_CUE]
    assert turn.tick(GIVE_UP_AFTER_S - 0.1) == []
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


def test_late_tick_jumps_straight_to_the_fallback():
    turn = Turn()
    turn.on_message(event("thinking"), 0.0)
    assert turn.tick(GIVE_UP_AFTER_S + 5) == [FALLBACK]


def test_pipeline_error_after_the_cue_speaks_the_fallback():
    turn = Turn()
    turn.on_message(event("thinking"), 0.0)
    turn.tick(CUE_AFTER_S)
    assert turn.on_message(event("pipeline_error"), 5.0) == [FALLBACK]


def test_end_of_run_reopens_after_a_fallback():
    turn = Turn()
    turn.on_message(event("thinking"), 0.0)
    turn.tick(GIVE_UP_AFTER_S)
    turn.on_message(event("idle"), 16.0)
    assert turn.on_message(reply("Minuteur terminé"), 60.0) == ["Minuteur terminé"]
    assert turn.tick(80.0) == []


def test_second_thinking_restarts_the_turn():
    turn = Turn()
    turn.on_message(event("thinking"), 0.0)
    turn.tick(CUE_AFTER_S)
    turn.on_message(event("thinking"), 10.0)
    assert turn.tick(10.0 + CUE_AFTER_S) == [THINKING_CUE]


def test_reply_after_an_error_fallback_is_spoken():
    turn = Turn()
    turn.on_message(event("thinking"), 0.0)
    turn.on_message(event("pipeline_error"), 0.1)
    assert turn.on_message(reply("Minuteur terminé"), 30.0) == ["Minuteur terminé"]


def test_only_the_one_late_reply_is_dropped():
    turn = Turn()
    turn.on_message(event("thinking"), 0.0)
    turn.tick(GIVE_UP_AFTER_S)
    assert turn.on_message(reply("trop tard"), 20.0) == []
    assert turn.on_message(reply("Minuteur terminé"), 60.0) == ["Minuteur terminé"]
