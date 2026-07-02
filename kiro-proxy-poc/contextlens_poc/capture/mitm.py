"""MITM capture strategy scaffold.

This module intentionally does not implement certificate generation or TLS
interception yet. It defines the extension points needed to add that capability
without redesigning the capture architecture.
"""

import asyncio

from contextlens_poc.capture.base import CaptureStrategy
from contextlens_poc.config import Settings
from contextlens_poc.logging import get_logger
from contextlens_poc.models.connection import ConnectionMetadata
from contextlens_poc.proxy.forwarder import TunnelForwarder

LOGGER = get_logger(__name__)


class MitmCaptureStrategy(CaptureStrategy):
    """Prepared architecture for future TLS interception."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._fallback_tunnel = TunnelForwarder(settings)

    async def start(self) -> None:
        LOGGER.warning(
            "mitm_strategy_scaffold_started",
            certificate_generation=False,
            tls_interception=False,
        )
        # TODO: Add local CA generation and trust-store installation guidance.
        # TODO: Add per-host leaf certificate generation and cache.
        # TODO: Add TLS termination from client and TLS initiation to upstream.
        # TODO: Add HTTP request/response inspection after TLS termination.

    async def handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        metadata: ConnectionMetadata,
    ) -> None:
        LOGGER.info(
            "mitm_not_implemented_falling_back_to_tunnel",
            connection_id=metadata.connection_id,
        )
        result = await self._fallback_tunnel.forward(reader, writer, metadata)
        LOGGER.info(
            "mitm_fallback_connection_observed",
            connection_id=result.connection_id,
            host=result.host,
            port=result.port,
            method=result.method,
            latency_seconds=round(result.latency_seconds, 3),
            bytes_sent=result.bytes_sent,
            bytes_received=result.bytes_received,
            error=result.error,
        )

    async def stop(self) -> None:
        LOGGER.info("mitm_strategy_stopped")

