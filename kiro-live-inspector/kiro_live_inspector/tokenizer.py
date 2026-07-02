"""Deterministic local token estimation.

Provider-supplied usage is always preferred. This module exists for cases where
usage fields are missing or unavailable.
"""

from __future__ import annotations

import re
from typing import Any

import orjson

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


class TokenCounter:
    """Small local token estimator with no model calls.

    This is intentionally conservative and dependency-light for the experiment.
    It is not a billing-accurate tokenizer. The dashboard marks locally counted
    usage as estimated whenever provider usage is unavailable.
    """

    def count_text(self, value: str) -> int:
        if not value:
            return 0
        return max(1, len(TOKEN_PATTERN.findall(value)))

    def count_jsonish(self, value: Any) -> int:
        if value is None:
            return 0
        if isinstance(value, str):
            return self.count_text(value)
        if isinstance(value, bytes):
            return self.count_text(value.decode("utf-8", errors="replace"))
        if isinstance(value, list):
            return sum(self.count_jsonish(item) for item in value)
        if isinstance(value, dict):
            return sum(self.count_jsonish(item) for item in value.values())
        try:
            return self.count_text(orjson.dumps(value).decode("utf-8"))
        except TypeError:
            return self.count_text(str(value))

