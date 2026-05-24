"""Async Anthropic provider adapter (wrap_anthropic_async)."""

from __future__ import annotations

import inspect
from typing import Any

from ._shared import extract_output, merge_first_dict_arg, pick_keys
from .anthropic import (
    ANTHROPIC_CONFIG_KEYS,
    ANTHROPIC_OUTPUT_KEYS,
    derive_anthropic_model_version,
)
from .base import PROVIDER_ERROR_RISK_FLAG, ProviderHostLogger, WrapContext


class AsyncAnthropicAdapter:
    """Detects ``AsyncAnthropic``-shaped clients (``messages.create`` is awaitable)."""

    provider_id = "anthropic"

    def detect(self, client: Any) -> bool:
        messages = getattr(client, "messages", None)
        if messages is None:
            return False
        create = getattr(messages, "create", None)
        if not callable(create):
            return False
        return inspect.iscoroutinefunction(create)

    def wrap(self, audit: ProviderHostLogger, client: Any, context: WrapContext) -> None:
        messages = client.messages
        original_create = messages.create

        async def wrapped_create(*args: Any, **kwargs: Any) -> Any:
            params = merge_first_dict_arg(args, kwargs)
            model = str(params.get("model") or "unknown")
            call_id = audit.start_call(
                case_id=context.case_id,
                session_id=context.session_id,
                parent_call_id=context.parent_call_id,
                model_provider="anthropic",
                model_name=model,
                model_version=derive_anthropic_model_version(model),
                model_configuration=pick_keys(params, ANTHROPIC_CONFIG_KEYS),
                prompt_template_id=context.prompt_template_id,
                prompt_template_version=context.prompt_template_version,
                operator_id=context.operator_id,
                input={"messages": params.get("messages"), "system": params.get("system")},
            )
            try:
                response = await original_create(*args, **kwargs)
                output = extract_output(response, ANTHROPIC_OUTPUT_KEYS)
                audit.end_call(call_id, output=output, output_decision=output)
                return response
            except Exception:
                audit.end_call(
                    call_id,
                    output=None,
                    output_decision=None,
                    risk_flags=[PROVIDER_ERROR_RISK_FLAG],
                )
                raise

        messages.create = wrapped_create


async_anthropic_adapter = AsyncAnthropicAdapter()
