#!/usr/bin/env python3
"""Register a Chutes OAuth app and store client_id/client_secret in the keychain. [BETA]

Usage:
  python register_oauth_app.py \
    --name "My App" \
    --homepage-url https://myapp.example.com \
    --redirect-uri http://localhost:3000/api/auth/chutes/callback \
    --redirect-uri https://myapp.example.com/api/auth/chutes/callback \
    --scope openid --scope profile --scope chutes:invoke \
    --profile oauth.my-app

The client_secret is NEVER written to stdout, logs, or error messages.
It is stored directly in the OS keychain via manage_credentials.py.

Exit codes:
  0 success (app created, credentials stored)
  1 bad input / missing management API key / profile already exists
  2 Chutes API error
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import api_key, idp_request, put_secret, redact


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", required=True, help="Human-readable app name")
    p.add_argument("--description", default="", help="Short description shown on consent screen")
    p.add_argument("--homepage-url", required=True, help="Public URL for the app")
    p.add_argument(
        "--redirect-uri",
        action="append",
        required=True,
        help="Allowed redirect URI (repeat for multiple)",
    )
    p.add_argument(
        "--scope",
        action="append",
        default=[],
        help="OAuth scope (repeat; default: openid profile chutes:invoke)",
    )
    p.add_argument(
        "--profile",
        required=True,
        help="Keychain profile name under which to store client_id/client_secret",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the request body and exit without calling Chutes",
    )
    args = p.parse_args()

    scopes = args.scope or ["openid", "profile", "chutes:invoke"]

    body = {
        "name": args.name,
        "description": args.description,
        "homepage_url": args.homepage_url,
        "redirect_uris": args.redirect_uri,
        "scopes": scopes,
    }

    if args.dry_run:
        print(json.dumps({"POST /idp/apps": body}, indent=2))
        return 0

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        print(
            "hint: register a Chutes account and API key first via the chutes-ai hub skill,",
            file=sys.stderr,
        )
        print("       then save credentials with manage_credentials.py set-profile.", file=sys.stderr)
        return 1

    try:
        resp = idp_request("POST", "/idp/apps", bearer=bearer, body=body)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    client_id = resp.get("client_id") or resp.get("clientId")
    client_secret = resp.get("client_secret") or resp.get("clientSecret")
    app_id = resp.get("app_id") or resp.get("id")

    if not client_id or not client_secret:
        print(
            "error: Chutes response missing client_id/client_secret. "
            "Check /idp/apps schema at https://api.chutes.ai/openapi.json",
            file=sys.stderr,
        )
        return 2

    try:
        put_secret("client_id", client_id, profile=args.profile)
        put_secret("client_secret", client_secret, profile=args.profile)
    except RuntimeError as e:
        print(f"error storing secrets: {e}", file=sys.stderr)
        print(
            f"CRITICAL: the app was created on Chutes but its secret is not saved. "
            f"Rotate it immediately via POST /idp/apps/{app_id}/regenerate-secret",
            file=sys.stderr,
        )
        return 2

    # Only safe, non-secret output on stdout.
    print(
        json.dumps(
            {
                "status": "ok",
                "app_id": app_id,
                "client_id": client_id,  # cid_ values are NOT secret (OAuth treats them as public)
                "client_secret_preview": redact(client_secret),
                "profile": args.profile,
                "scopes": scopes,
                "redirect_uris": args.redirect_uri,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
