"""PII detection + redaction — Python parity with packages/sdk/src/pii.ts."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from ..defaults import PII_DEFAULTS
from ..errors import ERROR_CODES, AuditLayerPiiError
from ..pii_patterns import ALL_PII_PATTERN_NAMES, DEFAULT_ENABLED_PII_PATTERNS, PII_PATTERN_REGISTRY
from .token_store import PiiTokenStore

Strategy = Literal["pseudonymize", "hash", "remove"]


@dataclass(frozen=True)
class RedactionResult:
    redacted: Any
    fields_touched: list[str]
    pseudonym_key: str | None


@dataclass(frozen=True)
class _Match:
    pattern_name: str
    match: str
    index: int


def hash_string(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def detect_pii(
    text: str,
    enabled_patterns: Mapping[str, bool] | None = None,
    custom_patterns: Mapping[str, re.Pattern[str]] | None = None,
) -> list[_Match]:
    """All matches across enabled built-in + custom patterns, sorted by index."""

    enabled = enabled_patterns or {}
    out: list[_Match] = []
    for name in ALL_PII_PATTERN_NAMES:
        if not enabled.get(name):
            continue
        regex = PII_PATTERN_REGISTRY[name].regex
        for m in regex.finditer(text):
            out.append(_Match(pattern_name=name, match=m.group(0), index=m.start()))
    if custom_patterns:
        for name, regex in custom_patterns.items():
            for m in regex.finditer(text):
                out.append(_Match(pattern_name=name, match=m.group(0), index=m.start()))
    out.sort(key=lambda m: m.index)
    return out


class PiiRedactor:
    """Walks a JSON-compatible value and redacts PII in every string leaf.

    Mirrors the TS PiiRedactor: ``pseudonymize`` consumes a token store
    (idempotent reversible tokens), ``hash`` outputs a truncated SHA-256
    prefix, ``remove`` substitutes ``[REDACTED]``.
    """

    def __init__(
        self,
        *,
        enabled: bool = False,
        strategy: Strategy = PII_DEFAULTS.strategy,
        patterns: Mapping[str, bool] | None = None,
        custom_patterns: Mapping[str, re.Pattern[str]] | None = None,
        token_store: PiiTokenStore | None = None,
    ) -> None:
        self.enabled = enabled
        self.strategy: Strategy = strategy
        self._enabled_patterns: Mapping[str, bool] = (
            patterns if patterns is not None else dict(DEFAULT_ENABLED_PII_PATTERNS)
        )
        self._custom_patterns: Mapping[str, re.Pattern[str]] = custom_patterns or {}
        self._token_store = token_store
        if enabled and strategy == "pseudonymize" and token_store is None:
            raise AuditLayerPiiError(
                ERROR_CODES["PII_TOKEN_STORE_MISSING"],
                "PiiRedactor: pseudonymize strategy requires a token store. "
                "Configure piiRedaction.tokenStore.",
                {"strategy": strategy},
            )

    def redact(self, value: Any, case_id: str) -> RedactionResult:
        if not self.enabled:
            return RedactionResult(redacted=value, fields_touched=[], pseudonym_key=None)
        touched: set[str] = set()
        redacted = self._walk(value, case_id, "root", touched)
        pseudonym_key = (
            case_id if self.strategy == "pseudonymize" and self._token_store is not None else None
        )
        return RedactionResult(
            redacted=redacted,
            fields_touched=sorted(touched),
            pseudonym_key=pseudonym_key,
        )

    def _walk(self, v: Any, case_id: str, path: str, touched: set[str]) -> Any:
        if v is None or isinstance(v, (bool, int, float)):
            return v
        if isinstance(v, str):
            return self._redact_string(v, case_id, path, touched)
        if isinstance(v, list):
            return [self._walk(item, case_id, f"{path}[{i}]", touched) for i, item in enumerate(v)]
        if isinstance(v, dict):
            return {k: self._walk(val, case_id, f"{path}.{k}", touched) for k, val in v.items()}
        return v

    def _redact_string(self, text: str, case_id: str, path: str, touched: set[str]) -> str:
        matches = detect_pii(text, self._enabled_patterns, self._custom_patterns)
        if not matches:
            return text
        out = text
        for m in reversed(matches):
            touched.add(f"{path}:{m.pattern_name}")
            if self.strategy == "remove":
                replacement = PII_DEFAULTS.remove_placeholder
            elif self.strategy == "hash":
                replacement = (
                    f"{PII_DEFAULTS.hash_prefix}:"
                    f"{hash_string(m.match)[: PII_DEFAULTS.hash_hex_length]}"
                )
            else:
                assert self._token_store is not None
                replacement = self._token_store.get_or_create_token(
                    case_id,
                    f"{path}:{m.pattern_name}",
                    m.match,
                )
            out = out[: m.index] + replacement + out[m.index + len(m.match) :]
        return out
