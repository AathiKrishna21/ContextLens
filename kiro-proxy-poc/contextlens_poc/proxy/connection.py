"""Connection helpers for byte forwarding."""

import asyncio
from dataclasses import dataclass


@dataclass(slots=True)
class ByteCounters:
    client_to_upstream: int = 0
    upstream_to_client: int = 0


async def relay_stream(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    *,
    counter_name: str,
    counters: ByteCounters,
) -> None:
    """Relay bytes until EOF or connection failure."""

    try:
        while chunk := await reader.read(64 * 1024):
            if counter_name == "client_to_upstream":
                counters.client_to_upstream += len(chunk)
            else:
                counters.upstream_to_client += len(chunk)
            writer.write(chunk)
            await writer.drain()
    except (ConnectionError, asyncio.IncompleteReadError):
        return
    finally:
        writer.close()

