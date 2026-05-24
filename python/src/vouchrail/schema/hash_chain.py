"""SHA-256 hash chain primitives — Python parity with TS reference.

The chain link semantics here match ``packages/schema/src/hash-chain.ts``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Literal

from .jcs import canonicalize_for_hash

HASH_ALGORITHM: Literal["sha256"] = "sha256"

# SHA-256 of the ASCII sentinel "vouchrail:genesis-v1" — stable across all
# installations and matches the TS implementation byte-for-byte.
GENESIS_PREVIOUS_HASH: str = hashlib.sha256(b"vouchrail:genesis-v1").hexdigest()


def compute_entry_hash(entry_without_hash_or_sig: dict[str, Any]) -> str:
    """Canonicalize the entry (sans ``entryHash`` and ``signature``) and SHA-256."""

    canonical = canonicalize_for_hash(entry_without_hash_or_sig)
    return hashlib.sha256(canonical).hexdigest()


def link_entry(
    input_fields: dict[str, Any],
    previous_entry: dict[str, Any] | None,
) -> dict[str, Any]:
    """Stamp ``previousEntryHash`` + ``entryHash`` onto ``input_fields``.

    Returns a new dict; ``input_fields`` is not mutated. The caller applies the
    signature separately (it depends on an external key).
    """

    previous_entry_hash = (
        previous_entry["entryHash"] if previous_entry is not None else GENESIS_PREVIOUS_HASH
    )
    candidate = {**input_fields, "previousEntryHash": previous_entry_hash}
    entry_hash = compute_entry_hash(candidate)
    return {**candidate, "entryHash": entry_hash}


def verify_entry_hash(entry: dict[str, Any]) -> bool:
    """Recompute the hash of ``entry`` and check it against the stored value."""

    stored: str = entry["entryHash"]
    stripped = {k: v for k, v in entry.items() if k not in ("entryHash", "signature")}
    return compute_entry_hash(stripped) == stored


@dataclass(frozen=True)
class ChainVerificationResult:
    """Result of verifying a chain of entries; ``broken_at`` is ``None`` iff valid."""

    valid: bool
    broken_at: int | None = None
    reason: (
        Literal["entry_hash_mismatch", "chain_link_mismatch", "genesis_link_mismatch"] | None
    ) = None
    detail: str | None = None


def verify_chain(entries: list[dict[str, Any]]) -> ChainVerificationResult:
    """Verify ``entries`` in chronological order.

    Same contract as ``verifyChain`` in the TS schema package.
    """

    for i, entry in enumerate(entries):
        prev = entries[i - 1] if i > 0 else None
        if not verify_entry_hash(entry):
            return ChainVerificationResult(
                valid=False,
                broken_at=i,
                reason="entry_hash_mismatch",
                detail=(
                    f"entry at index {i} (callId={entry.get('callId')}) has been modified"
                ),
            )
        expected_prev = prev["entryHash"] if prev is not None else GENESIS_PREVIOUS_HASH
        if entry.get("previousEntryHash") != expected_prev:
            return ChainVerificationResult(
                valid=False,
                broken_at=i,
                reason=("genesis_link_mismatch" if prev is None else "chain_link_mismatch"),
                detail=(
                    f"entry at index {i} (callId={entry.get('callId')}) does not "
                    "link to previous entry"
                ),
            )
    return ChainVerificationResult(valid=True)
