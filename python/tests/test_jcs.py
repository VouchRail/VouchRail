"""Tests for the JCS canonicalization implementation.

The cross-language conformance vectors live under ``conformance-vectors/``
and are run by both TS + Python runners in CI. These tests cover Python-
specific edge cases (NaN/Infinity raising, circular structures, supported
types) that the vectors cannot represent in JSON.
"""

from __future__ import annotations

import math

import pytest

from auditlayer.schema.jcs import canonicalize, canonicalize_for_hash


def test_null():
    assert canonicalize(None) == "null"


def test_booleans():
    assert canonicalize(True) == "true"
    assert canonicalize(False) == "false"


def test_empty_collections():
    assert canonicalize([]) == "[]"
    assert canonicalize({}) == "{}"


def test_integer_uses_int_str():
    assert canonicalize(0) == "0"
    assert canonicalize(1) == "1"
    assert canonicalize(-1) == "-1"
    assert canonicalize(9007199254740991) == "9007199254740991"


def test_float_whole_number_drops_decimal():
    assert canonicalize(1.0) == "1"
    assert canonicalize(-2.0) == "-2"


def test_float_fractional():
    assert canonicalize(0.5) == "0.5"
    assert canonicalize(0.1) == "0.1"


def test_float_ecma262_positional_lower_boundary():
    # ECMA-262 NumberToString keeps positional notation down to 10^-6.
    # Below that it switches to scientific. Locks the cross-language contract
    # with JS JSON.stringify; Python's json.dumps would diverge here.
    assert canonicalize(0.000001) == "0.000001"
    assert canonicalize(0.0000001) == "1e-7"
    assert canonicalize(0.00000015) == "1.5e-7"


def test_float_ecma262_positional_upper_boundary():
    # ECMA-262 keeps positional notation up to and including 10^20; at 10^21
    # it switches to scientific. Catches the divergence at 1e16-1e20 where
    # Python json.dumps would emit "1e+16" but JS emits "10000000000000000".
    assert canonicalize(1e16) == "10000000000000000"
    assert canonicalize(1e20) == "100000000000000000000"
    assert canonicalize(1e21) == "1e+21"
    assert canonicalize(1.5e21) == "1.5e+21"


def test_float_negative_zero_serializes_as_zero():
    # ECMA-262: +0 and -0 both -> "0".
    assert canonicalize(-0.0) == "0"


def test_float_negative_sign_preserved():
    assert canonicalize(-0.5) == "-0.5"
    assert canonicalize(-0.000001) == "-0.000001"


def test_string():
    assert canonicalize("hello") == '"hello"'
    assert canonicalize("a\tb") == '"a\\tb"'
    assert canonicalize("a\"b") == '"a\\"b"'
    assert canonicalize("a\\b") == '"a\\\\b"'


def test_array_preserves_order():
    assert canonicalize([3, 1, 2]) == "[3,1,2]"


def test_object_keys_sorted():
    out = canonicalize({"z": 1, "a": 2})
    assert out == '{"a":2,"z":1}'


def test_object_keys_utf16_sort():
    # 'Z' (U+005A) sorts before 'z' (U+007A) sorts before 'Ä' (U+00C4)
    # sorts before 'ä' (U+00E4) sorts before 'ñ' (U+00F1).
    out = canonicalize({"Ä": 1, "z": 2, "ñ": 3, "Z": 4, "ä": 5})
    assert out == '{"Z":4,"z":2,"Ä":1,"ä":5,"ñ":3}'


def test_nested_recurse():
    out = canonicalize({"outer": {"inner": [1, {"leaf": "ok"}]}})
    assert out == '{"outer":{"inner":[1,{"leaf":"ok"}]}}'


def test_nan_raises():
    with pytest.raises(TypeError):
        canonicalize(float("nan"))


def test_inf_raises():
    with pytest.raises(TypeError):
        canonicalize(math.inf)
    with pytest.raises(TypeError):
        canonicalize(-math.inf)


def test_circular_object_raises():
    a: dict = {}
    a["self"] = a
    with pytest.raises(TypeError):
        canonicalize(a)


def test_circular_array_raises():
    a: list = []
    a.append(a)
    with pytest.raises(TypeError):
        canonicalize(a)


def test_unsupported_type_raises():
    with pytest.raises(TypeError):
        canonicalize(object())


def test_non_string_object_key_raises():
    with pytest.raises(TypeError):
        canonicalize({1: "v"})


def test_canonicalize_for_hash_returns_utf8_bytes():
    result = canonicalize_for_hash({"hello": "wörld"})
    assert isinstance(result, bytes)
    assert result == canonicalize({"hello": "wörld"}).encode("utf-8")
