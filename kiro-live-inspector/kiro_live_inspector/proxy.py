"""Programmatic mitmproxy runner."""

from __future__ import annotations

import asyncio
from pathlib import Path

from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from rich.console import Console

from kiro_live_inspector.capture import GenericHttpCapture


class MitmProxyRunner:
    """Run mitmproxy with the generic HTTP capture addon."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        capture_dir: Path,
        upstream_cert: bool = True,
        console: Console | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._capture_dir = capture_dir
        self._upstream_cert = upstream_cert
        self._console = console or Console()
        self._master: DumpMaster | None = None

    async def run(self) -> None:
        opts = options.Options(
            listen_host=self._host,
            listen_port=self._port,
            mode=["regular"],
            upstream_cert=self._upstream_cert,
        )
        master = DumpMaster(opts, with_termlog=False, with_dumper=False)
        master.addons.add(GenericHttpCapture(self._capture_dir, console=self._console))
        self._master = master
        await master.run()

    async def shutdown(self) -> None:
        if self._master is not None:
            self._master.shutdown()
            await asyncio.sleep(0)
