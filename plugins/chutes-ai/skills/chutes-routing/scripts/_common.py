"""Shared helpers for chutes-routing scripts.

Re-exports from chutes-sign-in's _common.py plus routing-specific helpers
(list_models, resolve_chute_id).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve().parent
_SOURCE = _HERE.parent.parent / "chutes-sign-in" / "scripts" / "_common.py"

if not _SOURCE.exists():
    raise RuntimeError(
        f"Cannot locate shared helper at {_SOURCE}. "
        "chutes-routing depends on chutes-sign-in's _common.py."
    )

_spec = importlib.util.spec_from_file_location("chutes_signin_common", _SOURCE)
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("chutes_signin_common", _mod)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

api_key = _mod.api_key
get_secret = _mod.get_secret
idp_request = _mod.idp_request
CHUTES_API_BASE = _mod.CHUTES_API_BASE

# --- routing-specific helpers -----------------------------------------------

import json
import urllib.error
import urllib.request

CHUTES_INFER_BASE = "https://llm.chutes.ai/v1"


def list_models(bearer: str) -> list[dict]:
    """GET /v1/models. Source of truth for every filter/rank decision."""
    req = urllib.request.Request(
        f"{CHUTES_INFER_BASE}/models",
        headers={"Authorization": f"Bearer {bearer}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GET /v1/models failed: HTTP {e.code}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"GET /v1/models network error: {e.reason}") from None
    return data.get("data", [])


def effective_prompt_cost(model: dict) -> float:
    """Return per-1M-token prompt cost for cost-ranking.

    Uses base pricing; discount/override math is the caller's responsibility
    when --apply-overrides is passed.
    """
    pricing = model.get("pricing") or {}
    return float(pricing.get("prompt") or 0.0)


def effective_completion_cost(model: dict) -> float:
    pricing = model.get("pricing") or {}
    return float(pricing.get("completion") or 0.0)


def total_per_1m(model: dict) -> float:
    return effective_prompt_cost(model) + effective_completion_cost(model)
