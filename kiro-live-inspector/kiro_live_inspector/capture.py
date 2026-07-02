"""Generic mitmproxy HTTP capture addon.

This module intentionally avoids provider-specific assumptions. It captures every
HTTP flow mitmproxy gives us and persists request/response bodies for protocol
reverse engineering.
"""

from __future__ import annotations

import gzip
import itertools
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

import orjson
from mitmproxy import http
from rich.console import Console
from rich.panel import Panel


@dataclass(frozen=True, slots=True)
class BodyCapture:
    kind: str
    size: int
    path: Path
    top_level_keys: list[str]
    decompressed: bool
    decode_error: str | None = None


class GenericHttpCapture:
    """Capture every HTTP request and response body to disk."""

    def __init__(self, capture_dir: Path, console: Console | None = None) -> None:
        self._capture_dir = capture_dir
        self._console = console or Console()
        self._counter = itertools.count(1)
        self._flow_started: dict[str, float] = {}
        self._flow_numbers: dict[str, int] = {}

    def load(self, loader: Any) -> None:
        self._capture_dir.mkdir(parents=True, exist_ok=True)

    def request(self, flow: http.HTTPFlow) -> None:
        number = next(self._counter)
        self._flow_numbers[flow.id] = number
        self._flow_started[flow.id] = perf_counter()

    def response(self, flow: http.HTTPFlow) -> None:
        number = self._flow_numbers.pop(flow.id, next(self._counter))
        started = self._flow_started.pop(flow.id, perf_counter())
        latency_seconds = max(perf_counter() - started, 0.0)

        request_capture = self._capture_message("request", number, flow.request)
        response_capture = self._capture_message("response", number, flow.response)
        self._print_summary(
            flow=flow,
            number=number,
            request_capture=request_capture,
            response_capture=response_capture,
            latency_seconds=latency_seconds,
            error=None,
        )

    def error(self, flow: http.HTTPFlow) -> None:
        number = self._flow_numbers.pop(flow.id, next(self._counter))
        started = self._flow_started.pop(flow.id, perf_counter())
        latency_seconds = max(perf_counter() - started, 0.0)

        request_capture = self._capture_message("request", number, flow.request)
        response_capture = None
        if flow.response is not None:
            response_capture = self._capture_message("response", number, flow.response)

        self._print_summary(
            flow=flow,
            number=number,
            request_capture=request_capture,
            response_capture=response_capture,
            latency_seconds=latency_seconds,
            error=str(flow.error) if flow.error else "unknown mitmproxy flow error",
        )

    def _capture_message(
        self,
        prefix: str,
        number: int,
        message: http.Message | None,
    ) -> BodyCapture:
        if message is None:
            body = b""
            content_type = ""
            content_encoding = ""
        else:
            body = message.raw_content or b""
            content_type = message.headers.get("content-type", "")
            content_encoding = message.headers.get("content-encoding", "")

        decoded_body, decompressed, decode_error = self._decode_body(body, content_encoding)
        json_value = self._try_json(decoded_body)

        if json_value is not None:
            output_path = self._capture_dir / f"{prefix}_{number:04d}.json"
            output_path.write_bytes(orjson.dumps(json_value, option=orjson.OPT_INDENT_2))
            keys = list(json_value.keys()) if isinstance(json_value, dict) else []
            return BodyCapture(
                kind="json",
                size=len(body),
                path=output_path,
                top_level_keys=keys,
                decompressed=decompressed,
                decode_error=decode_error,
            )

        output_path = self._capture_dir / f"{prefix}_{number:04d}.bin"
        output_path.write_bytes(decoded_body if decompressed else body)
        return BodyCapture(
            kind=self._body_kind(decoded_body, content_type),
            size=len(body),
            path=output_path,
            top_level_keys=[],
            decompressed=decompressed,
            decode_error=decode_error,
        )

    def _decode_body(self, body: bytes, content_encoding: str) -> tuple[bytes, bool, str | None]:
        if not body:
            return body, False, None

        encoding = content_encoding.lower().strip()
        try:
            if "gzip" in encoding:
                return gzip.decompress(body), True, None
            if "deflate" in encoding:
                return zlib.decompress(body), True, None
            if "br" in encoding:
                try:
                    import brotli  # type: ignore[import-not-found]
                except ImportError:
                    return body, False, "brotli module unavailable"
                return brotli.decompress(body), True, None
        except Exception as exc:
            return body, False, str(exc)

        return body, False, None

    def _try_json(self, body: bytes) -> Any | None:
        if not body:
            return None
        try:
            return orjson.loads(body)
        except orjson.JSONDecodeError:
            return None

    def _body_kind(self, body: bytes, content_type: str) -> str:
        if not body:
            return "empty"
        lowered = content_type.lower()
        if lowered.startswith("text/") or "xml" in lowered or "html" in lowered:
            return "text"
        try:
            body.decode("utf-8")
        except UnicodeDecodeError:
            return "binary"
        return "text"

    def _print_summary(
        self,
        *,
        flow: http.HTTPFlow,
        number: int,
        request_capture: BodyCapture,
        response_capture: BodyCapture | None,
        latency_seconds: float,
        error: str | None,
    ) -> None:
        response_size = response_capture.size if response_capture else 0
        response_kind = response_capture.kind if response_capture else "missing"
        top_level_keys = sorted(
            set(request_capture.top_level_keys)
            | set(response_capture.top_level_keys if response_capture else [])
        )

        lines = [
            f"Capture: {number:04d}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            f"Host: {flow.request.host}",
            f"Method: {flow.request.method}",
            f"Path: {flow.request.path}",
            f"Content-Type: {flow.request.headers.get('content-type', '')}",
            f"Content-Encoding: {flow.request.headers.get('content-encoding', '')}",
            f"Request Size: {request_capture.size}",
            f"Response Size: {response_size}",
            f"Latency: {latency_seconds:.3f}s",
            f"Body Type: request={request_capture.kind}, response={response_kind}",
            "Top-level JSON keys: " + (", ".join(top_level_keys) if top_level_keys else "-"),
            f"Request File: {request_capture.path}",
            f"Response File: {response_capture.path if response_capture else '-'}",
        ]
        if request_capture.decompressed or (response_capture and response_capture.decompressed):
            lines.append("Decompressed: yes")
        if request_capture.decode_error:
            lines.append(f"Request Decode Error: {request_capture.decode_error}")
        if response_capture and response_capture.decode_error:
            lines.append(f"Response Decode Error: {response_capture.decode_error}")
        if error:
            lines.append(f"Error: {error}")

        self._console.print(Panel("\n".join(lines), title="HTTP Capture", border_style="cyan"))
