from __future__ import annotations

import json
from typing import Any


def serialize_for_tokens(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def estimate_tokens(value: Any) -> int:
    """Estimate tokens with tiktoken when available, otherwise use a chars/4 heuristic."""

    text = serialize_for_tokens(value)
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return max(1, int(len(text) / 4))


def estimate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    input_cost_per_1m: float,
    output_cost_per_1m: float,
) -> float:
    return (input_tokens / 1_000_000.0) * input_cost_per_1m + (
        output_tokens / 1_000_000.0
    ) * output_cost_per_1m
