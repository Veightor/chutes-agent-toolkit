#!/usr/bin/env python3
"""Create or update a stable model alias on Chutes.ai. [BETA]

Usage:
  python alias_deploy.py --alias interactive-fast --model myuser/qwen3-8b
  python alias_deploy.py --alias tee-chat --model deepseek-ai/DeepSeek-V3-0324-TEE --replace

Aliases are listed + recommended in:
  plugins/chutes-ai/skills/chutes-ai/references/model-aliases.md

Exit codes:
  0 alias set
  1 bad input
  2 Chutes API error
"""
from __future__ import annotations

import argparse
import sys

from _common import api_key, idp_request


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--alias", required=True, help="stable handle (e.g. interactive-fast)")
    p.add_argument("--model", required=True, help="model id the alias resolves to")
    p.add_argument(
        "--replace",
        action="store_true",
        help="If the alias already exists, delete and recreate it",
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    print(f"setting alias {args.alias!r} → {args.model}")
    if args.dry_run:
        return 0

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.replace:
        try:
            idp_request("DELETE", f"/model_aliases/{args.alias}", bearer=bearer)
            print(f"  deleted existing alias {args.alias!r}")
        except RuntimeError:
            pass  # not present — that's fine

    try:
        idp_request(
            "POST",
            "/model_aliases/",
            bearer=bearer,
            body={"alias": args.alias, "model": args.model},
        )
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"  alias set.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
