"""AuditLayer typed error hierarchy — Python parity with TS.

Mirrors ``packages/sdk/src/errors.ts``. Stable ``code`` strings are
identical across the two SDKs so a cross-language verifier or log
shipper can branch on error.code regardless of source language.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Final

# Stable error codes. NEVER renumber or remove — values are part of the
# public surface. Keep aligned with packages/sdk/src/errors.ts ERROR_CODES.
ERROR_CODES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "CONFIG_INVALID": "AUDITLAYER_CONFIG_INVALID",
        "CONFIG_MISSING_FIELD": "AUDITLAYER_CONFIG_MISSING_FIELD",
        "CONFIG_UNKNOWN_BACKEND": "AUDITLAYER_CONFIG_UNKNOWN_BACKEND",
        "CONFIG_UNKNOWN_STORE": "AUDITLAYER_CONFIG_UNKNOWN_STORE",
        "STORAGE_BAD_JSON": "AUDITLAYER_STORAGE_BAD_JSON",
        "STORAGE_BAD_SCHEMA": "AUDITLAYER_STORAGE_BAD_SCHEMA",
        "STORAGE_BACKEND_MISSING_DEP": "AUDITLAYER_STORAGE_BACKEND_MISSING_DEP",
        "SCHEMA_HASH_RECHECK_FAILED": "AUDITLAYER_SCHEMA_HASH_RECHECK_FAILED",
        "SCHEMA_INVALID_TIMESTAMP": "AUDITLAYER_SCHEMA_INVALID_TIMESTAMP",
        "SIGNER_INVALID_SECRET": "AUDITLAYER_SIGNER_INVALID_SECRET",
        "SIGNER_EXTERNAL_INVALID_OUTPUT": "AUDITLAYER_SIGNER_EXTERNAL_INVALID_OUTPUT",
        "PROVIDER_UNSUPPORTED_CLIENT": "AUDITLAYER_PROVIDER_UNSUPPORTED_CLIENT",
        "PII_TOKEN_STORE_MISSING": "AUDITLAYER_PII_TOKEN_STORE_MISSING",
        "PII_TOKEN_STORE_MISSING_DEP": "AUDITLAYER_PII_TOKEN_STORE_MISSING_DEP",
        "LOGGER_CALL_NOT_PENDING": "AUDITLAYER_LOGGER_CALL_NOT_PENDING",
        "LOGGER_PATH_SEGMENT_UNSAFE": "AUDITLAYER_LOGGER_PATH_SEGMENT_UNSAFE",
    },
)


class AuditLayerError(Exception):
    """Base class for every public failure path.

    Tests + callers branch on ``isinstance`` or ``error.code``, never on
    ``str(error)`` text.
    """

    __slots__ = ("code", "context")

    def __init__(self, code: str, message: str, context: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        # Frozen view so callers cannot mutate the error after the fact.
        self.context: Mapping[str, Any] = MappingProxyType(dict(context or {}))


class AuditLayerConfigError(AuditLayerError):
    pass


class AuditLayerStorageError(AuditLayerError):
    pass


class AuditLayerSchemaError(AuditLayerError):
    pass


class AuditLayerSignerError(AuditLayerError):
    pass


class AuditLayerProviderError(AuditLayerError):
    pass


class AuditLayerPiiError(AuditLayerError):
    pass


class AuditLayerLifecycleError(AuditLayerError):
    """Logger state-machine violations (e.g. end_call on a finalized call_id)."""

    pass
