"""mitmproxy addon that captures LLM requests and responses."""

from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from mitmproxy import http

from kiro_live_inspector.models import LlmRequestRecord
from kiro_live_inspector.parser import LlmPayloadParser
from kiro_live_inspector.session import InspectorSession


class KiroTrafficCapture:
    """Capture mitmproxy HTTP flows and update the in-memory session."""

    def __init__(self, session: InspectorSession, parser: LlmPayloadParser | None = None) -> None:
        self._session = session
        self._parser = parser or LlmPayloadParser()
        self._flow_started: dict[str, float] = {}

    def request(self, flow: http.HTTPFlow) -> None:
        self._flow_started[flow.id] = perf_counter()

    def response(self, flow: http.HTTPFlow) -> None:
        if not self._looks_like_llm_flow(flow):
            return

        started = self._flow_started.pop(flow.id, perf_counter())
        latency = max(perf_counter() - started, 0.0)

        request_body = self._parser.parse_json_body(flow.request.raw_content)
        response_body = self._parser.parse_json_body(flow.response.raw_content if flow.response else None)
        provider = self._parser.detect_provider(flow.request.pretty_url, request_body)
        model = self._parser.model_name(request_body, response_body)
        usage = self._parser.usage(provider, request_body, response_body)
        breakdown = self._parser.prompt_breakdown(provider, request_body)
        context_window, cost = self._parser.complete_record_fields(provider, model, usage)

        record = LlmRequestRecord(
            request_number=self._session.next_request_number(),
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            provider=provider,
            model=model,
            method=flow.request.method,
            url=flow.request.pretty_url,
            status_code=flow.response.status_code if flow.response else None,
            latency_seconds=latency,
            usage=usage,
            context_window=context_window,
            estimated_cost_usd=cost,
            prompt_breakdown=breakdown,
        )
        self._session.add_record(record)

    def error(self, flow: http.HTTPFlow) -> None:
        if not self._looks_like_llm_flow(flow):
            return

        started = self._flow_started.pop(flow.id, perf_counter())
        request_body = self._parser.parse_json_body(flow.request.raw_content)
        provider = self._parser.detect_provider(flow.request.pretty_url, request_body)
        model = self._parser.model_name(request_body, {})
        usage = self._parser.usage(provider, request_body, {})
        breakdown = self._parser.prompt_breakdown(provider, request_body)
        context_window, cost = self._parser.complete_record_fields(provider, model, usage)

        self._session.add_record(
            LlmRequestRecord(
                request_number=self._session.next_request_number(),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                provider=provider,
                model=model,
                method=flow.request.method,
                url=flow.request.pretty_url,
                latency_seconds=max(perf_counter() - started, 0.0),
                usage=usage,
                context_window=context_window,
                estimated_cost_usd=cost,
                prompt_breakdown=breakdown,
                error=str(flow.error) if flow.error else "unknown flow error",
            )
        )

    def _looks_like_llm_flow(self, flow: http.HTTPFlow) -> bool:
        host = flow.request.host.lower()
        path = flow.request.path.lower()
        content_type = flow.request.headers.get("content-type", "").lower()

        provider_host = any(
            marker in host
            for marker in (
                "anthropic",
                "openai",
                "bedrock",
                "amazonaws.com",
            )
        )
        llm_path = any(
            marker in path
            for marker in (
                "/v1/messages",
                "/v1/chat/completions",
                "/v1/responses",
                "invoke-model",
                "converse",
            )
        )
        json_body = "json" in content_type or bool(flow.request.raw_content)
        return provider_host and llm_path and json_body

