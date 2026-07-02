"""Abstract capture strategy contract."""

import asyncio
from abc import ABC, abstractmethod

from contextlens_poc.models.connection import ConnectionMetadata


class CaptureStrategy(ABC):
    """Strategy interface for traffic capture experiments."""

    @abstractmethod
    async def start(self) -> None:
        """Prepare strategy resources."""

    @abstractmethod
    async def handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        metadata: ConnectionMetadata,
    ) -> None:
        """Handle a single inbound client connection."""

    @abstractmethod
    async def stop(self) -> None:
        """Release strategy resources."""

