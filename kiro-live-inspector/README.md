# Kiro Live Inspector

Kiro Live Inspector is a standalone developer utility for watching Kiro CLI LLM traffic in a live terminal dashboard.

It is not ContextLens. It is not a plugin system. It is not a web application. It is a focused experiment: can Kiro CLI be observed through a local HTTPS MITM proxy, and can prompt usage be displayed live?

## What It Shows

Every intercepted LLM request updates an in-memory dashboard with:

- Current provider
- Current model
- Current request tokens
- Current response tokens
- Running session total tokens
- Estimated cost
- Estimated context window usage
- Request count
- Average latency
- Current requests per minute
- Prompt composition breakdown
- Request history data

## How It Works

Kiro Live Inspector runs `mitmproxy` programmatically and installs a capture addon.

```text
Kiro CLI -> Kiro Live Inspector MITM proxy -> LLM Provider
                         |
                         v
                 Rich terminal dashboard
```

The proxy inspects JSON request and response bodies after MITM TLS termination. Provider-supplied usage fields are preferred. If provider usage is missing, the tool uses deterministic local token estimation and marks the values as estimated internally.

## Project Structure

```text
kiro-live-inspector/
    README.md
    pyproject.toml
    kiro_live_inspector/
        cli.py
        proxy.py
        capture.py
        parser.py
        tokenizer.py
        dashboard.py
        session.py
        metrics.py
        models.py
        utils.py
```

## Install

```powershell
cd C:\Aathi\ContextLens\kiro-live-inspector
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

macOS or Linux:

```bash
cd kiro-live-inspector
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Run

```bash
kiro-live-inspector run --host 127.0.0.1 --port 8080
```

Set proxy variables in the same shell that launches Kiro:

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

Some tools also read lowercase variables:

```bash
export http_proxy=http://127.0.0.1:8080
export https_proxy=http://127.0.0.1:8080
```

## mitmproxy Certificate Setup

Because this tool uses HTTPS MITM, the client must trust the mitmproxy certificate authority.

1. Run the inspector once.
2. Open the mitmproxy certificate directory:

   - Windows: `%USERPROFILE%\.mitmproxy`
   - macOS/Linux: `~/.mitmproxy`

3. Install and trust `mitmproxy-ca-cert.cer` for your operating system.
4. Restart Kiro from a shell with the proxy variables set.

If Kiro uses its own certificate store, additional client-specific trust configuration may be required.

## Test With curl

Start the inspector:

```bash
kiro-live-inspector run --port 8080
```

In another terminal:

```bash
curl -x http://127.0.0.1:8080 https://api.anthropic.com/
```

For a JSON-like request:

```bash
curl -x http://127.0.0.1:8080 https://api.anthropic.com/v1/messages \
  -H "content-type: application/json" \
  -d "{\"model\":\"claude-3-5-sonnet\",\"messages\":[{\"role\":\"user\",\"content\":\"hello\"}]}"
```

The provider may reject the request because no valid authentication is supplied. The important validation is whether the inspector sees the flow and updates the dashboard.

## Test With Kiro CLI

1. Start Kiro Live Inspector.
2. Configure `HTTP_PROXY` and `HTTPS_PROXY`.
3. Ensure Kiro trusts the mitmproxy CA.
4. Run a normal Kiro workflow.
5. Watch the terminal dashboard update.

Success means the dashboard updates with provider, model, prompt tokens, completion tokens, cost, context usage, latency, and prompt breakdown.

## Prompt Classification Heuristics

Classification is deterministic and best-effort:

- `system` fields and system-role messages become `System Prompt`.
- User-role messages become `User Prompt`.
- Assistant-role messages become `Assistant History`.
- Tool definitions and function schemas become `Tool Calls`.
- Tool-result content becomes `Tool Results`.
- Text containing file/path markers is classified as `Files`.
- Text containing resource markers is classified as `Resources`.
- Text containing steering markers is classified as `Steering`.
- Text containing skill markers is classified as `Skills`.
- Anything not recognized becomes `Conversation` or `Unknown`.

These heuristics are intentionally transparent. They are not semantic analysis and do not make model calls.

## Provider Usage

Provider-supplied usage fields are preferred:

- Anthropic: `usage.input_tokens`, `usage.output_tokens`
- OpenAI: `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`
- Bedrock: common `usage` and invocation metric fields

When usage is missing, local token estimation is used.

## Known Limitations

- Requires mitmproxy CA trust.
- Some clients may ignore `HTTP_PROXY` and `HTTPS_PROXY`.
- Some clients may use certificate pinning or custom trust stores.
- Streaming usage may only appear once the response completes.
- Token counting fallback is approximate.
- Pricing metadata is intentionally small and may become stale.
- No database or persistent history is implemented.
- The dashboard is terminal-only.

## Success Criteria

The experiment succeeds if, while Kiro CLI is running, the terminal dashboard continuously updates with:

- Prompt tokens
- Completion tokens
- Session total
- Cost
- Context window usage
- Prompt composition
- Request history
- Latency

If this works, the result is strong evidence that a larger local observability platform can build on a MITM proxy architecture.

