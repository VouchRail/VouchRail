"""Provider adapter contract — Python parity with TS providers/types.ts."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

PROVIDER_ERROR_RISK_FLAG = "provider_error"


@runtime_checkable
class ProviderHostLogger(Protocol):
    """Minimal logger surface a provider adapter depends on."""

    def start_call(
        self,
        *,
        case_id: str,
        session_id: str | None = ...,
        parent_call_id: str | None = ...,
        model_provider: str,
        model_name: str,
        model_version: str,
        model_configuration: dict[str, Any] | None = ...,
        prompt_template_id: str,
        prompt_template_version: str,
        operator_id: str,
        input: Any = ...,
        prompt: Any = ...,
        reference_database: str | None = ...,
    ) -> str: ...

    def end_call(
        self,
        call_id: str,
        *,
        output: Any = ...,
        output_decision: Any = ...,
        reason_codes: list[str] | None = ...,
        risk_flags: list[str] | None = ...,
    ) -> dict[str, Any]: ...


@runtime_checkable
class ProviderAdapter(Protocol):
    """A provider SDK wrapper. ``wrap`` MUST mutate ``client`` in place."""

    provider_id: str

    def detect(self, client: Any) -> bool: ...

    def wrap(self, audit: ProviderHostLogger, client: Any, context: WrapContext) -> None: ...


class WrapContext:
    """Audit context applied to every call routed through a wrapped client."""

    __slots__ = (
        "case_id",
        "operator_id",
        "parent_call_id",
        "prompt_template_id",
        "prompt_template_version",
        "session_id",
    )

    def __init__(
        self,
        *,
        case_id: str,
        prompt_template_id: str,
        prompt_template_version: str,
        operator_id: str,
        session_id: str | None = None,
        parent_call_id: str | None = None,
    ) -> None:
        self.case_id = case_id
        self.prompt_template_id = prompt_template_id
        self.prompt_template_version = prompt_template_version
        self.operator_id = operator_id
        self.session_id = session_id
        self.parent_call_id = parent_call_id
