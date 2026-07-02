"""In-memory session statistics."""

from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timedelta, timezone
from statistics import mean

from kiro_live_inspector.models import LlmRequestRecord, Provider


class InspectorSession:
    """Thread-safe in-memory session state for the live dashboard."""

    def __init__(self, max_history: int = 500) -> None:
        self._lock = threading.RLock()
        self._records: deque[LlmRequestRecord] = deque(maxlen=max_history)
        self._next_request_number = 1

    def next_request_number(self) -> int:
        with self._lock:
            number = self._next_request_number
            self._next_request_number += 1
            return number

    def add_record(self, record: LlmRequestRecord) -> None:
        with self._lock:
            self._records.append(record)

    def records(self) -> list[LlmRequestRecord]:
        with self._lock:
            return list(self._records)

    def latest(self) -> LlmRequestRecord | None:
        with self._lock:
            return self._records[-1] if self._records else None

    def snapshot(self) -> "SessionSnapshot":
        records = self.records()
        total_prompt = sum(item.usage.prompt_tokens for item in records)
        total_completion = sum(item.usage.completion_tokens for item in records)
        total_cost = sum(item.estimated_cost_usd for item in records)
        latencies = [item.latency_seconds for item in records]
        prompt_sizes = [item.usage.prompt_tokens for item in records]
        completion_sizes = [item.usage.completion_tokens for item in records]
        now = datetime.now(timezone.utc)
        recent = [item for item in records if item.completed_at >= now - timedelta(minutes=1)]

        latest = records[-1] if records else None
        return SessionSnapshot(
            total_requests=len(records),
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_completion,
            total_tokens=total_prompt + total_completion,
            estimated_cost_usd=total_cost,
            largest_prompt=max(prompt_sizes, default=0),
            average_prompt_size=mean(prompt_sizes) if prompt_sizes else 0.0,
            average_completion_size=mean(completion_sizes) if completion_sizes else 0.0,
            average_latency_seconds=mean(latencies) if latencies else 0.0,
            requests_per_minute=len(recent),
            current_provider=latest.provider if latest else Provider.UNKNOWN,
            current_model=latest.model if latest else "unknown",
            latest=latest,
        )


class SessionSnapshot:
    def __init__(
        self,
        *,
        total_requests: int,
        total_prompt_tokens: int,
        total_completion_tokens: int,
        total_tokens: int,
        estimated_cost_usd: float,
        largest_prompt: int,
        average_prompt_size: float,
        average_completion_size: float,
        average_latency_seconds: float,
        requests_per_minute: int,
        current_provider: Provider,
        current_model: str,
        latest: LlmRequestRecord | None,
    ) -> None:
        self.total_requests = total_requests
        self.total_prompt_tokens = total_prompt_tokens
        self.total_completion_tokens = total_completion_tokens
        self.total_tokens = total_tokens
        self.estimated_cost_usd = estimated_cost_usd
        self.largest_prompt = largest_prompt
        self.average_prompt_size = average_prompt_size
        self.average_completion_size = average_completion_size
        self.average_latency_seconds = average_latency_seconds
        self.requests_per_minute = requests_per_minute
        self.current_provider = current_provider
        self.current_model = current_model
        self.latest = latest

