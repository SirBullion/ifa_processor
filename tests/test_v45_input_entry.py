from runtime.input_entry_v45 import (
    EntryState,
    correct_prime_sum,
    entry_text,
    first_primes,
    render_correction,
)


def test_security_and_execution_ole_wole_are_distinct():
    security = entry_text(EntryState.OLE_WOLE_ASE)
    execution = entry_text(EntryState.OLE_WOLE_ATUNSE)
    assert security == "Ó LÈ WỌLÉ — ÀṢẸ"
    assert execution == "Ó LÈ WỌLÉ — ÀTÚNṢE"
    assert security != execution


def test_sum_first_seven_primes_exact():
    correction = correct_prime_sum("SUM THE FIRST 7 PRIME NUMBERS")
    assert correction is not None
    assert correction.state is EntryState.O_WOLE_ACCEPTED
    assert correction.values == (2, 3, 5, 7, 11, 13, 17)
    assert correction.result == 58
    assert "Ó WỌLÉ" not in render_correction(correction)


def test_sum_first_seven_primes_typo_is_corrected_above_threshold():
    correction = correct_prime_sum("SUM FIST 7 PTIME")
    assert correction is not None
    assert correction.state is EntryState.OLE_WOLE_ATUNSE
    assert correction.confidence >= 0.75
    assert correction.result == 58
    assert "Ó LÈ WỌLÉ — ÀTÚNṢE" in render_correction(correction)


def test_low_confidence_prime_like_input_is_not_executed():
    correction = correct_prime_sum("SX XXRST 7 PXMS")
    assert correction is not None
    assert correction.state is EntryState.KO_WOLE_REJECTED
    assert correction.confidence < 0.75
    assert "KÒ WỌLÉ" in render_correction(correction)
    assert "Result" not in render_correction(correction)


def test_unrelated_input_is_left_for_regular_language_dispatch():
    assert correct_prime_sum("SHOW RMU") is None
    assert sum(first_primes(7)) == 58
