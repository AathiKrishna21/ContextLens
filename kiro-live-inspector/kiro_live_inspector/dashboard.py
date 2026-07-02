"""Rich live terminal dashboard."""

from __future__ import annotations

import asyncio

from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from kiro_live_inspector.models import LlmRequestRecord, PromptCategory
from kiro_live_inspector.session import InspectorSession
from kiro_live_inspector.utils import clamp


class LiveDashboard:
    """Continuously render session state."""

    def __init__(self, session: InspectorSession, refresh_seconds: float = 0.5) -> None:
        self._session = session
        self._refresh_seconds = refresh_seconds
        self._show_history = False

    async def run(self) -> None:
        with Live(self._render(), refresh_per_second=4, screen=True) as live:
            while True:
                live.update(self._render())
                await asyncio.sleep(self._refresh_seconds)

    def toggle_history(self) -> None:
        self._show_history = not self._show_history

    def _render(self) -> Panel:
        snapshot = self._session.snapshot()
        latest = snapshot.latest

        header = Align.center(Text("Kiro Live Inspector", style="bold cyan"))
        current = self._current_table(latest)
        session = self._session_table()
        breakdown = self._breakdown_table(latest)
        history = self._history_table() if self._show_history else Text(
            "Press Enter to toggle request history. Press Ctrl+C to exit.",
            style="dim",
        )
        return Panel(
            Group(header, current, breakdown, session, history),
            border_style="cyan",
        )

    def _current_table(self, latest: LlmRequestRecord | None) -> Table:
        table = Table(title="Current Request", expand=True)
        table.add_column("Metric", style="bold")
        table.add_column("Value")

        if not latest:
            for name in (
                "Provider",
                "Model",
                "Context",
                "Prompt",
                "Completion",
                "Session Total",
                "Estimated Cost",
                "Latency",
                "Requests",
                "RPM",
            ):
                table.add_row(name, "-")
            return table

        snapshot = self._session.snapshot()
        context_percent = latest.context_usage_percent
        table.add_row("Provider", latest.provider.value)
        table.add_row("Model", latest.model)
        table.add_row(
            "Context",
            f"{context_percent:.1f}% " + self._bar(context_percent),
        )
        table.add_row("Prompt", f"{latest.usage.prompt_tokens:,}")
        table.add_row("Completion", f"{latest.usage.completion_tokens:,}")
        table.add_row("Session Total", f"{snapshot.total_tokens:,}")
        table.add_row("Estimated Cost", f"${snapshot.estimated_cost_usd:.4f}")
        table.add_row("Latency", f"{latest.latency_seconds:.3f}s")
        table.add_row("Requests", f"{snapshot.total_requests:,}")
        table.add_row("RPM", f"{snapshot.requests_per_minute:,}")
        return table

    def _breakdown_table(self, latest: LlmRequestRecord | None) -> Table:
        table = Table(title="Prompt Breakdown", expand=True)
        table.add_column("Category")
        table.add_column("Tokens", justify="right")
        table.add_column("Share", justify="right")

        if not latest or not latest.prompt_breakdown.token_counts:
            table.add_row("No intercepted request yet", "-", "-")
            return table

        total = latest.prompt_breakdown.total_tokens or 1
        for category in PromptCategory:
            tokens = latest.prompt_breakdown.token_counts.get(category, 0)
            if tokens <= 0:
                continue
            table.add_row(category.value, f"{tokens:,}", f"{tokens / total:.0%}")
        return table

    def _session_table(self) -> Table:
        snapshot = self._session.snapshot()
        table = Table(title="Session", expand=True)
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")
        table.add_row("Total Requests", f"{snapshot.total_requests:,}")
        table.add_row("Total Prompt Tokens", f"{snapshot.total_prompt_tokens:,}")
        table.add_row("Total Completion Tokens", f"{snapshot.total_completion_tokens:,}")
        table.add_row("Total Tokens", f"{snapshot.total_tokens:,}")
        table.add_row("Estimated Cost", f"${snapshot.estimated_cost_usd:.4f}")
        table.add_row("Largest Prompt", f"{snapshot.largest_prompt:,}")
        table.add_row("Average Prompt Size", f"{snapshot.average_prompt_size:,.1f}")
        table.add_row("Average Completion Size", f"{snapshot.average_completion_size:,.1f}")
        table.add_row("Average Latency", f"{snapshot.average_latency_seconds:.3f}s")
        return table

    def _history_table(self) -> Table:
        table = Table(title="Request History", expand=True)
        table.add_column("#", justify="right")
        table.add_column("Time")
        table.add_column("Prompt", justify="right")
        table.add_column("Completion", justify="right")
        table.add_column("Latency", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Provider")
        table.add_column("Model")

        for record in self._session.records()[-20:]:
            table.add_row(
                str(record.request_number),
                record.completed_at.strftime("%H:%M:%S"),
                f"{record.usage.prompt_tokens:,}",
                f"{record.usage.completion_tokens:,}",
                f"{record.latency_seconds:.2f}s",
                f"${record.estimated_cost_usd:.4f}",
                record.provider.value,
                record.model,
            )
        return table

    def _bar(self, percent: float) -> str:
        width = 18
        filled = round(clamp(percent, 0, 100) / 100 * width)
        return "[" + "#" * filled + "-" * (width - filled) + "]"
