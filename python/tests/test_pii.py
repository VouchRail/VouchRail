"""Tests for ``PiiRedactor`` + ``detect_pii`` overlap correctness."""

from __future__ import annotations

from vouchrail import PiiRedactor
from vouchrail.pii.redactor import detect_pii


def test_detect_pii_drops_overlapping_matches() -> None:
    # `4111-1111-1111-1111` matches BOTH phone and creditCard regexes at the
    # same starting index. Before the dedup fix the backward replacement
    # walked intersecting spans and corrupted the redacted output. Now exactly
    # one match wins (earliest, longest), later overlaps are dropped.
    matches = detect_pii(
        "charged 4111-1111-1111-1111 today",
        enabled_patterns={"phone": True, "creditCard": True},
    )
    assert len(matches) == 1
    assert matches[0].match == "4111-1111-1111-1111"


def test_redactor_keeps_surrounding_text_intact_on_overlap() -> None:
    redactor = PiiRedactor(
        enabled=True,
        strategy="hash",
        patterns={"phone": True, "creditCard": True},
    )
    result = redactor.redact(
        {"msg": "charged 4111-1111-1111-1111 today"},
        case_id="case-overlap",
    )
    out = result.redacted["msg"]
    assert "4111-1111-1111-1111" not in out
    assert out.startswith("charged ")
    assert out.endswith(" today")
    # The single hashed pattern lands between "charged " and " today".
    import re

    assert re.fullmatch(r"charged pii-h:[0-9a-f]{16} today", out) is not None
