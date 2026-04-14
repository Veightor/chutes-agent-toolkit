"""Shared helpers for chutes-platform-ops scripts."""
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
get_secret = _mod.get_secret
put_secret = _mod.put_secret
idp_request = _mod.idp_request
redact = _mod.redact
CHUTES_API_BASE = _mod.CHUTES_API_BASE


def paginate(bearer: str, path: str, page_size: int = 100, max_pages: int = 50) -> list[dict]:
    """Generic pagination helper — returns the full `items` list."""
    items: list[dict] = []
    page = 0
    while True:
        sep = "&" if "?" in path else "?"
        d = idp_request("GET", f"{path}{sep}page={page}&limit={page_size}", bearer=bearer)
        batch = d.get("items") if isinstance(d, dict) else None
        if batch is None and isinstance(d, list):
            return d
        if not batch:
            break
        items.extend(batch)
        total = (d or {}).get("total") or 0
        if (page + 1) * page_size >= total:
            break
        page += 1
        if page >= max_pages:
            break
    return items


def my_user_id(bearer: str) -> str:
    me = idp_request("GET", "/users/me", bearer=bearer)
    uid = me.get("user_id")
    if not uid:
        raise RuntimeError("/users/me did not return user_id")
    return uid
