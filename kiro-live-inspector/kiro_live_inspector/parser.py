"""Provider detection, usage extraction, and prompt breakdown heuristics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import orjson

from kiro_live_inspector.metrics import estimate_cost, model_info
from kiro_live_inspector.models import PromptBreakdown, PromptCategory, Provider, Usage
from kiro_live_inspector.tokenizer import TokenCounter
from kiro_live_inspector.utils import host_from_url


class LlmPayloadParser:
    """Parse intercepted LLM payloads using deterministic provider heuristics."""

    def __init__(self, token_counter: TokenCounter | None = None) -> None:
        self._tokens = token_counter or TokenCounter()

    def parse_json_body(self, content: bytes | None) -> dict[str, Any]:
        if not content:
            return {}
        try:
            parsed = orjson.loads(content)
        except orjson.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def detect_provider(self, url: str, request_body: Mapping[str, Any]) -> Provider:
        host = host_from_url(url).lower()
        if "anthropic" in host or "claude" in str(request_body.get("model", "")).lower():
            return Provider.ANTHROPIC
        if "openai" in host or str(request_body.get("model", "")).lower().startswith("gpt-"):
            return Provider.OPENAI
        if "bedrock" in host or "amazonaws.com" in host:
            return Provider.BEDROCK
        return Provider.UNKNOWN

    def model_name(self, request_body: Mapping[str, Any], response_body: Mapping[str, Any]) -> str:
        model = request_body.get("model") or response_body.get("model")
        return str(model) if model else "unknown"

    def usage(
        self,
        provider: Provider,
        request_body: Mapping[str, Any],
        response_body: Mapping[str, Any],
    ) -> Usage:
        provider_usage = self._provider_usage(provider, response_body)
        if provider_usage:
            return provider_usage

        prompt_tokens = self._tokens.count_jsonish(request_body)
        completion_tokens = self._tokens.count_jsonish(self._response_text(provider, response_body))
        return Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated=True,
        )

    def prompt_breakdown(self, provider: Provider, request_body: Mapping[str, Any]) -> PromptBreakdown:
        breakdown = PromptBreakdown()
        match provider:
            case Provider.ANTHROPIC:
                self._anthropic_breakdown(request_body, breakdown)
            case Provider.OPENAI:
                self._openai_breakdown(request_body, breakdown)
            case Provider.BEDROCK:
                self._bedrock_breakdown(request_body, breakdown)
            case Provider.UNKNOWN:
                breakdown.add(PromptCategory.UNKNOWN, self._tokens.count_jsonish(request_body))
        return breakdown

    def complete_record_fields(
        self,
        provider: Provider,
        model: str,
        usage: Usage,
    ) -> tuple[int | None, float]:
        info = model_info(provider, model)
        return info.context_window, estimate_cost(provider, model, usage)

    def _provider_usage(self, provider: Provider, body: Mapping[str, Any]) -> Usage | None:
        if not body:
            return None

        if provider is Provider.ANTHROPIC:
            usage = body.get("usage")
            if isinstance(usage, Mapping):
                input_tokens = int(usage.get("input_tokens") or 0)
                output_tokens = int(usage.get("output_tokens") or 0)
                return Usage(
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    estimated=False,
                )

        if provider is Provider.OPENAI:
            usage = body.get("usage")
            if isinstance(usage, Mapping):
                prompt_tokens = int(usage.get("prompt_tokens") or 0)
                completion_tokens = int(usage.get("completion_tokens") or 0)
                total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
                return Usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    estimated=False,
                )

        if provider is Provider.BEDROCK:
            usage = body.get("usage") or body.get("amazon-bedrock-invocationMetrics")
            if isinstance(usage, Mapping):
                prompt_tokens = int(usage.get("inputTokenCount") or usage.get("input_tokens") or 0)
                completion_tokens = int(
                    usage.get("outputTokenCount") or usage.get("output_tokens") or 0
                )
                return Usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    estimated=False,
                )

        return None

    def _anthropic_breakdown(
        self,
        body: Mapping[str, Any],
        breakdown: PromptBreakdown,
    ) -> None:
        breakdown.add(PromptCategory.SYSTEM_PROMPT, self._tokens.count_jsonish(body.get("system")))
        tools = body.get("tools")
        breakdown.add(PromptCategory.TOOL_CALLS, self._tokens.count_jsonish(tools))

        messages = body.get("messages")
        if not isinstance(messages, list):
            breakdown.add(PromptCategory.UNKNOWN, self._tokens.count_jsonish(body))
            return

        for message in messages:
            if not isinstance(message, Mapping):
                breakdown.add(PromptCategory.UNKNOWN, self._tokens.count_jsonish(message))
                continue
            role = str(message.get("role", "")).lower()
            content = message.get("content")
            category = self._message_category(role, content)
            breakdown.add(category, self._tokens.count_jsonish(content))

    def _openai_breakdown(
        self,
        body: Mapping[str, Any],
        breakdown: PromptBreakdown,
    ) -> None:
        tools = body.get("tools") or body.get("functions")
        breakdown.add(PromptCategory.TOOL_CALLS, self._tokens.count_jsonish(tools))

        messages = body.get("messages") or body.get("input")
        if not isinstance(messages, list):
            breakdown.add(PromptCategory.UNKNOWN, self._tokens.count_jsonish(body))
            return

        for message in messages:
            if not isinstance(message, Mapping):
                breakdown.add(PromptCategory.CONVERSATION, self._tokens.count_jsonish(message))
                continue
            role = str(message.get("role", "")).lower()
            content = message.get("content")
            category = self._message_category(role, content)
            breakdown.add(category, self._tokens.count_jsonish(content))

    def _bedrock_breakdown(
        self,
        body: Mapping[str, Any],
        breakdown: PromptBreakdown,
    ) -> None:
        if "system" in body:
            breakdown.add(PromptCategory.SYSTEM_PROMPT, self._tokens.count_jsonish(body.get("system")))
        if "messages" in body:
            self._anthropic_breakdown(body, breakdown)
        else:
            breakdown.add(PromptCategory.UNKNOWN, self._tokens.count_jsonish(body))

    def _message_category(self, role: str, content: Any) -> PromptCategory:
        content_text = str(content).lower()
        if role == "system":
            return PromptCategory.SYSTEM_PROMPT
        if role == "assistant":
            return PromptCategory.ASSISTANT_HISTORY
        if role == "tool":
            return PromptCategory.TOOL_RESULTS
        if "tool_result" in content_text:
            return PromptCategory.TOOL_RESULTS
        if "tool_use" in content_text:
            return PromptCategory.TOOL_CALLS
        if "file" in content_text or "path" in content_text:
            return PromptCategory.FILES
        if "resource" in content_text:
            return PromptCategory.RESOURCES
        if "steering" in content_text:
            return PromptCategory.STEERING
        if "skill" in content_text:
            return PromptCategory.SKILLS
        if role == "user":
            return PromptCategory.USER_PROMPT
        return PromptCategory.CONVERSATION

    def _response_text(self, provider: Provider, body: Mapping[str, Any]) -> Any:
        if provider is Provider.ANTHROPIC:
            return body.get("content")
        if provider is Provider.OPENAI:
            return body.get("choices") or body.get("output")
        return body

