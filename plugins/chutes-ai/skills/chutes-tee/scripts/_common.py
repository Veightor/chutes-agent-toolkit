"""Shared helpers for chutes-tee scripts."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SOURCE = _HERE.parent.parent / "chutes-sign-in" / "scripts" / "_common.py"

_spec = importlib.util.spec_from_file_location("chutes_signin_common", _SOURCE)
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("chutes_signin_common", _mod)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)

api_key = _mod.api_key
idp_request = _mod.idp_request
CHUTES_API_BASE = _mod.CHUTES_API_BASE
