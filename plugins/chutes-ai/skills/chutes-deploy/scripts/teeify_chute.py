#!/usr/bin/env python3
"""Teeify an existing Chutes.ai affine chute. [BETA — DEFUNCT]

*** WARNING: PUT /chutes/{chute_id}/teeify was REMOVED from the Chutes API. ***
The path is absent from api.chutes.ai/openapi.json (verified 2026-06-11) and the
current chutes SDK has no teeify command. This script is kept for reference only
and WILL FAIL against the live API. TEE is now selected at deploy time via the
SDK templates' tee=True kwarg (build_vllm_chute / build_sglang_chute /
build_diffusion_chute). See references/teeify.md.

Usage (historical):
  python teeify_chute.py --chute-id <chute_id>

What it did:
  1. PUT /chutes/{chute_id}/teeify
  2. Prints the new TEE chute id and a reminder to verify attestation evidence manually.

For attestation verification use the sibling chutes-tee skill
(GET /chutes/{id}/evidence now requires ?nonce=<64 hex chars>).
"""
from __future__ import annotations

import argparse
import sys

from _common import api_key, idp_request


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chute-id", required=True, help="chute_id of the existing affine chute")
    args = p.parse_args()

    print("!! DEFUNCT — PUT /chutes/{id}/teeify was removed from the Chutes API")
    print("   (gone from openapi.json as of 2026-06-11). This call is expected to fail.")
    print("   Use tee=True at deploy time via the SDK templates instead.")
    print(f"   source chute_id: {args.chute_id}")
    print("   note: TEE guarantees are not automatically verified by this skill.")
    print("         Use GET /chutes/{chute_id}/evidence?nonce=<64-hex> (nonce required)")
    print("         and the chutes-tee skill to verify attestation evidence.")
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
    print(f"  GET /chutes/{new_chute_id or args.chute_id}/evidence?nonce=<64-hex-chars>")
    print("Deep verification: use the chutes-tee skill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
