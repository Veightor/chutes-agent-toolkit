#!/usr/bin/env python3
"""Deploy a vLLM chute on Chutes.ai. [BETA]

Usage:
  python deploy_vllm.py \
    --model Qwen/Qwen3-8B \
    --gpu h100 \
    [--name myuser/qwen3-8b] \
    [--max-model-len 32768] \
    [--trust-remote-code] \
    [--public] \
    [--alias interactive-fast] \
    [--dry-run]

The script:
  1. Reads cpk_ from manage_credentials.py.
  2. POSTs /chutes/vllm with a templated body (see references/vllm-recipe.md).
  3. Streams build logs from GET /images/{image_id}/logs until the build settles.
  4. Polls GET /chutes/warmup/{chute_id} until the chute is serving.
  5. Optionally creates a stable model alias via POST /model_aliases/.

Exit codes:
  0 deployed and serving
  1 bad input / quota or balance issue
  2 Chutes API error or build failure
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from _common import api_key, idp_request


def build_body(args: argparse.Namespace) -> dict:
    name = args.name or f"<username>/{args.model.split('/')[-1].lower()}"
    body = {
        "name": name,
        "model": args.model,
        "tagline": args.tagline or f"{args.model} via vLLM",
        "readme": args.readme or f"Deployed via chutes-deploy skill.",
        "node_selector": {
            "gpu_count": args.gpu_count,
            "gpu_type": args.gpu,
        },
        "vllm_args": {
            "max_model_len": args.max_model_len,
            "gpu_memory_utilization": args.gpu_memory_utilization,
        },
        "revision": args.revision,
        "public": bool(args.public),
    }
    if args.trust_remote_code:
        body["vllm_args"]["trust_remote_code"] = True
    if args.dtype:
        body["vllm_args"]["dtype"] = args.dtype
    if args.quantization:
        body["vllm_args"]["quantization"] = args.quantization
    return body


def stream_build_logs(bearer: str, image_id: str, timeout_seconds: int = 1800) -> bool:
    """Poll /images/{id}/logs until the build terminates. Return True on success."""
    # Upstream may support SSE; a polling fallback keeps the script simple + resilient.
    start = time.time()
    last_marker = None
    while time.time() - start < timeout_seconds:
        try:
            resp = idp_request("GET", f"/images/{image_id}/logs", bearer=bearer)
        except RuntimeError as e:
            print(f"  log fetch error: {e}", file=sys.stderr)
            time.sleep(5)
            continue
        status = resp.get("status")
        marker = resp.get("marker") or resp.get("cursor")
        # Print any new lines
        for line in resp.get("lines", []) or []:
            print(f"  {line}")
        if status in ("succeeded", "ready", "built"):
            return True
        if status in ("failed", "error"):
            print(f"  build failed: {resp.get('detail', '')}", file=sys.stderr)
            return False
        if marker == last_marker:
            time.sleep(5)
        last_marker = marker
    print(f"  build log polling timed out after {timeout_seconds}s", file=sys.stderr)
    return False


def poll_warmup(bearer: str, chute_id: str, timeout_seconds: int = 1200) -> dict:
    """Poll /chutes/warmup/{id} until ready. Return the final response."""
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            resp = idp_request("GET", f"/chutes/warmup/{chute_id}", bearer=bearer)
        except RuntimeError as e:
            print(f"  warmup fetch error: {e}", file=sys.stderr)
            time.sleep(5)
            continue
        status = resp.get("status")
        progress = resp.get("progress")
        print(f"  warmup: {status} ({progress})" if progress is not None else f"  warmup: {status}")
        if status == "ready":
            return resp
        if status == "error":
            raise RuntimeError(f"warmup failed: {resp.get('detail', '')}")
        time.sleep(5)
    raise RuntimeError(f"warmup timed out after {timeout_seconds}s")


def create_alias(bearer: str, alias: str, model_id: str) -> None:
    try:
        idp_request("POST", "/model_aliases/", bearer=bearer, body={"alias": alias, "model": model_id})
        print(f"  alias '{alias}' → {model_id}")
    except RuntimeError as e:
        print(f"  alias creation failed (non-fatal): {e}", file=sys.stderr)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, help="HF repo id (e.g. Qwen/Qwen3-8B)")
    p.add_argument("--gpu", default="h100", help="GPU type (a100_80gb, h100, h200, l40s, …)")
    p.add_argument("--gpu-count", type=int, default=1)
    p.add_argument("--name", default=None, help="Chute name (owner/name)")
    p.add_argument("--tagline", default=None)
    p.add_argument("--readme", default=None)
    p.add_argument("--max-model-len", type=int, default=32768)
    p.add_argument("--gpu-memory-utilization", type=float, default=0.9)
    p.add_argument("--dtype", default=None)
    p.add_argument("--quantization", default=None)
    p.add_argument("--trust-remote-code", action="store_true")
    p.add_argument("--revision", default="main")
    p.add_argument("--public", action="store_true", help="Make the chute publicly callable")
    p.add_argument("--alias", default=None, help="Create this stable alias on success")
    p.add_argument("--dry-run", action="store_true", help="Print the body and exit")
    args = p.parse_args()

    body = build_body(args)

    if args.dry_run:
        print(json.dumps({"POST /chutes/vllm": body}, indent=2))
        return 0

    print("!! BETA — deploying a chute consumes real paid compute on Chutes.")
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

    print("POST /chutes/vllm …")
    try:
        resp = idp_request("POST", "/chutes/vllm", bearer=bearer, body=body)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
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

    if args.alias:
        print(f"creating alias '{args.alias}'…")
        create_alias(bearer, args.alias, model_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
