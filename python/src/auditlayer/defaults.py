"""Centralized defaults for the Python SDK — Python parity with TS.

Mirrors ``packages/sdk/src/defaults.ts``. Every default that would
otherwise be a magic literal lives here.
"""

from __future__ import annotations

from typing import Final, Literal


class StorageDefaults:
    rotate_by: Literal["hour", "day"] = "hour"
    s3_checksum_algorithm: Literal["SHA256"] = "SHA256"
    s3_content_type: str = "application/json"
    jsonl_extension: str = ".jsonl"


STORAGE_DEFAULTS: Final = StorageDefaults()


class SigningDefaults:
    inline_secret_min_length: int = 16
    inline_signature_prefix: str = "hmac-sha256"
    inline_key_id: str = "inline"


SIGNING_DEFAULTS: Final = SigningDefaults()


class PiiDefaults:
    strategy: Literal["pseudonymize", "hash", "remove"] = "pseudonymize"
    pseudonym_random_bytes: int = 8
    pseudonym_prefix: str = "pii"
    hash_prefix: str = "pii-h"
    hash_hex_length: int = 16
    remove_placeholder: str = "[REDACTED]"
    composite_delimiter: str = "\x1f"


PII_DEFAULTS: Final = PiiDefaults()


class CliDefaults:
    config_files: tuple[str, ...] = ("auditlayer.config.json", ".auditlayer.json")
    init_output_path: str = "auditlayer.config.json"


CLI_DEFAULTS: Final = CliDefaults()


class RetentionDefaults:
    deployer_minimum_days: int = 180
    provider_target_days: int = 2555


RETENTION_DEFAULTS: Final = RetentionDefaults()


class HashChainDefaults:
    enabled: bool = True
    algorithm: Literal["sha256"] = "sha256"


HASH_CHAIN_DEFAULTS: Final = HashChainDefaults()


# Path-segment regex; mirrors ``util.ts`` ``SAFE_PATH_SEGMENT``.
SAFE_PATH_SEGMENT_PATTERN: Final[str] = r"^[A-Za-z0-9._-]+$"
