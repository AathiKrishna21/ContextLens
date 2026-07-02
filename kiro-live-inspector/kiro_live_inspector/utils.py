"""Utility helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse


def nested_get(payload: Mapping[str, Any], *keys: str) -> Any:
    value: Any = payload
    for key in keys:
        if not isinstance(value, Mapping):
            return None
        value = value.get(key)
    return value


def text_size(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value)
    if isinstance(value, bytes):
        return len(value)
    if isinstance(value, list):
        return sum(text_size(item) for item in value)
    if isinstance(value, dict):
        return sum(text_size(item) for item in value.values())
    return len(str(value))


def host_from_url(url: str) -> str:
    return urlparse(url).hostname or ""


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))

