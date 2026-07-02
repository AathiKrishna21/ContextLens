"""Model metadata and cost estimation."""

from __future__ import annotations

from kiro_live_inspector.models import Provider, ProviderModelInfo, ProviderPricing, Usage


MODEL_INFO: dict[str, ProviderModelInfo] = {
    "claude-3-5-sonnet": ProviderModelInfo(
        context_window=200_000,
        pricing=ProviderPricing(input_per_million=3.00, output_per_million=15.00),
    ),
    "claude-3-7-sonnet": ProviderModelInfo(
        context_window=200_000,
        pricing=ProviderPricing(input_per_million=3.00, output_per_million=15.00),
    ),
    "claude-sonnet-4": ProviderModelInfo(
        context_window=200_000,
        pricing=ProviderPricing(input_per_million=3.00, output_per_million=15.00),
    ),
    "gpt-4o": ProviderModelInfo(
        context_window=128_000,
        pricing=ProviderPricing(input_per_million=5.00, output_per_million=15.00),
    ),
    "gpt-4o-mini": ProviderModelInfo(
        context_window=128_000,
        pricing=ProviderPricing(input_per_million=0.15, output_per_million=0.60),
    ),
}

PROVIDER_DEFAULTS: dict[Provider, ProviderModelInfo] = {
    Provider.ANTHROPIC: ProviderModelInfo(
        context_window=200_000,
        pricing=ProviderPricing(input_per_million=3.00, output_per_million=15.00),
    ),
    Provider.OPENAI: ProviderModelInfo(
        context_window=128_000,
        pricing=ProviderPricing(input_per_million=5.00, output_per_million=15.00),
    ),
    Provider.BEDROCK: ProviderModelInfo(
        context_window=200_000,
        pricing=ProviderPricing(input_per_million=3.00, output_per_million=15.00),
    ),
}


def model_info(provider: Provider, model: str) -> ProviderModelInfo:
    model_lower = model.lower()
    for prefix, info in MODEL_INFO.items():
        if model_lower.startswith(prefix):
            return info
    return PROVIDER_DEFAULTS.get(provider, ProviderModelInfo())


def estimate_cost(provider: Provider, model: str, usage: Usage) -> float:
    info = model_info(provider, model)
    if not info.pricing:
        return 0.0
    input_cost = usage.prompt_tokens * info.pricing.input_per_million / 1_000_000
    output_cost = usage.completion_tokens * info.pricing.output_per_million / 1_000_000
    return input_cost + output_cost

