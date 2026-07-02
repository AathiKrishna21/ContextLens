"""Transparent HTTP and HTTPS CONNECT forwarding."""

import asyncio
import time

from contextlens_poc.config import Settings
from contextlens_poc.logging import get_logger
from contextlens_poc.models.connection import ConnectionMetadata, ConnectionResult, ProxyRequestKind
from contextlens_poc.proxy.connection import ByteCounters, relay_stream
from contextlens_poc.utils.http import parse_proxy_request, rewrite_absolute_form_request

LOGGER = get_logger(__name__)


class TunnelForwarder:
    """Forward HTTP proxy and HTTPS CONNECT traffic without TLS interception."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def forward(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        metadata: ConnectionMetadata,
    ) -> ConnectionResult:
        started = time.perf_counter()
        request = None
        counters = ByteCounters()

        try:
            raw_header = await asyncio.wait_for(
                reader.readuntil(b"\r\n\r\n"),
                timeout=self._settings.connect_timeout_seconds,
            )
            if len(raw_header) > self._settings.max_initial_request_bytes:
                raise ValueError("initial proxy request exceeds configured limit")

            request = parse_proxy_request(raw_header)
            upstream_reader, upstream_writer = await asyncio.wait_for(
                asyncio.open_connection(request.host, request.port),
                timeout=self._settings.connect_timeout_seconds,
            )

            if request.kind == ProxyRequestKind.CONNECT:
                writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await writer.drain()
            else:
                outbound_header = rewrite_absolute_form_request(raw_header)
                counters.client_to_upstream += len(outbound_header)
                upstream_writer.write(outbound_header)
                await upstream_writer.drain()

            await asyncio.wait_for(
                asyncio.gather(
                    relay_stream(
                        reader,
                        upstream_writer,
                        counter_name="client_to_upstream",
                        counters=counters,
                    ),
                    relay_stream(
                        upstream_reader,
                        writer,
                        counter_name="upstream_to_client",
                        counters=counters,
                    ),
                ),
                timeout=self._settings.idle_timeout_seconds,
            )

            return ConnectionResult(
                connection_id=metadata.connection_id,
                host=request.host,
                port=request.port,
                method=request.method,
                latency_seconds=time.perf_counter() - started,
                bytes_sent=counters.client_to_upstream,
                bytes_received=counters.upstream_to_client,
            )
        except Exception as exc:
            host = request.host if request else "unknown"
            port = request.port if request else 0
            method = request.method if request else "UNKNOWN"
            result = ConnectionResult(
                connection_id=metadata.connection_id,
                host=host,
                port=port,
                method=method,
                latency_seconds=time.perf_counter() - started,
                bytes_sent=counters.client_to_upstream,
                bytes_received=counters.upstream_to_client,
                error=str(exc),
            )
            LOGGER.warning("connection_failed", connection_id=metadata.connection_id, error=str(exc))
            return result
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

