"""Signer ABC — Python parity with packages/sdk/src/signing.ts."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Signer(ABC):
    """Sign a SHA-256 hex digest with a backend-specific key."""

    key_id: str

    @abstractmethod
    def sign(self, entry_hash_hex: str) -> str:
        """Return the signature string. Caller stores it verbatim."""
