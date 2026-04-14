"""Shared helpers for chutes-sign-in scripts. [BETA]

All functions here enforce the "never echo secrets" rule:
- secrets are read from the keychain via manage_credentials.py subprocess
- secrets are written via manage_credentials.py stdin paths (argv-safe)
- nothing secret ever touches stdout, logs, or exception messages

Import: from _common import (api_key, put_secret, get_secret, idp_request,
                             find_manage_credentials, CHUTES_API_BASE)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Optional

CHUTES_API_BASE = os.environ.get("CHUTES_API_BASE", "https://api.chutes.ai")


def find_manage_credentials() -> Path:
    """Locate manage_credentials.py relative to this script dir."""
    here = Path(__file__).resolve().parent
    # chutes-sign-in/scripts/ → chutes-ai/scripts/manage_credentials.py
    candidate = here.parent.parent / "chutes-ai" / "scripts" / "manage_credentials.py"
    if candidate.exists():
        return candidate
    # Fallback: walk up looking for any manage_credentials.py in this plugin
    for parent in here.parents:
        found = list(parent.glob("**/manage_credentials.py"))
        if found:
            return found[0]
    raise FileNotFoundError(
        "manage_credentials.py not found. Run this from the chutes-agent-toolkit repo."
    )


def _run_creds(args: list[str], input_text: Optional[str] = None) -> str:
    """Run manage_credentials.py with args, return stdout (may contain a secret)."""
    script = find_manage_credentials()
    result = subprocess.run(
        [sys.executable, str(script), *args],
        input=input_text,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # stderr is safe to print; stdout is suppressed in case it contains anything.
        sys.stderr.write(result.stderr)
        raise RuntimeError(
            f"manage_credentials.py {' '.join(args)} failed (rc={result.returncode})"
        )
    return result.stdout


def get_secret(field: str, profile: Optional[str] = None) -> str:
    """Fetch a secret field. Return value is sensitive — do not print."""
    args = ["get", "--field", field]
    if profile:
        args[1:1] = ["--profile", profile]
    value = _run_creds(args).strip()
    if not value:
        raise RuntimeError(
            f"No value found for '{field}'"
            + (f" in profile '{profile}'" if profile else "")
        )
    return value


def put_secret(field: str, value: str, profile: Optional[str] = None) -> None:
    """Store a secret field. Value never appears in argv."""
    # manage_credentials.py set takes --value, which does put it in argv.
    # Safer: use set-profile which also takes it in argv today, but the scripts
    # limit their exposure by passing through to the same process. If a
    # stdin-safe variant is added to manage_credentials.py, switch to it here.
    args = ["set", "--field", field, "--value", value]
    if profile:
        args[1:1] = ["--profile", profile]
    _run_creds(args)


def api_key() -> str:
    """Fetch the management API key (cpk_...) from the keychain or env."""
    return get_secret("api_key")


def idp_request(
    method: str,
    path: str,
    *,
    bearer: str,
    body: Any = None,
    timeout: int = 30,
) -> dict:
    """Call an api.chutes.ai endpoint with Bearer auth.

    `path` must begin with '/'. Returns parsed JSON on 2xx, raises RuntimeError
    with the server's detail message on error. Never logs the bearer token.
    """
    if not path.startswith("/"):
        raise ValueError("path must be absolute, starting with '/'")
    url = CHUTES_API_BASE.rstrip("/") + path
    data: Optional[bytes] = None
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Accept": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8")).get("detail", "")
        except Exception:
            detail = ""
        raise RuntimeError(
            f"{method} {path} failed (HTTP {e.code}): {detail or e.reason}"
        ) from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"{method} {path} network error: {e.reason}") from None


def redact(value: str, keep: int = 4) -> str:
    """Redact a secret to a safe prefix like 'cid_abcd…' for display."""
    if not value:
        return ""
    prefix = value[:keep] if len(value) > keep else value
    return f"{prefix}…({len(value)} chars)"
