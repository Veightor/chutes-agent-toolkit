#!/usr/bin/env python3
"""POST /idp/token/introspect wrapper. [BETA — needs a live OAuth access token]

Usage:
  python introspect_token.py --token <oauth_access_token>
  python introspect_token.py --token-file /path/to/token.txt

Wraps RFC 7662 introspection. Returns a JSON object like:
  {"active": true, "scope": "openid profile chutes:invoke",
   "client_id": "cid_...", "username": "...", "exp": ..., "sub": "..."}

Wave-2 note: this script has NOT been exercised against a live token
because the verification environment doesn't complete a SIWC browser
flow to produce one. Graduates out of BETA when a test run is recorded.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import api_key, idp_request


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--token", help="Token value (argv-visible; prefer --token-file)")
    group.add_argument("--token-file", help="Path to a file containing just the token")
    p.add_argument("--expected-scope", action="append", default=[], help="Fail if the scope is not present")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if args.token_file:
        token = Path(args.token_file).read_text().strip()
    else:
        token = args.token

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        resp = idp_request("POST", "/idp/token/introspect", bearer=bearer, body={"token": token})
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(resp, indent=2))
    else:
        active = resp.get("active")
        scope = resp.get("scope", "")
        client = resp.get("client_id", "")
        user = resp.get("username") or resp.get("sub", "")
        exp = resp.get("exp")
        print(f"active:    {active}")
        print(f"client_id: {client}")
        print(f"username:  {user}")
        print(f"scope:     {scope}")
        print(f"expires:   {exp}")

    if args.expected_scope:
        present = set(resp.get("scope", "").split())
        missing = [s for s in args.expected_scope if s not in present]
        if missing:
            print(f"\nFAIL: missing scopes: {missing}", file=sys.stderr)
            return 1

    if resp.get("active") is False:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
