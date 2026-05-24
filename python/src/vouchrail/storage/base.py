"""Storage backend ABC — Python parity with packages/sdk/src/backends/types.ts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AppendOptions:
    system_id: str


@dataclass(frozen=True)
class QueryOptions:
    system_id: str
    from_: str | None = None
    to: str | None = None
    case_id: str | None = None


class StorageBackend(ABC):
    """Append-only storage with chronological listing."""

    @abstractmethod
    def append(self, entry: dict[str, Any], opts: AppendOptions) -> None:
        """Append a single audit log entry. MUST be atomic per-entry."""

    @abstractmethod
    def list(self, opts: QueryOptions) -> Iterable[dict[str, Any]]:
        """Iterate entries in chronological order (best effort)."""

    def close(self) -> None:
        """Optional resource cleanup. Default no-op."""
        return None
