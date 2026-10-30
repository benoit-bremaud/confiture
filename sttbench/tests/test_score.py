import pytest

from score import Result, Summary, normalize, summarize, word_errors


def test_normalize_ignores_case_punctuation_and_hyphens():
    assert normalize("Quelle heure est-il ?") == ["quelle", "heure", "est", "il"]


def test_normalize_splits_elisions():
    assert normalize("C’est l'heure") == ["c", "est", "l", "heure"]


def test_normalize_spells_small_numbers():
    assert normalize("7 fois 8, 17 et 42") == normalize(
        "sept fois huit, dix-sept et 42"
    )


@pytest.mark.parametrize(
    ("hypothesis", "expected"),
    [
        ("il fait beau", (0, 3)),
        ("il fait chaud", (1, 3)),
        ("il beau", (1, 3)),
        ("il fait très beau", (1, 3)),
        ("beau fait il", (2, 3)),
        ("", (3, 3)),
    ],
)
def test_word_errors(hypothesis, expected):
    assert word_errors("il fait beau", hypothesis) == expected


def test_summarize_rates_child_over_the_full_set_and_latency():
    results = [Result("child", "bonjour Yuki", "bonjour Yuki", 1.0)] * 8 + [
        Result("child", "bonjour Yuki", "bonjour", 2.0),
        Result("adult", "il pleut", "il pleut", 2.5),
    ]
    summary = summarize(results)
    assert summary.wer == 1 / 20
    assert summary.child_correct_ratio == 0.8
    assert summary.max_latency_s == 2.5


def test_summarize_partial_child_set_cannot_pass():
    results = [Result("child", "bonjour", "bonjour", 1.0)] * 4
    assert summarize(results).child_correct_ratio == 0.4
    assert not summarize(results).passes


def test_summarize_empty_is_zero():
    assert summarize([]) == Summary(0.0, 0.0, 0.0)


def test_passes_on_thresholds():
    assert Summary(0.1, 0.8, 3.0).passes
    assert not Summary(0.1, 0.7, 1.0).passes
    assert not Summary(0.1, 1.0, 3.1).passes
