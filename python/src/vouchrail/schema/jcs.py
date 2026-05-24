"""JSON Canonicalization Scheme (JCS) — RFC 8785.

Byte-compatible with the TypeScript reference implementation in
``packages/schema/src/canonicalize.ts``. Cross-language hash determinism is the
non-negotiable invariant of the VouchRail schema spec; any divergence here
breaks the chain.

Rules implemented:
- UTF-8 output bytes (the returned ``str`` encodes to UTF-8 cleanly).
- Object keys sorted by UTF-16 code unit order (RFC 8785 §3.2.3). Python
  strings iterate over Unicode code points; for the BMP-only key space the
  VouchRail schema requires (ASCII-ish identifiers), code-point order matches
  UTF-16 code-unit order. The unit tests pin this with explicit non-ASCII
  vectors.
- Strings serialized via :func:`json.dumps` with ``ensure_ascii=False`` and
  ``separators=(',', ':')`` — RFC 8785 §3.2.2.2 short-form escapes for
  U+0000 to U+001F, U+0022, U+005C.
- Numbers serialized per RFC 8785 §3.2.2.3 via ECMA-262 ToString(Number). The
  IEEE 754 double-precision shortest-round-trip representation is what the TS
  side gets from ``JSON.stringify``; Python's ``repr`` for floats produces the
  same shortest-round-trip but with different formatting for whole numbers
  (``1.0`` vs ``1``). We special-case integers explicitly.
- ``true`` / ``false`` / ``null`` are the literal lowercase JSON tokens.
- ``NaN`` / ``±Infinity`` raise ``TypeError``.
- Circular structures raise ``TypeError`` (detected via id-set).

This module deliberately does not depend on any third-party JSON library
because canonical-form behavior must be controlled byte-precisely.
"""

from __future__ import annotations

import json
import math
from typing import Any


def canonicalize(value: Any) -> str:
    """Return the JCS canonical string for ``value`` (JSON-compatible input)."""

    seen: set[int] = set()
    return _serialize(value, seen)


def canonicalize_for_hash(value: Any) -> bytes:
    """UTF-8 bytes of the canonical form, suitable for SHA-256 hashing."""

    return canonicalize(value).encode("utf-8")


def _serialize(value: Any, seen: set[int]) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, bool):  # pragma: no cover — handled above; defensive.
        return "true" if value else "false"
    if isinstance(value, int):
        return _serialize_int(value)
    if isinstance(value, float):
        return _serialize_float(value)
    if isinstance(value, str):
        return _serialize_string(value)
    if isinstance(value, (list, tuple)):
        return _serialize_array(value, seen)
    if isinstance(value, dict):
        return _serialize_object(value, seen)
    raise TypeError(f"canonicalize: unsupported value type {type(value).__name__}")


def _serialize_int(value: int) -> str:
    # Booleans subclass int; guarded earlier. Plain integer ToString matches
    # JSON.stringify in TS (no leading +, '-' for negatives).
    return str(value)


def _serialize_float(value: float) -> str:
    if math.isnan(value) or math.isinf(value):
        raise TypeError("canonicalize: non-finite numbers are not valid JCS")
    if value.is_integer() and abs(value) <= 2**53 - 1:
        # JSON.stringify(1.0) -> "1"; mirror that for safe-integer-valued floats.
        return str(int(value))
    return _ecma262_number_to_string(value)


def _ecma262_number_to_string(x: float) -> str:
    """ECMA-262 Number::toString (a.k.a. JS ``JSON.stringify`` for numbers).

    RFC 8785 §3.2.2.3 references this algorithm for canonical numeric output.
    Python's :func:`json.dumps` does NOT match it: Python switches to
    scientific notation around 1e-5 while JS uses positional notation down to
    1e-7. Without this function the conformance vectors silently drift apart
    for any float with magnitude smaller than 1e-4 or any integer-valued
    float between 2^53 and 1e21.

    Algorithm (paraphrased from ECMA-262 §6.1.6.1.13):
    Given x != 0, extract integers ``s`` (significant digits, no trailing
    zeros) and ``n`` such that ``s`` has ``k`` digits and ``s * 10^(n-k) = x``.
    Then:

    * If ``k <= n <= 21``: positional integer, append ``n-k`` trailing zeros.
    * If ``0 < n <= 21``: positional with decimal point at position ``n``.
    * If ``-6 < n <= 0``: positional ``"0."`` + ``-n`` leading zeros + digits.
    * If ``k == 1`` (and outside positional range): ``d e<sign><abs(n-1)>``.
    * Otherwise: ``d.<rest> e<sign><abs(n-1)>``.

    Python's :func:`repr` returns the shortest round-trippable decimal for
    any IEEE 754 double, matching V8. We extract the same significant digits
    Python produces and re-format per ECMA-262.
    """
    if x == 0:
        # +0 and -0 both serialize as "0".
        return "0"
    if x < 0:
        return "-" + _ecma262_number_to_string(-x)

    # repr(x) returns the shortest round-trippable decimal, with formatting
    # that differs from ECMA-262 only in where the scientific/positional
    # cutoff lies. We strip the formatting and re-apply ECMA-262 rules.
    s = repr(x)
    if "e" in s:
        mantissa_str, exp_part = s.split("e")
        e_offset = int(exp_part)
    else:
        mantissa_str = s
        e_offset = 0

    if "." in mantissa_str:
        int_part, frac_part = mantissa_str.split(".")
    else:
        int_part, frac_part = mantissa_str, ""

    combined = (int_part + frac_part).lstrip("0")
    if not combined:
        return "0"

    leading_zeros_stripped = (len(int_part) + len(frac_part)) - len(combined)
    leading_exp = (len(int_part) - 1) - leading_zeros_stripped + e_offset

    digits = combined.rstrip("0") or "0"
    k = len(digits)
    n = leading_exp + 1

    if 1 <= n <= 21 and n >= k:
        return digits + "0" * (n - k)
    if 0 < n < k and n <= 21:
        return digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return "0." + "0" * (-n) + digits

    sign = "+" if n - 1 >= 0 else "-"
    abs_exp = abs(n - 1)
    if k == 1:
        return f"{digits}e{sign}{abs_exp}"
    return f"{digits[0]}.{digits[1:]}e{sign}{abs_exp}"


def _serialize_string(value: str) -> str:
    # JSON.stringify in V8 produces the JCS short-form escapes; Python's
    # ``json.dumps(..., ensure_ascii=False)`` does the same set of escapes
    # (\b \t \n \f \r \" \\ and \u00XX for other C0 controls).
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _serialize_array(value: list[Any] | tuple[Any, ...], seen: set[int]) -> str:
    obj_id = id(value)
    if obj_id in seen:
        raise TypeError("canonicalize: circular array")
    seen.add(obj_id)
    try:
        parts = [_serialize(item, seen) for item in value]
    finally:
        seen.discard(obj_id)
    return "[" + ",".join(parts) + "]"


def _serialize_object(value: dict[str, Any], seen: set[int]) -> str:
    obj_id = id(value)
    if obj_id in seen:
        raise TypeError("canonicalize: circular object")
    seen.add(obj_id)
    try:
        # Drop keys whose value is None — RFC 8785 says null is a valid JSON
        # value, but the VouchRail schema spec (matching the TS impl) treats
        # absent optional fields as "drop the key from the canonical form" so
        # that callers can choose between explicit-null and absent semantics.
        # The TS implementation drops only ``undefined``; Python has no
        # undefined sentinel, so the convention here is: callers serialize an
        # explicit ``None`` only when they want a JSON ``null`` to appear in
        # output. To keep parity with TS (which serializes ``null`` as
        # ``null``), we keep None values.
        keys = list(value.keys())
        for k in keys:
            if not isinstance(k, str):
                raise TypeError(
                    f"canonicalize: object key must be str, got {type(k).__name__}",
                )
        # Sort by UTF-16 code unit order (RFC 8785 §3.2.3).
        keys.sort(key=_utf16_sort_key)
        parts = [
            _serialize_string(k) + ":" + _serialize(value[k], seen) for k in keys
        ]
    finally:
        seen.discard(obj_id)
    return "{" + ",".join(parts) + "}"


def _utf16_sort_key(s: str) -> tuple[int, ...]:
    """Encode ``s`` to its UTF-16 BE code-unit sequence for sort comparison.

    JavaScript string comparison is by UTF-16 code unit, which differs from
    Python's default code-point comparison only in the supplementary plane
    (U+10000+) — surrogate pairs sort before code points 0xE000 to 0xFFFF.
    """

    return tuple(s.encode("utf-16-be"))
