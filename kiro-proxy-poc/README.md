# Kiro Proxy PoC

This repository is an engineering Proof of Concept for ContextLens traffic capture.

It does not build ContextLens. It answers one question:

> Can modern AI coding assistants, starting with Kiro CLI, be observed locally through a proxy architecture?

The code is intentionally modular so successful pieces can later evolve into a ContextLens proxy adapter.

## Goals

- Validate whether Kiro CLI honors `HTTP_PROXY` and `HTTPS_PROXY`.
- Validate whether HTTPS `CONNECT` requests can be observed.
- Capture connection metadata without TLS interception.
- Prepare a clean architecture for future MITM request inspection.
- Support replay and mock modes for offline experimentation.

## Non-Goals

This PoC does not implement:

- SQLite
- Dashboard
- REST API
- Web UI
- Plugins
- Authentication
- Configuration UI
- Recommendation engine
- Token analysis
- Prompt analysis
- Cost analysis

## Architecture

```text
contextlens_poc/
    main.py
    cli.py
    config.py
    logging.py
    capture/
        base.py
        tunnel.py
        mitm.py
        replay.py
        mock.py
    proxy/
        server.py
        forwarder.py
        connection.py
    models/
    utils/
```

All capture modes implement the same strategy interface:

```python
class CaptureStrategy:
    async def start()
    async def handle_connection(...)
    async def stop()
```

## Capture Strategies

### Tunnel

Tunnel mode implements an HTTP proxy with HTTPS `CONNECT` support.

It forwards traffic transparently and logs:

- Destination host
- Destination port
- Method, including `CONNECT`
- Latency
- Bytes sent
- Bytes received

It does not decrypt TLS.

Use this mode to answer:

> Does Kiro actually use the proxy?

### MITM

MITM mode is a scaffold only.

Certificate generation, trust-store installation, per-host leaf certificates, TLS termination, and request inspection are intentionally left as TODOs. The class exists to prove the architecture can accept MITM later without replacing the capture strategy abstraction.

For now, MITM mode falls back to tunnel forwarding.

### Replay

Replay mode loads previously recorded newline-delimited JSON events.

It does not use the network and rejects live client traffic. Use it for offline development of future analysis or UI surfaces.

### Mock

Mock mode returns deterministic fake JSON responses.

It is useful for testing future CLI and dashboard flows without contacting an upstream provider.

## Install

From this directory:

```powershell
cd C:\Aathi\ContextLens\kiro-proxy-poc
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

On macOS or Linux:

```bash
cd kiro-proxy-poc
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Run

Tunnel mode:

```bash
contextlens-poc run --strategy tunnel --host 127.0.0.1 --port 8080
```

MITM scaffold:

```bash
contextlens-poc run --strategy mitm
```

Replay mode:

```bash
contextlens-poc run --strategy replay --replay-file sessions.ndjson
```

Mock mode:

```bash
contextlens-poc run --strategy mock
```

## Configure Proxy Environment Variables

PowerShell:

```powershell
$env:HTTP_PROXY = "http://127.0.0.1:8080"
$env:HTTPS_PROXY = "http://127.0.0.1:8080"
```

macOS or Linux:

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
```

Some tools use lowercase variables:

```bash
export http_proxy=http://127.0.0.1:8080
export https_proxy=http://127.0.0.1:8080
```

## Test With curl

Start tunnel mode:

```bash
contextlens-poc run --strategy tunnel --port 8080
```

In another terminal:

```bash
curl -x http://127.0.0.1:8080 https://api.anthropic.com/
```

Expected result:

- The curl request may fail at the provider level because no API request is being made.
- The proxy should still log a `CONNECT` connection to `api.anthropic.com:443`.

You can also test plain HTTP:

```bash
curl -x http://127.0.0.1:8080 http://example.com/
```

## Test With Kiro CLI

1. Start the proxy:

   ```bash
   contextlens-poc run --strategy tunnel --host 127.0.0.1 --port 8080
   ```

2. Configure proxy variables in the same shell that launches Kiro:

   PowerShell:

   ```powershell
   $env:HTTP_PROXY = "http://127.0.0.1:8080"
   $env:HTTPS_PROXY = "http://127.0.0.1:8080"
   ```

   macOS or Linux:

   ```bash
   export HTTP_PROXY=http://127.0.0.1:8080
   export HTTPS_PROXY=http://127.0.0.1:8080
   ```

3. Run a normal Kiro CLI workflow.

4. Watch the proxy output.

Success looks like a connection panel similar to:

```text
New Connection
Host: api.anthropic.com
Port: 443
Method: CONNECT
Latency: 1.800s
Bytes Sent: 4212
Bytes Received: 12521
```

If no connection appears, Kiro may not be using standard proxy environment variables, or it may require different network configuration.

## What Success Means

This PoC succeeds if tunnel mode can show:

- Kiro opens connections through the local proxy.
- HTTPS requests appear as `CONNECT host:443`.
- Destination metadata can be captured.
- Latency and byte counts can be measured.
- Traffic can be forwarded without breaking the client workflow.

This would support a `YES` answer for a proxy-based ContextLens capture architecture.

## What Failure Means

If Kiro does not connect through the proxy, the result is still useful.

It may mean ContextLens needs:

- SDK-level instrumentation.
- Client-specific configuration.
- Local DNS or system proxy approaches.
- OS-level packet capture.
- A different adapter strategy for Kiro.

## Known Limitations

- TLS is not intercepted.
- Request and response bodies are not visible for HTTPS traffic.
- MITM certificate handling is not implemented.
- HTTP parsing is intentionally minimal.
- Proxy authentication is not implemented.
- SOCKS proxies are not implemented.
- HTTP/2 CONNECT behavior is not explicitly handled.
- Replay format is intentionally loose during the PoC phase.

## Next Steps

1. Run tunnel mode with curl.
2. Run tunnel mode with Kiro CLI.
3. Record whether Kiro uses `HTTP_PROXY` or `HTTPS_PROXY`.
4. If Kiro uses the proxy, add structured event recording.
5. If request inspection is required, implement MITM certificate generation and trust setup.
6. If Kiro does not use the proxy, evaluate SDK, system proxy, or packet capture strategies.

