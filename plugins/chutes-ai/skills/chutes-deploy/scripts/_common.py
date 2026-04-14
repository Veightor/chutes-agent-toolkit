"""Shared helpers for chutes-deploy scripts. [BETA]

Re-exports the helpers from chutes-sign-in's _common.py so there is one
implementation of the "call Chutes management API without leaking cpk_"
pattern. If this file drifts from chutes-sign-in/_common.py, fix it there
first and let the re-export inherit.
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
        "chutes-deploy depends on chutes-sign-in's _common.py."
    )

_spec = importlib.util.spec_from_file_location("chutes_signin_common", _SOURCE)
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("chutes_signin_common", _mod)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

# Re-export
api_key = _mod.api_key
get_secret = _mod.get_secret
put_secret = _mod.put_secret
idp_request = _mod.idp_request
redact = _mod.redact
CHUTES_API_BASE = _mod.CHUTES_API_BASE
