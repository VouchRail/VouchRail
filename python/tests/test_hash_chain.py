"""Tests for the SHA-256 hash chain primitives."""

from __future__ import annotations

import hashlib

from auditlayer.schema.hash_chain import (
    GENESIS_PREVIOUS_HASH,
    HASH_ALGORITHM,
    compute_entry_hash,
    link_entry,
    verify_chain,
    verify_entry_hash,
)


def test_hash_algorithm_is_sha256():
    assert HASH_ALGORITHM == "sha256"


def test_genesis_hash_matches_ts_reference():
    # Matches the TS implementation: SHA-256("auditlayer:genesis-v1").
    expected = hashlib.sha256(b"auditlayer:genesis-v1").hexdigest()
    assert GENESIS_PREVIOUS_HASH == expected


def test_compute_entry_hash_deterministic():
    entry = {"callId": "a", "value": 1}
    assert compute_entry_hash(entry) == compute_entry_hash(entry)


def test_compute_entry_hash_changes_with_payload():
    h1 = compute_entry_hash({"callId": "a"})
    h2 = compute_entry_hash({"callId": "b"})
    assert h1 != h2


def test_link_entry_uses_genesis_when_no_previous():
    linked = link_entry({"callId": "first"}, None)
    assert linked["previousEntryHash"] == GENESIS_PREVIOUS_HASH
    assert linked["entryHash"] != GENESIS_PREVIOUS_HASH


def test_link_entry_chains_to_previous():
    a = link_entry({"callId": "a"}, None)
    b = link_entry({"callId": "b"}, a)
    assert b["previousEntryHash"] == a["entryHash"]


def test_verify_entry_hash_round_trip():
    entry = link_entry({"callId": "z"}, None)
    full = {**entry, "signature": "sig:xxx"}
    assert verify_entry_hash(full) is True


def test_verify_entry_hash_detects_tamper():
    entry = link_entry({"callId": "z"}, None)
    full = {**entry, "signature": "sig:xxx"}
    full["callId"] = "TAMPERED"
    assert verify_entry_hash(full) is False


def test_verify_chain_happy_path():
    a = {**link_entry({"callId": "a"}, None), "signature": "s"}
    b = {**link_entry({"callId": "b"}, a), "signature": "s"}
    c = {**link_entry({"callId": "c"}, b), "signature": "s"}
    result = verify_chain([a, b, c])
    assert result.valid is True
    assert result.broken_at is None


def test_verify_chain_detects_link_break():
    a = {**link_entry({"callId": "a"}, None), "signature": "s"}
    b = {**link_entry({"callId": "b"}, a), "signature": "s"}
    # Forge `b` with the wrong previousEntryHash but a recomputed entryHash.
    forged_b = {**b, "previousEntryHash": "0" * 64}
    forged_b["entryHash"] = compute_entry_hash(
        {k: v for k, v in forged_b.items() if k not in ("entryHash", "signature")},
    )
    result = verify_chain([a, forged_b])
    assert result.valid is False
    assert result.broken_at == 1
    assert result.reason == "chain_link_mismatch"


def test_verify_chain_detects_modified_entry():
    a = {**link_entry({"callId": "a"}, None), "signature": "s"}
    a["callId"] = "TAMPERED"
    result = verify_chain([a])
    assert result.valid is False
    assert result.broken_at == 0
    assert result.reason == "entry_hash_mismatch"


def test_verify_chain_detects_bad_genesis():
    a = {**link_entry({"callId": "a"}, None), "signature": "s"}
    a["previousEntryHash"] = "1" * 64
    a["entryHash"] = compute_entry_hash(
        {k: v for k, v in a.items() if k not in ("entryHash", "signature")},
    )
    result = verify_chain([a])
    assert result.valid is False
    assert result.broken_at == 0
    assert result.reason == "genesis_link_mismatch"
