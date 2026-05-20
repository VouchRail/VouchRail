"""PII pseudonym token stores — Python parity with TS pii.ts."""

from __future__ import annotations

import secrets
from abc import ABC, abstractmethod

from ..defaults import PII_DEFAULTS


class PiiTokenStore(ABC):
    @abstractmethod
    def get_or_create_token(self, case_id: str, field_key: str, value: str) -> str:
        """Idempotent: identical (case_id, field_key, value) returns the same token."""

    @abstractmethod
    def reveal(self, token: str) -> str | None:
        """Return the original PII value for justified-reveal flows."""

    @abstractmethod
    def erase_case(self, case_id: str) -> None:
        """GDPR-style erasure: delete all tokens for a case."""

    def close(self) -> None:
        return None


def _mint_pseudonym() -> str:
    suffix = secrets.token_hex(PII_DEFAULTS.pseudonym_random_bytes)
    return f"{PII_DEFAULTS.pseudonym_prefix}:{suffix}"


def _composite_key(case_id: str, field_key: str, value: str) -> str:
    d = PII_DEFAULTS.composite_delimiter
    return f"{case_id}{d}{field_key}{d}{value}"


class InMemoryPiiTokenStore(PiiTokenStore):
    """Single-process token store; suitable for tests + short-lived demos."""

    def __init__(self) -> None:
        self._forward: dict[str, str] = {}
        self._reverse: dict[str, tuple[str, str, str]] = {}
        self._case_index: dict[str, set[str]] = {}

    def get_or_create_token(self, case_id: str, field_key: str, value: str) -> str:
        forward_key = _composite_key(case_id, field_key, value)
        existing = self._forward.get(forward_key)
        if existing is not None:
            return existing
        token = _mint_pseudonym()
        self._forward[forward_key] = token
        self._reverse[token] = (case_id, forward_key, value)
        self._case_index.setdefault(case_id, set()).add(token)
        return token

    def reveal(self, token: str) -> str | None:
        meta = self._reverse.get(token)
        return meta[2] if meta is not None else None

    def erase_case(self, case_id: str) -> None:
        tokens = self._case_index.pop(case_id, None)
        if tokens is None:
            return
        for t in tokens:
            meta = self._reverse.pop(t, None)
            if meta is not None:
                self._forward.pop(meta[1], None)
