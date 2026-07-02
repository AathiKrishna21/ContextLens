"""Typed models for live LLM request inspection."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class Provider(StrEnum):
    ANTHROPIC = "Anthropic"
    OPENAI = "OpenAI"
    BEDROCK = "Bedrock"
    UNKNOWN = "Unknown"


class PromptCategory(StrEnum):
    SYSTEM_PROMPT = "System Prompt"
    CONVERSATION = "Conversation"
    USER_PROMPT = "User Prompt"
    ASSISTANT_HISTORY = "Assistant History"
    TOOL_CALLS = "Tool Calls"
    TOOL_RESULTS = "Tool Results"
    RESOURCES = "Resources"
    FILES = "Files"
    STEERING = "Steering"
    SKILLS = "Skills"
    UNKNOWN = "Unknown"


class PromptBreakdown(BaseModel):
    token_counts: dict[PromptCategory, int] = Field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return sum(self.token_counts.values())

    def add(self, category: PromptCategory, tokens: int) -> None:
        self.token_counts[category] = self.token_counts.get(category, 0) + max(tokens, 0)


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated: bool = True


class LlmRequestRecord(BaseModel):
    request_number: int
    started_at: datetime
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider: Provider = Provider.UNKNOWN
    model: str = "unknown"
    method: str = "POST"
    url: str = ""
    status_code: int | None = None
    latency_seconds: float = 0.0
    usage: Usage = Field(default_factory=Usage)
    context_window: int | None = None
    estimated_cost_usd: float = 0.0
    prompt_breakdown: PromptBreakdown = Field(default_factory=PromptBreakdown)
    error: str | None = None

    @property
    def context_usage_percent(self) -> float:
        if not self.context_window:
            return 0.0
        return min((self.usage.prompt_tokens / self.context_window) * 100.0, 100.0)


class ProviderPricing(BaseModel):
    input_per_million: float
    output_per_million: float


class ProviderModelInfo(BaseModel):
    context_window: int | None = None
    pricing: ProviderPricing | None = None

