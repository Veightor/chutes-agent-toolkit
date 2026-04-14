#!/usr/bin/env python3
"""Check whether a Bittensor hotkey has a Chutes agent registration.

Usage:
  python agent_status.py --hotkey <ss58_hotkey>

Read-only. GET /users/agent_registration/{hotkey}. Returns:
  - status: registered (plus user_id and profile data) on 200
  - status: not_registered on 404
  - error + exit != 0 on any other code

Exit codes:
  0 registered
  1 not registered (404) / bad input / missing credentials
  2 Chutes API error
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import api_key, idp_request


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--hotkey", required=True, help="SS58 hotkey to look up")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        resp = idp_request("GET", f"/users/agent_registration/{args.hotkey}", bearer=bearer)
    except RuntimeError as e:
        msg = str(e)
        if "HTTP 404" in msg or "not found" in msg.lower():
            if args.json:
                print(json.dumps({"status": "not_registered", "hotkey": args.hotkey}))
            else:
                print(f"status:  not_registered")
                print(f"hotkey:  {args.hotkey}")
                print(f"  (the hotkey has no Chutes agent registration yet)")
            return 1
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"status": "registered", **(resp or {})}, indent=2))
    else:
        print(f"status:  registered")
        print(f"hotkey:  {args.hotkey}")
        for k in ("user_id", "username", "payment_address", "balance", "created_at"):
            if k in (resp or {}):
                print(f"{k:<16}: {resp[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
