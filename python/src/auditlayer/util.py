"""Internal helpers — Python parity with packages/sdk/src/util.ts."""

from __future__ import annotations

import datetime as _dt
import hashlib
import re
import uuid
from typing import Any

from .defaults import SAFE_PATH_SEGMENT_PATTERN
from .errors import ERROR_CODES, AuditLayerConfigError, AuditLayerSchemaError
from .schema.jcs import canonicalize_for_hash

_SAFE_PATH_SEGMENT = re.compile(SAFE_PATH_SEGMENT_PATTERN)


def assert_safe_path_segment(value: str, label: str) -> str:
    """Reject any string unsafe for use as a file-path or S3-key segment."""

    if not value or not _SAFE_PATH_SEGMENT.fullmatch(value) or value in (".", ".."):
        raise AuditLayerConfigError(
            ERROR_CODES["LOGGER_PATH_SEGMENT_UNSAFE"],
            f"{label} must match {SAFE_PATH_SEGMENT_PATTERN} and not be '.' or '..' "
            f"(got {value!r}).",
            {"label": label, "value": value},
        )
    return value


def now_iso() -> str:
    """ISO-8601 with explicit ``Z`` suffix, microsecond precision.

    Matches ``new Date().toISOString()`` in JS so cross-platform timestamps
    sort and parse identically.
    """

    return (
        _dt.datetime.now(tz=_dt.timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def uuid_v4() -> str:
    return str(uuid.uuid4())


def derive_duration_ms(started_at: str, ended_at: str) -> int:
    try:
        start = _dt.datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end = _dt.datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuditLayerSchemaError(
            ERROR_CODES["SCHEMA_INVALID_TIMESTAMP"],
            f"derive_duration_ms: invalid ISO datetime ({started_at} / {ended_at})",
            {"startedAt": started_at, "endedAt": ended_at},
        ) from exc
    return max(0, int((end - start).total_seconds() * 1000))


def fingerprint(value: Any) -> str:
    """SHA-256 hex of the JCS canonical form. Stable across SDK versions."""

    canonical = canonicalize_for_hash(None if value is None else value)
    return hashlib.sha256(canonical).hexdigest()
