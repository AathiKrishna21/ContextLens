"""Tunnel capture strategy with HTTP proxy and HTTPS CONNECT forwarding."""

import asyncio

from rich.console import Console
from rich.panel import Panel

from contextlens_poc.capture.base import CaptureStrategy
from contextlens_poc.config import Settings
from contextlens_poc.logging import get_logger
from contextlens_poc.models.connection import ConnectionMetadata, ConnectionResult
from contextlens_poc.proxy.forwarder import TunnelForwarder

LOGGER = get_logger(__name__)


class TunnelCaptureStrategy(CaptureStrategy):
    """Validate whether clients honor HTTP_PROXY and HTTPS_PROXY."""

    def __init__(self, settings: Settings, console: Console | None = None) -> None:
        self._settings = settings
        self._forwarder = TunnelForwarder(settings)
        self._console = console or Console()

    async def start(self) -> None:
        LOGGER.info("tunnel_strategy_started", tls_interception=False)

    async def handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        metadata: ConnectionMetadata,
    ) -> None:
        result = await self._forwarder.forward(reader, writer, metadata)
        self._log_result(result)

    async def stop(self) -> None:
        LOGGER.info("tunnel_strategy_stopped")

    def _log_result(self, result: ConnectionResult) -> None:
        LOGGER.info(
            "connection_observed",
            connection_id=result.connection_id,
            host=result.host,
            port=result.port,
            method=result.method,
            latency_seconds=round(result.latency_seconds, 3),
            bytes_sent=result.bytes_sent,
            bytes_received=result.bytes_received,
            error=result.error,
        )

        status = "FAILED" if result.error else result.method
        body = "\n".join(
            [
                "[bold]New Connection[/bold]",
                f"Host: {result.host}",
                f"Port: {result.port}",
                f"Method: {status}",
                f"Latency: {result.latency_seconds:.3f}s",
                f"Bytes Sent: {result.bytes_sent}",
                f"Bytes Received: {result.bytes_received}",
                f"Error: {result.error}" if result.error else "",
            ]
        ).strip()
        self._console.print(Panel(body, title="ContextLens PoC", expand=False))

