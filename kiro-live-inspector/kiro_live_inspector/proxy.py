"""Programmatic mitmproxy runner."""

from __future__ import annotations

import asyncio

from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster

from kiro_live_inspector.capture import KiroTrafficCapture
from kiro_live_inspector.session import InspectorSession


class MitmProxyRunner:
    """Run mitmproxy with the Kiro capture addon."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        session: InspectorSession,
        upstream_cert: bool = True,
    ) -> None:
        self._host = host
        self._port = port
        self._session = session
        self._upstream_cert = upstream_cert
        self._master: DumpMaster | None = None

    async def run(self) -> None:
        opts = options.Options(
            listen_host=self._host,
            listen_port=self._port,
            mode=["regular"],
            upstream_cert=self._upstream_cert,
        )
        master = DumpMaster(opts, with_termlog=False, with_dumper=False)
        master.addons.add(KiroTrafficCapture(self._session))
        self._master = master
        await master.run()

    async def shutdown(self) -> None:
        if self._master is not None:
            self._master.shutdown()
            await asyncio.sleep(0)

