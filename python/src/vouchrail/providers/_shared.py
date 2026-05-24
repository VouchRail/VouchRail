"""Helpers reused by every provider adapter."""

from __future__ import annotations

from typing import Any


def pick_keys(params: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {k: params[k] for k in keys if k in params}


def extract_output(response: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(response, dict):
        return {k: response.get(k) for k in keys}
    return response


def merge_first_dict_arg(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    """Anthropic/OpenAI SDKs accept kwargs; mock clients used in tests sometimes
    pass a dict positionally. Merge both into one params dict, with kwargs
    winning on key collisions."""
    params: dict[str, Any] = dict(kwargs)
    if args:
        first = args[0]
        if isinstance(first, dict):
            params = {**first, **params}
    return params
