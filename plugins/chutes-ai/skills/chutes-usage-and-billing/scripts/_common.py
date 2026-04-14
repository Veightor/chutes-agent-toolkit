"""Shared helpers for chutes-usage-and-billing scripts.

Imports from chutes-sign-in's _common.py.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SOURCE = _HERE.parent.parent / "chutes-sign-in" / "scripts" / "_common.py"

if not _SOURCE.exists():
    raise RuntimeError(
        f"Cannot locate shared helper at {_SOURCE}. "
        "chutes-usage-and-billing depends on chutes-sign-in's _common.py."
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


def pct_bar(usage: float, cap: float, width: int = 20) -> str:
    """ASCII progress bar like [##########..........] 50.0%"""
    if cap <= 0:
        return "[" + "." * width + "]   n/a"
    pct = min(usage / cap, 1.0)
    filled = int(pct * width)
    bar = "#" * filled + "." * (width - filled)
    return f"[{bar}] {pct * 100:5.1f}%"


def fmt_usd(v: float) -> str:
    return f"${v:>8.4f}"
