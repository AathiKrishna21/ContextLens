"""Command line interface."""

from __future__ import annotations

import asyncio
import contextlib
import threading

import typer
from rich.console import Console

from kiro_live_inspector.dashboard import LiveDashboard
from kiro_live_inspector.proxy import MitmProxyRunner
from kiro_live_inspector.session import InspectorSession

app = typer.Typer(help="Live terminal inspector for Kiro CLI LLM traffic.")
console = Console()


@app.command()
def run(
    host: str = typer.Option("127.0.0.1", "--host", help="MITM proxy listen host."),
    port: int = typer.Option(8080, "--port", help="MITM proxy listen port."),
    no_upstream_cert: bool = typer.Option(
        False,
        "--no-upstream-cert",
        help="Disable upstream certificate sniffing in mitmproxy.",
    ),
) -> None:
    """Run the live inspector."""

    asyncio.run(_run(host=host, port=port, upstream_cert=not no_upstream_cert))


async def _run(host: str, port: int, upstream_cert: bool) -> None:
    session = InspectorSession()
    proxy = MitmProxyRunner(host=host, port=port, session=session, upstream_cert=upstream_cert)
    dashboard = LiveDashboard(session)
    stop_input = threading.Event()

    console.print(f"[bold cyan]Kiro Live Inspector[/bold cyan] listening on {host}:{port}")
    console.print("Configure Kiro with:")
    console.print(f"  HTTP_PROXY=http://{host}:{port}")
    console.print(f"  HTTPS_PROXY=http://{host}:{port}")

    input_thread = threading.Thread(
        target=_history_toggle_loop,
        args=(dashboard, stop_input),
        daemon=True,
    )
    input_thread.start()

    proxy_task = asyncio.create_task(proxy.run())
    dashboard_task = asyncio.create_task(dashboard.run())

    try:
        await asyncio.gather(proxy_task, dashboard_task)
    except KeyboardInterrupt:
        console.print("[yellow]Shutting down...[/yellow]")
    finally:
        await proxy.shutdown()
        stop_input.set()
        for task in (proxy_task, dashboard_task):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


def _history_toggle_loop(dashboard: LiveDashboard, stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        try:
            input()
        except EOFError:
            return
        dashboard.toggle_history()
