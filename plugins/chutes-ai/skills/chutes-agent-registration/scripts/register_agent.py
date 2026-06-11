#!/usr/bin/env python3
"""Register a Chutes.ai agent account via a Bittensor hotkey signature. [BETA dry-run only]

Usage:
  python register_agent.py \
    --hotkey <ss58_hotkey> \
    --coldkey <ss58_coldkey> \
    --signature <sig_or_path> \
    --profile agent.myagent \
    --dry-run

  # Live (destructive):
  python register_agent.py \
    --hotkey ... --coldkey ... --signature ... --profile agent.myagent \
    --yes --i-know-bittensor

Dry-run is the DEFAULT. Both --yes AND --i-know-bittensor are required
for a live POST; the second flag is a tripwire acknowledging onchain
implications.

What a live run does:
  1. POST /users/agent_registration with {hotkey, coldkey, signature}.
  2. Poll GET /users/agent_registration/{hotkey} every 5s until the status
     is "completed" (live-observed terminal value, 2026-06-11) or a
     user_id appears.
  3. POST /users/{user_id}/agent_setup to finalize.
  4. Write returned api_key / fingerprint to the keychain under --profile.
  5. Print redacted previews — NEVER raw secret values.

Exit codes:
  0 ok
  1 bad input / missing credentials / missing tripwire on live run
  2 Chutes API error / signature rejected
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from _common import api_key, idp_request, put_secret, redact


def load_signature(value: str) -> str:
    """Allow --signature to be either the literal signature or @path/to/file."""
    if value.startswith("@"):
        return Path(value[1:]).read_text().strip()
    return value


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--hotkey", required=True, help="SS58 hotkey address")
    p.add_argument("--coldkey", required=True, help="SS58 coldkey address (onchain owner)")
    p.add_argument(
        "--signature",
        required=True,
        help="Signature value, or @path/to/signature-file",
    )
    p.add_argument("--profile", required=True, help="Keychain profile name for returned credentials")
    p.add_argument("--dry-run", action="store_true", help="Print the POST body and exit (default if --yes is not passed)")
    p.add_argument("--yes", action="store_true", help="Required for a live POST")
    p.add_argument(
        "--i-know-bittensor",
        action="store_true",
        help="Tripwire: acknowledge that registration creates real onchain state",
    )
    p.add_argument("--poll-interval", type=int, default=5)
    p.add_argument("--poll-timeout", type=int, default=300)
    args = p.parse_args()

    signature = load_signature(args.signature)

    body = {
        "hotkey": args.hotkey,
        "coldkey": args.coldkey,
        "signature": signature,
    }

    # The signature is sensitive; redact in any printout.
    display_body = {**body, "signature": f"{signature[:8]}... ({len(signature)} chars)"}

    if args.dry_run or not args.yes:
        if not args.dry_run and not args.yes:
            print("(no --yes and no --dry-run; treating as --dry-run by default)")
        print(json.dumps({"POST /users/agent_registration": display_body}, indent=2))
        print()
        print("dry-run: no network call made. To go live, add --yes --i-know-bittensor.")
        return 0

    if not args.i_know_bittensor:
        print(
            "error: live registration requires --i-know-bittensor as well as --yes.\n"
            "       This is a deliberate tripwire. Agent registration creates real\n"
            "       onchain state tied to your hotkey/coldkey and is not cheaply\n"
            "       reversible.",
            file=sys.stderr,
        )
        return 1

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"POST /users/agent_registration (hotkey={args.hotkey[:12]}...)")
    try:
        resp = idp_request("POST", "/users/agent_registration", bearer=bearer, body=body)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"  initial response: {json.dumps({k: v for k, v in resp.items() if 'secret' not in k.lower() and 'key' not in k.lower()}, indent=2)}")

    # Poll status
    start = time.time()
    while time.time() - start < args.poll_timeout:
        time.sleep(args.poll_interval)
        try:
            status = idp_request("GET", f"/users/agent_registration/{args.hotkey}", bearer=bearer)
        except RuntimeError as e:
            print(f"  poll error: {e}", file=sys.stderr)
            continue
        state = status.get("status")
        print(f"  poll: {state}")
        # "completed" is the live-observed terminal status (2026-06-11);
        # "ready" kept for backward compatibility with older API releases.
        if state in ("completed", "ready") or status.get("user_id"):
            break
        if state == "error":
            print(f"  registration failed: {status.get('detail', '')}", file=sys.stderr)
            return 2
    else:
        print(f"  poll timed out after {args.poll_timeout}s", file=sys.stderr)
        return 2

    user_id = status.get("user_id")
    if not user_id:
        print(f"error: no user_id in status response: {status}", file=sys.stderr)
        return 2

    # Finalize
    print(f"POST /users/{user_id}/agent_setup")
    try:
        setup = idp_request("POST", f"/users/{user_id}/agent_setup", bearer=bearer, body={})
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    returned_api_key = setup.get("api_key") or setup.get("secret_key")
    returned_fingerprint = setup.get("fingerprint")
    payment_address = setup.get("payment_address")

    if returned_api_key:
        try:
            put_secret("api_key", returned_api_key, profile=args.profile)
            print(f"  stored api_key in keychain profile {args.profile!r}: {redact(returned_api_key)}")
        except RuntimeError as e:
            print(f"  CRITICAL: keychain write failed for api_key: {e}", file=sys.stderr)
            return 2
    if returned_fingerprint:
        try:
            put_secret("fingerprint", returned_fingerprint, profile=args.profile)
            print(f"  stored fingerprint in keychain: {redact(returned_fingerprint)}")
        except RuntimeError as e:
            print(f"  CRITICAL: keychain write failed for fingerprint: {e}", file=sys.stderr)
            return 2

    print()
    print("Agent account ready.")
    print(f"  user_id: {user_id}")
    if payment_address:
        print(f"  payment_address: {payment_address}")
    print(f"  profile: {args.profile}")
    print(f"  use it with: CHUTES_PROFILE={args.profile} python manage_credentials.py get --field api_key")
    return 0


if __name__ == "__main__":
    sys.exit(main())
