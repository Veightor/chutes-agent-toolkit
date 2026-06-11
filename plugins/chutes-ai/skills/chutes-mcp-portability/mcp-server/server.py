#!/usr/bin/env python3
"""Chutes.ai MCP server — stdio transport. [BETA]

Exposes Chutes management + inference endpoints as MCP tools so any
MCP-aware client (Claude Desktop, Cursor, Cline, Claude Code) can use
Chutes without hand-rolling integrations.

Auth:
  Inference (`llm.chutes.ai/v1`):
    CHUTES_API_KEY env var — primary
    falls back to `manage_credentials.py get --field api_key` subprocess

  Management (`api.chutes.ai`):
    CHUTES_FINGERPRINT env var — primary
    falls back to `manage_credentials.py get --field fingerprint`
    then exchanges the fingerprint for a short-lived JWT via `POST /users/login`

Write/deploy tools are marked [BETA] in their description and stay that
way until an explicit verification pass exercises each one.

Run:
  chutes-mcp-server                 # stdio mode (for MCP clients)
  chutes-mcp-server --self-check    # run a read-only health check and exit
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    print(
        "error: `mcp` package not installed. Run `uv tool install chutes-mcp-server` "
        "or `pip install mcp`.",
        file=sys.stderr,
    )
    sys.exit(2)

CHUTES_API_BASE = os.environ.get("CHUTES_API_BASE", "https://api.chutes.ai")
CHUTES_INFER_BASE = os.environ.get("CHUTES_INFER_BASE", "https://llm.chutes.ai/v1")
BETA_PREFIX = "[BETA] "


def _find_manage_credentials() -> Optional[Path]:
    """Locate manage_credentials.py by walking up from this file."""
    here = Path(__file__).resolve().parent
    candidate = here.parent.parent / "chutes-ai" / "scripts" / "manage_credentials.py"
    if candidate.exists():
        return candidate
    for parent in here.parents:
        found = list(parent.glob("**/manage_credentials.py"))
        if found:
            return found[0]
    return None


def _get_secret(field: str, env_var: str) -> str:
    """Read a Chutes secret from env or the credential store. Never logged."""
    env_val = os.environ.get(env_var)
    if env_val:
        return env_val
    script = _find_manage_credentials()
    if not script:
        raise RuntimeError(
            f"{env_var} not set and manage_credentials.py not found on PATH"
        )
    result = subprocess.run(
        [sys.executable, str(script), "get", "--field", field],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"failed to read Chutes {field} from credential store")
    return result.stdout.strip()


def _get_api_key() -> str:
    return _get_secret("api_key", "CHUTES_API_KEY")


def _get_fingerprint() -> str:
    return _get_secret("fingerprint", "CHUTES_FINGERPRINT")


def _has_fingerprint() -> bool:
    try:
        _get_fingerprint()
        return True
    except Exception:
        return False


def _get_management_jwt() -> str:
    fingerprint = _get_fingerprint()
    data = json.dumps({"fingerprint": fingerprint}).encode("utf-8")
    req = urllib.request.Request(
        CHUTES_API_BASE.rstrip("/") + "/users/login",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            obj = json.loads(raw) if raw else {}
            token = obj.get("token") or obj.get("access_token") or obj.get("jwt")
            if not token:
                raise RuntimeError("management login succeeded but no JWT/token was returned")
            return token
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read().decode("utf-8")).get("detail", "")
        except Exception:
            pass
        raise RuntimeError(f"management login failed: HTTP {e.code}: {detail or e.reason}") from None


def _request(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    body: Any = None,
    timeout: int = 60,
) -> Any:
    data: Optional[bytes] = None
    headers = {**headers, "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read().decode("utf-8")).get("detail", "")
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code}: {detail or e.reason}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"network error: {e.reason}") from None


def _mgmt(method: str, path: str, *, body: Any = None) -> Any:
    jwt = _get_management_jwt()
    return _request(
        method,
        CHUTES_API_BASE.rstrip("/") + path,
        headers={"Authorization": f"Bearer {jwt}"},
        body=body,
    )


def _infer(method: str, path: str, *, body: Any = None) -> Any:
    return _request(
        method,
        CHUTES_INFER_BASE.rstrip("/") + path,
        headers={"X-API-Key": _get_api_key()},
        body=body,
    )


app = FastMCP("chutes-ai")


# ---- Read-only tools (graduate individually after verified calls) ----

@app.tool(description="List models available on Chutes.ai via the OpenAI-compatible /v1/models endpoint.")
def chutes_list_models(limit: int = 25) -> dict:
    data = _infer("GET", "/models")
    items = data.get("data", [])
    if limit:
        items = items[:limit]
    return {"count": len(items), "models": [{"id": m.get("id"), "confidential_compute": m.get("confidential_compute"), "pricing": m.get("pricing")} for m in items]}


@app.tool(description="List chutes owned by or shared with the current user.")
def chutes_list_chutes(page: int = 0, limit: int = 25) -> dict:
    return _mgmt("GET", f"/chutes/?page={page}&limit={limit}")


@app.tool(description="List stable model aliases configured for this account.")
def chutes_list_aliases() -> dict:
    return _mgmt("GET", "/model_aliases/")


@app.tool(description="Get aggregated invocation usage for the current user.")
def chutes_get_usage() -> dict:
    return _mgmt("GET", "/invocations/usage")


@app.tool(description="Get current user quotas.")
def chutes_get_quota() -> dict:
    return _mgmt("GET", "/users/me/quotas")


@app.tool(description="Get current user active discounts.")
def chutes_get_discounts() -> dict:
    return _mgmt("GET", "/users/me/discounts")


@app.tool(description="Fetch TEE attestation evidence for a specific chute.")
def chutes_get_evidence(chute_id: str) -> dict:
    return _mgmt("GET", f"/chutes/{chute_id}/evidence")


@app.tool(description="Introspect an OAuth access token issued by Chutes (RFC 7662).")
def chutes_oauth_introspect(token: str) -> dict:
    return _mgmt("POST", "/idp/token/introspect", body={"token": token})


@app.tool(description="List API keys on the current account (does not return secret values).")
def chutes_list_api_keys(page: int = 0, limit: int = 25) -> dict:
    return _mgmt("GET", f"/api_keys/?page={page}&limit={limit}")


@app.tool(description="Run a chat completion against Chutes.ai. Returns the assistant message only.")
def chutes_chat_complete(model: str, messages: list[dict], max_tokens: int = 512, temperature: float = 0.7) -> dict:
    body = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    resp = _infer("POST", "/chat/completions", body=body)
    choices = resp.get("choices", [])
    if not choices:
        return {"content": "", "raw": resp}
    return {"content": choices[0]["message"]["content"], "finish_reason": choices[0].get("finish_reason")}


# ---- Write / deploy tools (BETA permanent under deploy-features policy) ----

@app.tool(description=BETA_PREFIX + "Deploy a vLLM chute. WRITES: POST /chutes/vllm. Consumes paid compute.")
def chutes_deploy_vllm(model: str, gpu: str = "h100", gpu_count: int = 1, name: Optional[str] = None, public: bool = False) -> dict:
    body = {
        "name": name or f"mcp/{model.split('/')[-1].lower()}",
        "model": model,
        "node_selector": {"gpu_count": gpu_count, "gpu_type": gpu},
        "public": public,
    }
    return _mgmt("POST", "/chutes/vllm", body=body)


@app.tool(description=BETA_PREFIX + "Deploy a diffusion chute. WRITES: POST /chutes/diffusion. Consumes paid compute.")
def chutes_deploy_diffusion(model: str, gpu: str = "a100_40gb", gpu_count: int = 1, name: Optional[str] = None, public: bool = False) -> dict:
    body = {
        "name": name or f"mcp/{model.split('/')[-1].lower()}",
        "model": model,
        "node_selector": {"gpu_count": gpu_count, "gpu_type": gpu},
        "public": public,
    }
    return _mgmt("POST", "/chutes/diffusion", body=body)


@app.tool(description=BETA_PREFIX + "Create a TEE variant of an existing affine chute. WRITES: PUT /chutes/{id}/teeify.")
def chutes_teeify(chute_id: str) -> dict:
    return _mgmt("PUT", f"/chutes/{chute_id}/teeify", body={})


@app.tool(description=BETA_PREFIX + "Create a stable model alias pointing at one or more chute UUIDs. WRITES: POST /model_aliases/.")
def chutes_set_alias(alias: str, chute_ids: list[str]) -> dict:
    """Create an alias. `chute_ids` is a list of chute UUIDs (not model names)."""
    return _mgmt("POST", "/model_aliases/", body={"alias": alias, "chute_ids": chute_ids})


@app.tool(description=BETA_PREFIX + "Delete a model alias. WRITES: DELETE /model_aliases/{alias}.")
def chutes_delete_alias(alias: str) -> dict:
    return _mgmt("DELETE", f"/model_aliases/{alias}")


@app.tool(description=BETA_PREFIX + "Create a new API key on the current account. WRITES: POST /api_keys/. The secret_key is returned ONCE.")
def chutes_create_api_key(name: str, admin: bool = False) -> dict:
    return _mgmt("POST", "/api_keys/", body={"name": name, "admin": admin})


# ---- Entry point ----

def main() -> int:
    parser = argparse.ArgumentParser(description="Chutes.ai MCP server")
    parser.add_argument("--self-check", action="store_true", help="Run a read-only health check and exit")
    args = parser.parse_args()

    if args.self_check:
        try:
            model_result = chutes_list_models(limit=1)  # type: ignore[call-arg]
            mgmt_total = None
            if _has_fingerprint():
                mgmt_result = chutes_list_api_keys(page=0, limit=1)  # type: ignore[call-arg]
                mgmt_total = mgmt_result.get('total')
        except RuntimeError as e:
            print(f"self-check FAILED: {e}", file=sys.stderr)
            return 2
        if mgmt_total is None:
            print(f"self-check OK: inference reachable ({model_result.get('count')} model(s)); management check skipped (no fingerprint configured)")
        else:
            print(
                "self-check OK: "
                f"inference reachable ({model_result.get('count')} model(s)); "
                f"management reachable ({mgmt_total} api key(s) visible)"
            )
        return 0

    app.run()  # stdio transport
    return 0


if __name__ == "__main__":
    sys.exit(main())
