"""Async TCP proxy server."""

import asyncio
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from uuid import uuid4

from contextlens_poc.config import Settings
from contextlens_poc.logging import get_logger
from contextlens_poc.models.connection import ConnectionMetadata

LOGGER = get_logger(__name__)


class ProxyServer(AbstractAsyncContextManager["ProxyServer"]):
    """Small asyncio TCP server delegated to a capture strategy."""

    def __init__(self, settings: Settings, handler: object) -> None:
        self._settings = settings
        self._handler = handler
        self._server: asyncio.Server | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            host=self._settings.host,
            port=self._settings.port,
        )
        sockets = ", ".join(str(sock.getsockname()) for sock in self._server.sockets or [])
        LOGGER.info("proxy_server_started", sockets=sockets)

    async def serve_forever(self) -> None:
        if self._server is None:
            await self.start()
        assert self._server is not None
        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        if self._server is None:
            return
        self._server.close()
        await self._server.wait_closed()
        LOGGER.info("proxy_server_stopped")

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        peer = writer.get_extra_info("peername") or ("unknown", 0)
        metadata = ConnectionMetadata(
            connection_id=str(uuid4()),
            client_host=str(peer[0]),
            client_port=int(peer[1]),
        )
        await self._handler.handle_connection(reader, writer, metadata)

    async def __aenter__(self) -> "ProxyServer":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.stop()

