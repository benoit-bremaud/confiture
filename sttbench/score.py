"""Scoring for the speech-to-text bench (benoit-bremaud/confiture#18, ADR-0008).

Pure functions: no audio, no network, so the selection rule is unit tested.
"""

import re
import unicodedata
from dataclasses import dataclass

# Acceptance of #18: at least 8/10 correct child transcriptions, STT latency of 3 s or less.
MIN_CHILD_CORRECT_RATIO = 0.8
MAX_LATENCY_S = 3.0
# The ratio is taken over the whole child set, so a half-recorded bench cannot pass.
CHILD_SENTENCES = 10

# Models write small numbers either way ("sept" or "7"); compare words, not spellings.
NUMBERS = dict(
    enumerate(
        "zéro un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze "
        "quinze seize dix-sept dix-huit dix-neuf vingt".split()
    )
)


def normalize(text: str) -> list[str]:
    """Lower-case words without punctuation, elisions split and numbers 0-20 spelt out."""
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"\d+", lambda m: NUMBERS.get(int(m[0]), m[0]), text)
    return re.findall(r"\w+", re.sub(r"[-'’]", " ", text))


def word_errors(reference: str, hypothesis: str) -> tuple[int, int]:
    """(edit distance in words, reference length): the numerator and denominator of WER."""
    ref, hyp = normalize(reference), normalize(hypothesis)
    row = list(range(len(hyp) + 1))
    for i, ref_word in enumerate(ref, 1):
        previous, row[0] = row[0], i
        for j, hyp_word in enumerate(hyp, 1):
            previous, row[j] = (
                row[j],
                min(row[j] + 1, row[j - 1] + 1, previous + (ref_word != hyp_word)),
            )
    return row[-1], len(ref)


@dataclass(frozen=True)
class Result:
    """One transcribed sentence; correct means no word error after normalisation."""

    speaker: str  # "adult" or "child"
    reference: str
    transcript: str
    latency_s: float

    @property
    def correct(self) -> bool:
        return word_errors(self.reference, self.transcript)[0] == 0


@dataclass(frozen=True)
class Summary:
    """Bench outcome of one model; child_correct_ratio is over CHILD_SENTENCES, 0.0 if none."""

    wer: float
    child_correct_ratio: float
    max_latency_s: float

    @property
    def passes(self) -> bool:
        return (
            self.child_correct_ratio >= MIN_CHILD_CORRECT_RATIO
            and self.max_latency_s <= MAX_LATENCY_S
        )


def summarize(results: list[Result]) -> Summary:
    """Corpus WER (summed errors over summed reference words), child ratio, worst latency."""
    errors = total = 0
    for result in results:
        e, n = word_errors(result.reference, result.transcript)
        errors, total = errors + e, total + n
    child = [r for r in results if r.speaker == "child"]
    return Summary(
        wer=errors / total if total else 0.0,
        child_correct_ratio=sum(r.correct for r in child)
        / max(len(child), CHILD_SENTENCES),
        max_latency_s=max((r.latency_s for r in results), default=0.0),
    )
