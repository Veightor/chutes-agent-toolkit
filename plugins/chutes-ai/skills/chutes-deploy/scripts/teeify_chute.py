#!/usr/bin/env python3
"""Teeify an existing Chutes.ai affine chute. [BETA]

Usage:
  python teeify_chute.py --chute-id <chute_id>

What it does:
  1. PUT /chutes/{chute_id}/teeify
  2. Prints the new TEE chute id and a reminder to verify attestation evidence manually.

See references/teeify.md for the semantics. Deep attestation verification is wave-2 work.
"""
from __future__ import annotations

import argparse
import sys

from _common import api_key, idp_request


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chute-id", required=True, help="chute_id of the existing affine chute")
    args = p.parse_args()

    print("!! BETA — teeify creates a new TEE variant on specialized hardware.")
    print(f"   source chute_id: {args.chute_id}")
    print("   note: TEE guarantees are not automatically verified by this skill.")
    print("         Use GET /chutes/{chute_id}/evidence to fetch attestation evidence manually.")
    try:
        confirm = input("Proceed? [y/N]: ").strip().lower()
    except EOFError:
        confirm = ""
    if confirm not in ("y", "yes"):
        print("aborted.")
        return 1

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"PUT /chutes/{args.chute_id}/teeify …")
    try:
        resp = idp_request("PUT", f"/chutes/{args.chute_id}/teeify", bearer=bearer, body={})
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    new_chute_id = resp.get("chute_id") or resp.get("id")
    new_model_id = resp.get("model_id") or resp.get("name")
    print(f"\nTEE variant created.")
    if new_chute_id:
        print(f"  new chute_id: {new_chute_id}")
    if new_model_id:
        print(f"  new model_id: {new_model_id}")
    print()
    print("Next step (manual): fetch attestation evidence and verify it.")
    print(f"  GET /chutes/{new_chute_id or args.chute_id}/evidence")
    print("Deep verification lands in the future chutes-tee skill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
