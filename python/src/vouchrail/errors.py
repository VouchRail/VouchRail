"""VouchRail typed error hierarchy — Python parity with TS.

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
        "CONFIG_INVALID": "VOUCHRAIL_CONFIG_INVALID",
        "CONFIG_MISSING_FIELD": "VOUCHRAIL_CONFIG_MISSING_FIELD",
        "CONFIG_UNKNOWN_BACKEND": "VOUCHRAIL_CONFIG_UNKNOWN_BACKEND",
        "CONFIG_UNKNOWN_STORE": "VOUCHRAIL_CONFIG_UNKNOWN_STORE",
        "STORAGE_BAD_JSON": "VOUCHRAIL_STORAGE_BAD_JSON",
        "STORAGE_BAD_SCHEMA": "VOUCHRAIL_STORAGE_BAD_SCHEMA",
        "STORAGE_BACKEND_MISSING_DEP": "VOUCHRAIL_STORAGE_BACKEND_MISSING_DEP",
        "SCHEMA_HASH_RECHECK_FAILED": "VOUCHRAIL_SCHEMA_HASH_RECHECK_FAILED",
        "SCHEMA_INVALID_TIMESTAMP": "VOUCHRAIL_SCHEMA_INVALID_TIMESTAMP",
        "SIGNER_INVALID_SECRET": "VOUCHRAIL_SIGNER_INVALID_SECRET",
        "SIGNER_EXTERNAL_INVALID_OUTPUT": "VOUCHRAIL_SIGNER_EXTERNAL_INVALID_OUTPUT",
        "PROVIDER_UNSUPPORTED_CLIENT": "VOUCHRAIL_PROVIDER_UNSUPPORTED_CLIENT",
        "PII_TOKEN_STORE_MISSING": "VOUCHRAIL_PII_TOKEN_STORE_MISSING",
        "PII_TOKEN_STORE_MISSING_DEP": "VOUCHRAIL_PII_TOKEN_STORE_MISSING_DEP",
        "LOGGER_CALL_NOT_PENDING": "VOUCHRAIL_LOGGER_CALL_NOT_PENDING",
        "LOGGER_PATH_SEGMENT_UNSAFE": "VOUCHRAIL_LOGGER_PATH_SEGMENT_UNSAFE",
    },
)


class VouchRailError(Exception):
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


class VouchRailConfigError(VouchRailError):
    pass


class VouchRailStorageError(VouchRailError):
    pass


class VouchRailSchemaError(VouchRailError):
    pass


class VouchRailSignerError(VouchRailError):
    pass


class VouchRailProviderError(VouchRailError):
    pass


class VouchRailPiiError(VouchRailError):
    pass


class VouchRailLifecycleError(VouchRailError):
    """Logger state-machine violations (e.g. end_call on a finalized call_id)."""

    pass
