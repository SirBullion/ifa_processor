"""Tonal entry states and recoverable-input correction for IFÁ v4.5."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum


class EntryState(str, Enum):
    KO_WOLE_INPUT = "KO_WOLE_INPUT"
    O_WOLE_ACCEPTED = "O_WOLE_ACCEPTED"
    OLE_WOLE_ASE = "OLE_WOLE_ASE"
    OLE_WOLE_ATUNSE = "OLE_WOLE_ATUNSE"
    KO_WOLE_REJECTED = "KO_WOLE_REJECTED"


ENTRY_TEXT = {
    EntryState.KO_WOLE_INPUT: "KỌ WỌLÉ",
    EntryState.O_WOLE_ACCEPTED: "Ó WỌLÉ",
    EntryState.OLE_WOLE_ASE: "Ó LÈ WỌLÉ — ÀṢẸ",
    EntryState.OLE_WOLE_ATUNSE: "Ó LÈ WỌLÉ — ÀTÚNṢE",
    EntryState.KO_WOLE_REJECTED: "KÒ WỌLÉ",
}


def entry_text(state: EntryState) -> str:
    return ENTRY_TEXT[state]


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    unmarked = "".join(character for character in decomposed if not unicodedata.combining(character))
    return " ".join(re.findall(r"[A-Z0-9]+", unmarked.upper()))


def first_primes(count: int) -> list[int]:
    if count < 1:
        return []
    primes: list[int] = []
    candidate = 2
    while len(primes) < count:
        is_prime = all(candidate % prime for prime in primes if prime * prime <= candidate)
        if is_prime:
            primes.append(candidate)
        candidate += 1
    return primes


@dataclass(frozen=True)
class CorrectionResult:
    state: EntryState
    original: str
    corrected: str
    confidence: float
    values: tuple[int, ...]
    result: int


PRIME_WORDS = ("SUM", "FIRST", "PRIMES")


def _best_word_score(word: str, expected: str) -> float:
    return SequenceMatcher(None, word, expected).ratio()


def correct_prime_sum(text: str, threshold: float = 0.75) -> CorrectionResult | None:
    """Recognize exact or recoverable requests to sum the first N primes."""
    normalized = normalize(text)
    words = normalized.split()
    number = next((int(word) for word in words if word.isdigit()), None)
    if number is None or not 1 <= number <= 255:
        return None

    lexical_words = [word for word in words if not word.isdigit() and word not in ("THE", "NUMBERS", "NUMBER")]
    if not lexical_words:
        return None

    scores = [max((_best_word_score(word, expected) for word in lexical_words), default=0.0) for expected in PRIME_WORDS]
    confidence = sum(scores) / len(scores)

    # Only claim this intent when at least two semantic keywords are visible.
    visible = sum(score >= 0.60 for score in scores)
    if visible < 2:
        return None

    corrected = f"SUM THE FIRST {number} PRIME NUMBERS"
    values = tuple(first_primes(number))
    exact_forms = {
        f"SUM FIRST {number} PRIMES",
        f"SUM FIRST {number} PRIME NUMBERS",
        f"SUM THE FIRST {number} PRIME NUMBERS",
    }
    state = EntryState.O_WOLE_ACCEPTED if normalized in exact_forms else EntryState.OLE_WOLE_ATUNSE
    if confidence < threshold:
        return CorrectionResult(EntryState.KO_WOLE_REJECTED, text, corrected, confidence, values, sum(values))
    return CorrectionResult(state, text, corrected, confidence, values, sum(values))


def render_correction(correction: CorrectionResult) -> str:
    # Interactive clients already emit Ó WỌLÉ when they receive valid input.
    # Only emit an additional state when correction or rejection changes it.
    lines = [] if correction.state is EntryState.O_WOLE_ACCEPTED else [entry_text(correction.state)]
    if correction.state is not EntryState.O_WOLE_ACCEPTED:
        lines.extend(
            (
                f"You wrote : {correction.original}",
                f"Suggested : {correction.corrected}",
                f"Confidence: {correction.confidence * 100:.2f}%",
            )
        )
    if correction.state is not EntryState.KO_WOLE_REJECTED:
        expression = " + ".join(str(value) for value in correction.values)
        lines.extend((f"Primes    : {expression}", f"Result    : {correction.result}"))
    else:
        lines.append("Correction confidence is below 75%.")
    return "\n".join(lines)
