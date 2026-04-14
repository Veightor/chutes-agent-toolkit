#!/usr/bin/env python3
"""Deploy a custom (CDK) chute from a pre-built image. [BETA]

Usage:
  python deploy_custom.py \
    --image-id <from build_image.py> \
    --entrypoint my_module:chute \
    --gpu h100 \
    --name myuser/my-chute \
    [--public] \
    [--alias stable-name]

Follows the same shape as deploy_vllm.py — warmup polling and alias creation
come from the shared helpers.
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import api_key, idp_request
from deploy_vllm import poll_warmup, create_alias


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--image-id", required=True)
    p.add_argument("--entrypoint", required=True, help="module:attr exposing the Chute object")
    p.add_argument("--gpu", default="h100")
    p.add_argument("--gpu-count", type=int, default=1)
    p.add_argument("--name", required=True)
    p.add_argument("--tagline", default=None)
    p.add_argument("--readme", default=None)
    p.add_argument("--public", action="store_true")
    p.add_argument("--alias", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    body = {
        "name": args.name,
        "image_id": args.image_id,
        "entrypoint": args.entrypoint,
        "tagline": args.tagline or args.name,
        "readme": args.readme or "Deployed via chutes-deploy skill.",
        "node_selector": {"gpu_count": args.gpu_count, "gpu_type": args.gpu},
        "public": bool(args.public),
    }

    if args.dry_run:
        print(json.dumps({"POST /chutes/": body}, indent=2))
        return 0

    print("!! BETA — deploying a custom chute consumes real paid compute.")
    print(f"   name:       {args.name}")
    print(f"   image_id:   {args.image_id}")
    print(f"   entrypoint: {args.entrypoint}")
    print(f"   gpu:        {args.gpu_count}× {args.gpu}")
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

    print("POST /chutes/ …")
    try:
        resp = idp_request("POST", "/chutes/", bearer=bearer, body=body)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    chute_id = resp.get("chute_id") or resp.get("id")
    model_id = resp.get("model_id") or resp.get("name") or args.name
    if not chute_id:
        print(f"error: response missing chute_id: {resp}", file=sys.stderr)
        return 2

    print(f"  chute_id: {chute_id}")

    print("polling warmup…")
    try:
        warmup = poll_warmup(bearer, chute_id)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    endpoint = warmup.get("endpoint", "https://llm.chutes.ai/v1")
    print(f"\nREADY. base_url={endpoint} model={model_id}")

    if args.alias:
        create_alias(bearer, args.alias, model_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
