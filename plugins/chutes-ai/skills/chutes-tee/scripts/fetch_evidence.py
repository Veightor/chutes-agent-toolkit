#!/usr/bin/env python3
"""Fetch TEE attestation evidence for a Chutes chute.

Usage:
  python fetch_evidence.py --chute-id <chute_id> [--out PATH] [--json]

Flow:
  1. GET /instances/nonce      -> a 64-hex nonce (or secrets.token_hex(32) locally)
  2. GET /chutes/{id}/evidence?nonce=<nonce>

The nonce MUST be exactly 64 hex characters (32 bytes); anything else
returns HTTP 400. This script auto-generates a fresh nonce.

Exit codes:
  0 ok
  1 bad input / missing credentials
  2 Chutes API error
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
from pathlib import Path

from _common import api_key, idp_request


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chute-id", required=True)
    p.add_argument("--out", help="write the envelope JSON to this file (default: stdout)")
    p.add_argument("--json", action="store_true", help="force JSON to stdout (otherwise the summary is printed)")
    p.add_argument("--server-nonce", action="store_true", help="fetch /instances/nonce instead of generating locally")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.server_nonce:
        try:
            nonce = idp_request("GET", "/instances/nonce", bearer=bearer)
            if isinstance(nonce, str):
                nonce = nonce.strip('"')
        except RuntimeError as e:
            print(f"error fetching nonce: {e}", file=sys.stderr)
            return 2
    else:
        nonce = secrets.token_hex(32)

    if not (isinstance(nonce, str) and len(nonce) == 64):
        print(f"error: bad nonce shape ({len(nonce) if isinstance(nonce, str) else type(nonce).__name__})", file=sys.stderr)
        return 2

    try:
        envelope = idp_request(
            "GET",
            f"/chutes/{args.chute_id}/evidence?nonce={nonce}",
            bearer=bearer,
            timeout=120,  # evidence envelopes are large (hundreds of KB)
        )
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    text = json.dumps(envelope, indent=2)

    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {len(text)} bytes to {args.out}")
    elif args.json:
        print(text)
    else:
        # Brief summary
        ev = envelope.get("evidence", []) if isinstance(envelope, dict) else []
        failed = envelope.get("failed_instance_ids", []) if isinstance(envelope, dict) else []
        print(f"=== evidence summary for chute {args.chute_id} ===")
        print(f"  nonce:           {nonce[:16]}... ({len(nonce)} chars)")
        print(f"  instances:       {len(ev)}")
        print(f"  failed:          {len(failed)}")
        if ev:
            first = ev[0]
            print(f"  first instance:  {first.get('instance_id', '?')}")
            print(f"    quote bytes:     {len(first.get('quote', ''))} b64 chars")
            print(f"    gpu_evidence:    {len(first.get('gpu_evidence', []))} records")
            print(f"    certificate:     {len(first.get('certificate', ''))} b64 chars")
        if failed:
            print(f"  failed ids: {failed}")
        print(f"\nUse --out to save the full envelope.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
