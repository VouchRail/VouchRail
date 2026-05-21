"""Pydantic model conformance checks."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from auditlayer.schema.types import (
    SCHEMA_VERSION,
    AuditLogEntryInput,
    HumanReview,
    ToolCall,
)

GOOD = {
    "schemaVersion": SCHEMA_VERSION,
    "recordedBy": "auditlayer@0.1.0",
    "callId": "00000000-0000-4000-8000-000000000001",
    "caseId": "case-1",
    "systemId": "sys-1",
    "startedAt": "2026-05-20T12:00:00.000Z",
    "endedAt": "2026-05-20T12:00:00.250Z",
    "durationMs": 250,
    "modelProvider": "anthropic",
    "modelName": "claude-3-5-sonnet-20241022",
    "modelVersion": "20241022",
    "modelConfiguration": {},
    "promptTemplateId": "tmpl",
    "promptTemplateVersion": "1.0.0",
    "promptFingerprint": "0" * 64,
    "inputFingerprint": "0" * 64,
    "outputFingerprint": "0" * 64,
    "outputDecision": {"ok": True},
    "operatorId": "op",
}


def test_camelcase_alias_roundtrip():
    entry = AuditLogEntryInput.model_validate(GOOD)
    assert entry.call_id == "00000000-0000-4000-8000-000000000001"
    dumped = entry.model_dump(by_alias=True, exclude_none=True)
    assert dumped["callId"] == entry.call_id
    assert "callId" in dumped
    assert "call_id" not in dumped


def test_rejects_unknown_field():
    bad = {**GOOD, "rogueField": "x"}
    with pytest.raises(ValidationError):
        AuditLogEntryInput.model_validate(bad)


def test_rejects_bad_fingerprint():
    bad = {**GOOD, "promptFingerprint": "not-hex"}
    with pytest.raises(ValidationError):
        AuditLogEntryInput.model_validate(bad)


def test_rejects_bad_iso_timestamp():
    bad = {**GOOD, "startedAt": "not-a-date"}
    with pytest.raises(ValidationError):
        AuditLogEntryInput.model_validate(bad)


def test_immutable_after_construction():
    entry = AuditLogEntryInput.model_validate(GOOD)
    with pytest.raises(ValidationError):
        entry.case_id = "mutated"  # type: ignore[misc]


def test_human_review_decision_enum():
    HumanReview.model_validate(
        {
            "reviewerId": "r",
            "reviewedAt": "2026-05-20T12:00:00.000Z",
            "decision": "approve",
        },
    )
    with pytest.raises(ValidationError):
        HumanReview.model_validate(
            {
                "reviewerId": "r",
                "reviewedAt": "2026-05-20T12:00:00.000Z",
                "decision": "nope",
            },
        )


def test_tool_call_requires_fingerprints():
    with pytest.raises(ValidationError):
        ToolCall.model_validate(
            {
                "toolName": "t",
                "inputFingerprint": "short",
                "outputFingerprint": "0" * 64,
                "startedAt": "2026-05-20T12:00:00.000Z",
                "endedAt": "2026-05-20T12:00:00.000Z",
            },
        )
