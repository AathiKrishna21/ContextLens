"""Mock capture strategy for dashboard and CLI testing."""

import asyncio

from contextlens_poc.capture.base import CaptureStrategy
from contextlens_poc.logging import get_logger
from contextlens_poc.models.connection import ConnectionMetadata

LOGGER = get_logger(__name__)


class MockCaptureStrategy(CaptureStrategy):
    """Return deterministic fake HTTP responses without upstream network access."""

    async def start(self) -> None:
        LOGGER.info("mock_strategy_started")

    async def handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        metadata: ConnectionMetadata,
    ) -> None:
        request_head = await reader.read(4096)
        LOGGER.info(
            "mock_connection_observed",
            connection_id=metadata.connection_id,
            bytes_received=len(request_head),
        )
        body = (
            b'{"id":"mock-response","object":"contextlens.poc.mock",'
            b'"message":"mock response from ContextLens PoC"}\n'
        )
        writer.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            + f"Content-Length: {len(body)}\r\n".encode("ascii")
            + b"Connection: close\r\n\r\n"
            + body
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def stop(self) -> None:
        LOGGER.info("mock_strategy_stopped")

