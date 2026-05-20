"""Provider registry — first-detect-wins, custom adapters take precedence.

Mirrors ``packages/sdk/src/providers/registry.ts``.
"""

from __future__ import annotations

from typing import Any

from ..errors import ERROR_CODES, AuditLayerProviderError
from .anthropic import anthropic_adapter
from .base import ProviderAdapter, ProviderHostLogger, WrapContext
from .openai import openai_adapter

BUILT_IN_PROVIDER_ADAPTERS: tuple[ProviderAdapter, ...] = (anthropic_adapter, openai_adapter)

_custom_adapters: list[ProviderAdapter] = []


def register_provider(adapter: ProviderAdapter) -> None:
    _custom_adapters.append(adapter)


def unregister_provider(provider_id: str) -> None:
    for i, a in enumerate(_custom_adapters):
        if a.provider_id == provider_id:
            del _custom_adapters[i]
            return


def resolve_adapters() -> tuple[ProviderAdapter, ...]:
    return tuple(_custom_adapters) + BUILT_IN_PROVIDER_ADAPTERS


def detect_adapter(client: Any) -> ProviderAdapter | None:
    for adapter in resolve_adapters():
        if adapter.detect(client):
            return adapter
    return None


def wrap_client(audit: ProviderHostLogger, client: Any, context: WrapContext) -> Any:
    """Wrap ``client`` in place; return the same reference."""

    adapter = detect_adapter(client)
    if adapter is None:
        raise AuditLayerProviderError(
            ERROR_CODES["PROVIDER_UNSUPPORTED_CLIENT"],
            "AuditLogger.wrap: client does not match any registered provider adapter. "
            "Built-in adapters: "
            + ", ".join(a.provider_id for a in BUILT_IN_PROVIDER_ADAPTERS)
            + ". Use start_call/end_call directly for unsupported clients, or call "
            "register_provider() with a custom adapter.",
            {"registered": [a.provider_id for a in resolve_adapters()]},
        )
    adapter.wrap(audit, client, context)
    return client
