#!/usr/bin/env python3
"""POST /idp/token/revoke wrapper. [BETA — needs a live OAuth token]

Usage:
  python revoke_token.py --token <token> --yes
  python revoke_token.py --token-file /path/to/token.txt --yes

Destructive — every session using this token stops working.

Wave-2 note: not exercised live; graduates when a test run is recorded.

CONTENT-TYPE CAVEAT (openapi fetched 2026-06-11): the spec declares this
endpoint's body as application/x-www-form-urlencoded (token required,
token_type_hint optional) — this script currently POSTs JSON via
idp_request(). Unverified whether the server also accepts JSON as of
2026-06-11; expect to switch to form encoding before BETA graduation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import api_key, idp_request


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--token")
    group.add_argument("--token-file")
    p.add_argument("--yes", action="store_true", help="Required to actually revoke")
    args = p.parse_args()

    if not args.yes:
        print("error: --yes required to revoke a token (this breaks every session using it)", file=sys.stderr)
        return 1

    token = Path(args.token_file).read_text().strip() if args.token_file else args.token

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        resp = idp_request("POST", "/idp/token/revoke", bearer=bearer, body={"token": token})
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"revoked: {resp.get('revoked', resp)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
