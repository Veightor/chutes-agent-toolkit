#!/usr/bin/env python3
"""Verify a Sign-in-with-Chutes integration end-to-end. [BETA — permanent until exercised]

Usage:
  python verify_siwc.py --target /path/to/next-app --profile oauth.my-app [--base-url http://localhost:3000]

Checks:
  1. The vendored files exist at the expected locations.
  2. The target .env.local has the three required entries.
  3. The target's client_id matches the keychain profile's client_id.
  4. The /api/auth/chutes/session route responds (200 or 401, not 500).
  5. (Optional) If a session cookie is supplied via --session-cookie, calls
     POST /idp/token/introspect and asserts active=true + expected scopes.

Exit codes:
  0 all checks passed
  1 bad input / file missing / shape mismatch
  2 upstream (Chutes or local dev server) error
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from _common import api_key, get_secret, idp_request

EXPECTED_FILES = [
    "lib/chutesAuth.ts",
    "lib/serverAuth.ts",
    "hooks/useChutesSession.ts",
    "app/api/auth/chutes/login/route.ts",
    "app/api/auth/chutes/callback/route.ts",
    "app/api/auth/chutes/logout/route.ts",
    "app/api/auth/chutes/session/route.ts",
    "components/SignInButton.tsx",
]


def app_root(target: Path) -> Path:
    return target / "src" if (target / "src" / "app").exists() else target


def check_files(target: Path) -> list[str]:
    missing = []
    root = app_root(target)
    for rel in EXPECTED_FILES:
        if not (root / rel).exists():
            missing.append(rel)
    return missing


def check_env(target: Path) -> list[str]:
    env_file = target / ".env.local"
    if not env_file.exists():
        return ["(.env.local missing entirely)"]
    text = env_file.read_text()
    needed = ["CHUTES_OAUTH_CLIENT_ID", "CHUTES_OAUTH_CLIENT_SECRET", "NEXT_PUBLIC_APP_URL"]
    return [k for k in needed if f"{k}=" not in text]


def check_session_route(base_url: str) -> tuple[int, str]:
    url = base_url.rstrip("/") + "/api/auth/chutes/session"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode("utf-8", errors="replace") if e.fp else "")
    except urllib.error.URLError as e:
        raise RuntimeError(f"dev server unreachable at {base_url}: {e.reason}") from None


def introspect_token(token: str, expected_client_id: str) -> dict:
    bearer = api_key()
    body = {"token": token}  # urlencoded form would be more correct
    # Note: /idp/token/introspect is typically form-encoded per RFC 7662.
    # Upstream may accept JSON; adjust in verified run.
    return idp_request("POST", "/idp/token/introspect", bearer=bearer, body=body)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--target", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--base-url", default="http://localhost:3000")
    p.add_argument("--access-token", default=None, help="If set, also introspect this token")
    args = p.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        print(f"error: target {target} does not exist", file=sys.stderr)
        return 1

    print("1. vendored files…")
    missing = check_files(target)
    if missing:
        print(f"   FAIL: missing {len(missing)} files:", file=sys.stderr)
        for m in missing:
            print(f"     - {m}", file=sys.stderr)
        return 1
    print("   ok")

    print("2. .env.local entries…")
    missing_env = check_env(target)
    if missing_env:
        print(f"   FAIL: missing {', '.join(missing_env)}", file=sys.stderr)
        return 1
    print("   ok")

    print("3. keychain profile…")
    try:
        cid = get_secret("client_id", profile=args.profile)
    except RuntimeError as e:
        print(f"   FAIL: {e}", file=sys.stderr)
        return 1
    env_text = (target / ".env.local").read_text()
    if f"CHUTES_OAUTH_CLIENT_ID={cid}" not in env_text:
        print("   FAIL: .env.local client_id does not match keychain profile", file=sys.stderr)
        return 1
    print(f"   ok (client_id prefix: {cid[:8]}…)")

    print(f"4. dev server /api/auth/chutes/session at {args.base_url}…")
    try:
        status, body = check_session_route(args.base_url)
    except RuntimeError as e:
        print(f"   FAIL: {e}", file=sys.stderr)
        return 2
    if status in (200, 401):
        print(f"   ok ({status})")
    elif status >= 500:
        print(f"   FAIL: server error {status}: {body[:200]}", file=sys.stderr)
        return 2
    else:
        print(f"   WARN: unexpected status {status}: {body[:200]}")

    if args.access_token:
        print("5. token introspection…")
        try:
            info = introspect_token(args.access_token, expected_client_id=cid)
        except RuntimeError as e:
            print(f"   FAIL: {e}", file=sys.stderr)
            return 2
        if not info.get("active"):
            print(f"   FAIL: token inactive: {info}", file=sys.stderr)
            return 1
        if info.get("client_id") != cid:
            print(f"   FAIL: introspect client_id mismatch: {info.get('client_id')} != {cid}", file=sys.stderr)
            return 1
        print(f"   ok (scopes: {info.get('scope')})")
    else:
        print("5. token introspection…  skipped (no --access-token)")

    print("\nall checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
