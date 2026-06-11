#!/usr/bin/env python3
"""Check whether a Bittensor hotkey has a Chutes agent registration.

Usage:
  python agent_status.py --hotkey <ss58_hotkey>

Read-only. GET /users/agent_registration/{hotkey}. Returns:
  - status: registered (plus registration data) on 200
  - status: not_registered on 404
  - error + exit != 0 on any other code

200 response shape (live-verified 2026-06-11): {status ("completed"),
registration_id, user_id, hotkey, coldkey, payment_address,
received_amount, required_amount (TAO), message}. In --json mode the
API's own status value (e.g. "completed") overrides the script's
"registered" label.

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
        # Field list matches the live-verified 200 response shape (2026-06-11);
        # the API's own "status" field (e.g. "completed") is skipped here because
        # the script prints its registered/not_registered label above.
        for k in ("user_id", "coldkey", "payment_address", "received_amount", "required_amount", "message"):
            if k in (resp or {}):
                print(f"{k:<16}: {resp[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
