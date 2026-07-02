"""Typer command line interface for the proxy PoC."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from contextlens_poc.capture.base import CaptureStrategy
from contextlens_poc.capture.mitm import MitmCaptureStrategy
from contextlens_poc.capture.mock import MockCaptureStrategy
from contextlens_poc.capture.replay import ReplayCaptureStrategy
from contextlens_poc.capture.tunnel import TunnelCaptureStrategy
from contextlens_poc.config import CaptureStrategyName, Settings
from contextlens_poc.logging import configure_logging, get_logger
from contextlens_poc.proxy.server import ProxyServer

app = typer.Typer(help="ContextLens traffic capture proof of concept.")
console = Console()


@app.command()
def run(
    strategy: CaptureStrategyName = typer.Option(
        CaptureStrategyName.TUNNEL,
        "--strategy",
        "-s",
        help="Capture strategy to run.",
    ),
    host: str = typer.Option("127.0.0.1", "--host", help="Listen host."),
    port: int = typer.Option(8080, "--port", help="Listen port."),
    replay_file: Path | None = typer.Option(None, "--replay-file", help="Replay ndjson file."),
    log_level: str = typer.Option("info", "--log-level", help="Log level."),
) -> None:
    """Run a capture strategy."""

    settings = Settings(
        strategy=strategy,
        host=host,
        port=port,
        replay_file=replay_file,
        log_level=log_level,
    )
    configure_logging(settings.log_level)
    asyncio.run(_run_async(settings))


async def _run_async(settings: Settings) -> None:
    logger = get_logger(__name__)
    strategy = _build_strategy(settings)

    console.print(
        f"[bold green]ContextLens PoC[/bold green] strategy={settings.strategy} "
        f"listening={settings.host}:{settings.port}"
    )
    console.print(f"Set HTTP_PROXY=http://{settings.host}:{settings.port}")
    console.print(f"Set HTTPS_PROXY=http://{settings.host}:{settings.port}")

    await strategy.start()
    server = ProxyServer(settings, strategy)

    try:
        await server.serve_forever()
    except KeyboardInterrupt:
        logger.info("shutdown_requested")
    finally:
        await server.stop()
        await strategy.stop()


def _build_strategy(settings: Settings) -> CaptureStrategy:
    match settings.strategy:
        case CaptureStrategyName.TUNNEL:
            return TunnelCaptureStrategy(settings, console=console)
        case CaptureStrategyName.MITM:
            return MitmCaptureStrategy(settings)
        case CaptureStrategyName.REPLAY:
            return ReplayCaptureStrategy(settings)
        case CaptureStrategyName.MOCK:
            return MockCaptureStrategy()

