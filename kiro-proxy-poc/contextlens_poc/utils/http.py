"""Small HTTP parsing helpers for proxy request prefaces."""

from urllib.parse import urlsplit

from contextlens_poc.models.connection import ProxyRequest, ProxyRequestKind


def parse_proxy_request(raw_header: bytes) -> ProxyRequest:
    """Parse the initial HTTP proxy request header.

    This intentionally parses only the request preface and headers needed to route
    traffic. It does not inspect TLS payloads or proxy full HTTP semantics.
    """

    try:
        text = raw_header.decode("iso-8859-1")
        request_line = text.split("\r\n", 1)[0]
        method, target, http_version = request_line.split(" ", 2)
    except ValueError as exc:
        raise ValueError("invalid proxy request header") from exc

    header_host = _extract_header(text, "host")

    if method.upper() == "CONNECT":
        host, port = _parse_host_port(target, default_port=443)
        kind = ProxyRequestKind.CONNECT
    else:
        host, port = _route_http_target(target, header_host)
        kind = ProxyRequestKind.HTTP if host else ProxyRequestKind.UNKNOWN

    if not host:
        raise ValueError("unable to determine upstream host")

    return ProxyRequest(
        kind=kind,
        method=method.upper(),
        target=target,
        host=host,
        port=port,
        http_version=http_version,
        raw_header=raw_header,
    )


def rewrite_absolute_form_request(raw_header: bytes) -> bytes:
    """Rewrite HTTP proxy absolute-form requests into origin-form requests."""

    try:
        text = raw_header.decode("iso-8859-1")
        request_line, rest = text.split("\r\n", 1)
        method, target, http_version = request_line.split(" ", 2)
    except ValueError:
        return raw_header

    parsed = urlsplit(target)
    if not parsed.scheme or not parsed.netloc:
        return raw_header

    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    return f"{method} {path} {http_version}\r\n{rest}".encode("iso-8859-1")


def _extract_header(header_text: str, name: str) -> str | None:
    prefix = f"{name.lower()}:"
    for line in header_text.split("\r\n")[1:]:
        if line.lower().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


def _route_http_target(target: str, host_header: str | None) -> tuple[str, int]:
    parsed = urlsplit(target)
    if parsed.scheme and parsed.hostname:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return parsed.hostname, port

    if host_header:
        return _parse_host_port(host_header, default_port=80)

    return "", 0


def _parse_host_port(value: str, default_port: int) -> tuple[str, int]:
    if value.startswith("["):
        host, _, remainder = value[1:].partition("]")
        if remainder.startswith(":"):
            return host, int(remainder[1:])
        return host, default_port

    if ":" in value:
        host, port_text = value.rsplit(":", 1)
        return host, int(port_text)

    return value, default_port

