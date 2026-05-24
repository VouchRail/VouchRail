"""OpenAI provider adapter (sync wrap_openai)."""

from __future__ import annotations

import inspect
from typing import Any

from ._shared import extract_output, merge_first_dict_arg, pick_keys
from .base import PROVIDER_ERROR_RISK_FLAG, ProviderHostLogger, WrapContext

OPENAI_CONFIG_KEYS: tuple[str, ...] = (
    "temperature",
    "top_p",
    "max_tokens",
    "frequency_penalty",
    "presence_penalty",
)

OPENAI_OUTPUT_KEYS: tuple[str, ...] = ("choices", "usage", "model", "id")


class OpenAiAdapter:
    provider_id = "openai"

    def detect(self, client: Any) -> bool:
        chat = getattr(client, "chat", None)
        if chat is None:
            return False
        completions = getattr(chat, "completions", None)
        if completions is None:
            return False
        create = getattr(completions, "create", None)
        if not callable(create):
            return False
        return not inspect.iscoroutinefunction(create)

    def wrap(self, audit: ProviderHostLogger, client: Any, context: WrapContext) -> None:
        completions = client.chat.completions
        original_create = completions.create

        def wrapped_create(*args: Any, **kwargs: Any) -> Any:
            params = merge_first_dict_arg(args, kwargs)
            model = str(params.get("model") or "unknown")
            call_id = audit.start_call(
                case_id=context.case_id,
                session_id=context.session_id,
                parent_call_id=context.parent_call_id,
                model_provider="openai",
                model_name=model,
                model_version=model,
                model_configuration=pick_keys(params, OPENAI_CONFIG_KEYS),
                prompt_template_id=context.prompt_template_id,
                prompt_template_version=context.prompt_template_version,
                operator_id=context.operator_id,
                input={"messages": params.get("messages")},
            )
            try:
                response = original_create(*args, **kwargs)
                output = extract_output(response, OPENAI_OUTPUT_KEYS)
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

        completions.create = wrapped_create


openai_adapter = OpenAiAdapter()
