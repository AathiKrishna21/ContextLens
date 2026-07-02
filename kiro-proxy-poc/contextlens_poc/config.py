"""Runtime configuration for the traffic capture PoC."""

from enum import StrEnum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CaptureStrategyName(StrEnum):
    TUNNEL = "tunnel"
    MITM = "mitm"
    REPLAY = "replay"
    MOCK = "mock"


class Settings(BaseSettings):
    """Configuration loaded from CLI options and environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="CONTEXTLENS_POC_",
        env_file=".env",
        extra="ignore",
    )

    host: str = Field(default="127.0.0.1", description="Proxy listen host.")
    port: int = Field(default=8080, ge=1, le=65535, description="Proxy listen port.")
    strategy: CaptureStrategyName = Field(default=CaptureStrategyName.TUNNEL)
    replay_file: Path | None = Field(
        default=None,
        description="Path to an ndjson replay file for replay strategy.",
    )
    log_level: str = Field(default="info", description="Structured log level.")
    connect_timeout_seconds: float = Field(default=10.0, gt=0)
    idle_timeout_seconds: float = Field(default=300.0, gt=0)
    max_initial_request_bytes: int = Field(default=1024 * 1024, gt=0)

