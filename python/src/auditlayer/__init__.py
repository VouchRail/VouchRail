"""AuditLayer Python SDK — EU AI Act Article 12 audit log infrastructure.

Tier S scaffold. The schema subpackage is implemented and byte-compatible with
the TypeScript reference SDK. Storage / signer / wrap / CLI ship in subsequent
milestones; see ``python/README.md`` for the roadmap.
"""

from .schema import (
    GENESIS_PREVIOUS_HASH,
    HASH_ALGORITHM,
    SCHEMA_VERSION,
    SDK_NAME,
    SDK_VERSION,
    AuditLogEntry,
    AuditLogEntryInput,
    canonicalize,
    canonicalize_for_hash,
    compute_entry_hash,
    link_entry,
    verify_chain,
    verify_entry_hash,
)

__all__ = [
    "GENESIS_PREVIOUS_HASH",
    "HASH_ALGORITHM",
    "SCHEMA_VERSION",
    "SDK_NAME",
    "SDK_VERSION",
    "AuditLogEntry",
    "AuditLogEntryInput",
    "canonicalize",
    "canonicalize_for_hash",
    "compute_entry_hash",
    "link_entry",
    "verify_chain",
    "verify_entry_hash",
]
