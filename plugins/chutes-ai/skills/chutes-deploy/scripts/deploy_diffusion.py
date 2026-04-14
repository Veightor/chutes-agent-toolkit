#!/usr/bin/env python3
"""Deploy a diffusion chute on Chutes.ai. [BETA]

Usage:
  python deploy_diffusion.py \
    --model stabilityai/sdxl-turbo \
    --gpu a100_40gb \
    [--name myuser/sdxl-turbo] \
    [--torch-dtype float16] \
    [--variant fp16] \
    [--public] \
    [--dry-run]

Mirror of deploy_vllm.py but targets POST /chutes/diffusion. See
references/diffusion-recipe.md for field notes.

Exit codes mirror deploy_vllm.py.
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import api_key, idp_request

# Reuse helpers by importing from deploy_vllm which also lives in this dir.
from deploy_vllm import stream_build_logs, poll_warmup, resolve_hf_revision  # noqa: E402


def build_body(args: argparse.Namespace) -> dict:
    name = args.name or f"<username>/{args.model.split('/')[-1].lower()}"
    pipeline_args: dict = {}
    if args.torch_dtype:
        pipeline_args["torch_dtype"] = args.torch_dtype
    if args.variant:
        pipeline_args["variant"] = args.variant
    if args.trust_remote_code:
        pipeline_args["trust_remote_code"] = True
    body = {
        "name": name,
        "model": args.model,
        "tagline": args.tagline or f"{args.model}",
        "readme": args.readme or "Deployed via chutes-deploy skill.",
        "node_selector": {
            "gpu_count": args.gpu_count,
            "gpu_type": args.gpu,
        },
        "pipeline_args": pipeline_args,
        "revision": args.revision,
        "public": bool(args.public),
    }
    return body


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True)
    p.add_argument("--gpu", default="a100_40gb")
    p.add_argument("--gpu-count", type=int, default=1)
    p.add_argument("--name", default=None)
    p.add_argument("--tagline", default=None)
    p.add_argument("--readme", default=None)
    p.add_argument("--torch-dtype", default="float16")
    p.add_argument("--variant", default=None)
    p.add_argument("--trust-remote-code", action="store_true")
    p.add_argument("--revision", default="main")
    p.add_argument("--public", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    try:
        resolved = resolve_hf_revision(args.model, args.revision)
    except RuntimeError as e:
        print(f"error resolving revision: {e}", file=sys.stderr)
        return 1
    if resolved != args.revision:
        print(f"  resolved revision {args.revision!r} -> {resolved}")
        args.revision = resolved

    body = build_body(args)

    if args.dry_run:
        print(json.dumps({"POST /chutes/diffusion": body}, indent=2))
        return 0

    print("!! BETA — deploying a diffusion chute consumes real paid compute.")
    print(f"   model: {args.model}")
    print(f"   gpu:   {args.gpu_count}× {args.gpu}")
    print(f"   name:  {body['name']}")
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

    print("POST /chutes/diffusion …")
    try:
        resp = idp_request("POST", "/chutes/diffusion", bearer=bearer, body=body)
    except RuntimeError as e:
        msg = str(e)
        print(f"error: {msg}", file=sys.stderr)
        if "Easy deployment is currently disabled" in msg:
            print(
                "\nhint: the platform-side easy-lane diffusion deployment is gated.\n"
                "      Use the custom CDK lane instead via build_image.py + deploy_custom.py.\n"
                "      See references/diffusion-recipe.md.",
                file=sys.stderr,
            )
        return 2

    chute_id = resp.get("chute_id") or resp.get("id")
    image_id = resp.get("image_id")
    model_id = resp.get("model_id") or resp.get("name") or body["name"]
    if not chute_id:
        print(f"error: response missing chute_id: {resp}", file=sys.stderr)
        return 2

    print(f"  chute_id: {chute_id}")
    print(f"  image_id: {image_id}")

    if image_id:
        print("streaming build logs…")
        if not stream_build_logs(bearer, image_id):
            return 2

    print("polling warmup…")
    try:
        warmup = poll_warmup(bearer, chute_id)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    endpoint = warmup.get("endpoint", "https://llm.chutes.ai/v1")
    print(f"\nREADY. Call with:")
    print(f"  base_url: {endpoint}")
    print(f"  model:    {model_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
