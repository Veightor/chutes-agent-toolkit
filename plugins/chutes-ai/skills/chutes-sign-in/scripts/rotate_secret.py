#!/usr/bin/env python3
"""Rotate a Chutes OAuth app client secret safely. [BETA — permanent until exercised]

Usage:
  python rotate_secret.py --profile oauth.my-app

What it does:
  1. Reads client_id from the keychain profile.
  2. POSTs /idp/apps/{client_id}/regenerate-secret.
  3. Writes the new client_secret back into the same keychain profile.
  4. Prints a prominent reminder to redeploy any running service that had the old secret loaded.

The old client_secret value is NEVER printed. The new value is NEVER printed.
Only redacted previews appear on stdout.

Exit codes:
  0 success (rotated + stored + redeploy reminder printed)
  1 bad input / missing profile / missing management API key
  2 Chutes API error / keychain write error (see note about recovery below)
"""
from __future__ import annotations

import argparse
import sys

from _common import api_key, get_secret, idp_request, put_secret, redact


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--profile", required=True)
    p.add_argument(
        "--app-id",
        default=None,
        help="Override: use this app_id instead of the profile's client_id",
    )
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.app_id:
        app_id = args.app_id
    else:
        try:
            app_id = get_secret("client_id", profile=args.profile)
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            print(
                f"hint: re-run register_oauth_app.py --profile {args.profile} first.",
                file=sys.stderr,
            )
            return 1

    print(f"Rotating secret for app {app_id[:8]}… (profile {args.profile})")

    try:
        resp = idp_request(
            "POST",
            f"/idp/apps/{app_id}/regenerate-secret",
            bearer=bearer,
            body={},
        )
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    new_secret = resp.get("client_secret") or resp.get("clientSecret")
    if not new_secret:
        print(
            "error: Chutes response missing client_secret. The secret may or may not have rotated. "
            "Check /idp/apps/{app_id} and re-run if needed.",
            file=sys.stderr,
        )
        return 2

    try:
        put_secret("client_secret", new_secret, profile=args.profile)
    except RuntimeError as e:
        print(
            f"CRITICAL: secret rotated on Chutes but KEYCHAIN WRITE FAILED: {e}\n"
            f"         The old secret is now invalid and the new one is not saved.\n"
            f"         Re-run rotate_secret.py to rotate again once the keychain is fixed.",
            file=sys.stderr,
        )
        return 2

    print(f"ok: new secret preview {redact(new_secret)}")
    print()
    print("!! IMPORTANT — the old client_secret is now invalid.")
    print("!! Redeploy every running service that loaded the old secret:")
    print("!!   - Vercel:    vercel env rm CHUTES_OAUTH_CLIENT_SECRET && vercel env add … && vercel --prod")
    print("!!   - Docker:    rebuild / restart with the new env var")
    print("!!   - bare dev:  kill and restart the dev server so .env.local is reloaded")
    print()
    print("This script does NOT auto-redeploy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
