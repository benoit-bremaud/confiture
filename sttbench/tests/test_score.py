from score import Result, Summary, normalize, smallest_passing, summarize, word_errors


def test_normalize_ignores_case_punctuation_and_hyphens():
    assert normalize("Quelle heure est-il ?") == normalize("quelle heure est il")


def test_normalize_unifies_apostrophes():
    assert normalize("C’est l’heure") == ["c'est", "l'heure"]


def test_word_errors_counts_substitution_insertion_deletion():
    assert word_errors("il fait beau", "il fait beau") == (0, 3)
    assert word_errors("il fait beau", "il fait chaud") == (1, 3)
    assert word_errors("il fait beau", "il beau") == (1, 3)
    assert word_errors("il fait beau", "il fait très beau") == (1, 3)


def test_summarize_rates_child_and_latency():
    results = [
        Result("child", "bonjour Yuki", "bonjour Yuki", 1.0),
        Result("child", "bonjour Yuki", "bonjour", 2.0),
        Result("adult", "il pleut", "il pleut", 2.5),
    ]
    summary = summarize(results)
    assert summary.wer == 1 / 6
    assert summary.child_correct_ratio == 0.5
    assert summary.max_latency_s == 2.5


def test_summarize_empty_is_zero():
    assert summarize([]) == Summary(0.0, 0.0, 0.0)


def test_passes_on_thresholds():
    assert Summary(0.1, 0.8, 3.0).passes
    assert not Summary(0.1, 0.7, 1.0).passes
    assert not Summary(0.1, 1.0, 3.1).passes


def test_smallest_passing_picks_first_in_order():
    summaries = {
        "tiny": Summary(0.3, 0.5, 0.8),
        "base": Summary(0.1, 0.9, 1.5),
        "small": Summary(0.05, 1.0, 2.9),
    }
    assert smallest_passing(summaries, ["tiny", "base", "small"]) == "base"
    assert smallest_passing({"tiny": summaries["tiny"]}, ["tiny"]) is None
