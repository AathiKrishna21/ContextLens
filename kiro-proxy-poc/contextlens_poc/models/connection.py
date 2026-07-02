"""Connection-level models captured by the proxy PoC."""

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class ProxyRequestKind(StrEnum):
    CONNECT = "CONNECT"
    HTTP = "HTTP"
    UNKNOWN = "UNKNOWN"


class ProxyRequest(BaseModel):
    kind: ProxyRequestKind
    method: str
    target: str
    host: str
    port: int
    http_version: str = "HTTP/1.1"
    raw_header: bytes


class ConnectionMetadata(BaseModel):
    connection_id: str
    client_host: str
    client_port: int
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionResult(BaseModel):
    connection_id: str
    host: str
    port: int
    method: str
    latency_seconds: float
    bytes_sent: int = 0
    bytes_received: int = 0
    error: str | None = None

