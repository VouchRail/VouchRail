"""PII pseudonym token stores — Python parity with TS pii.ts."""

from __future__ import annotations

import datetime as _dt
import secrets
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path

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


class SqlitePiiTokenStore(PiiTokenStore):
    """File-backed token store using Python's stdlib ``sqlite3``.

    Mirrors ``SqlitePiiTokenStore`` in ``packages/sdk/src/pii.ts``. The TS
    version depends on the optional ``better-sqlite3`` peer dep; the Python
    version uses the stdlib so no extra install is needed. Schema is
    intentionally identical so the same database file can be opened by
    either runtime if a customer ever decides to share state.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = str(path)
        # ``check_same_thread=False`` lets multiple threads share the
        # connection; access is serialized at the SQL level via short
        # transactions.
        self._conn = sqlite3.connect(self._path, check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pii_tokens (
              case_id TEXT NOT NULL,
              field_key TEXT NOT NULL,
              value TEXT NOT NULL,
              token TEXT NOT NULL UNIQUE,
              created_at TEXT NOT NULL,
              PRIMARY KEY (case_id, field_key, value)
            )
            """,
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_pii_token ON pii_tokens(token)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_pii_case ON pii_tokens(case_id)")

    def get_or_create_token(self, case_id: str, field_key: str, value: str) -> str:
        cur = self._conn.execute(
            "SELECT token FROM pii_tokens WHERE case_id = ? AND field_key = ? AND value = ?",
            (case_id, field_key, value),
        )
        row = cur.fetchone()
        if row is not None:
            return str(row[0])
        token = _mint_pseudonym()
        created_at = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO pii_tokens (case_id, field_key, value, token, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (case_id, field_key, value, token, created_at),
        )
        return token

    def reveal(self, token: str) -> str | None:
        cur = self._conn.execute("SELECT value FROM pii_tokens WHERE token = ?", (token,))
        row = cur.fetchone()
        return str(row[0]) if row is not None else None

    def erase_case(self, case_id: str) -> None:
        self._conn.execute("DELETE FROM pii_tokens WHERE case_id = ?", (case_id,))

    def close(self) -> None:
        self._conn.close()
