"""Offline replay capture strategy."""

import asyncio

import orjson

from contextlens_poc.capture.base import CaptureStrategy
from contextlens_poc.config import Settings
from contextlens_poc.logging import get_logger
from contextlens_poc.models.connection import ConnectionMetadata

LOGGER = get_logger(__name__)


class ReplayCaptureStrategy(CaptureStrategy):
    """Load previously recorded connection events without network forwarding."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def start(self) -> None:
        if not self._settings.replay_file:
            LOGGER.warning("replay_started_without_file")
            return

        LOGGER.info("replay_started", replay_file=str(self._settings.replay_file))
        with self._settings.replay_file.open("rb") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    event = orjson.loads(line)
                except orjson.JSONDecodeError as exc:
                    LOGGER.warning("replay_event_invalid", line=line_number, error=str(exc))
                    continue
                LOGGER.info("replay_event", line=line_number, event=event)

    async def handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        metadata: ConnectionMetadata,
    ) -> None:
        LOGGER.info("replay_rejecting_live_connection", connection_id=metadata.connection_id)
        writer.write(
            b"HTTP/1.1 503 Service Unavailable\r\n"
            b"Content-Type: text/plain\r\n"
            b"Connection: close\r\n\r\n"
            b"Replay strategy does not accept live network traffic.\n"
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def stop(self) -> None:
        LOGGER.info("replay_strategy_stopped")

