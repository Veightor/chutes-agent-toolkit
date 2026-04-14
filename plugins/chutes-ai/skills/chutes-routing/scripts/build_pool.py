#!/usr/bin/env python3
"""Build a Chutes.ai routing pool from an intent.

Usage:
  python build_pool.py --intent interactive-fast --size 4
  python build_pool.py --intent tee-chat --size 3 --alias tee-chat
  python build_pool.py --intent custom --require-feature tools --max-prompt-cost 0.30 --size 3

Intents (see references/alias-packs.md for full definitions):
  interactive-fast      text I/O, cheapest, :latency suggested
  interactive-rich      reasoning + long ctx, :latency suggested
  cheap-background      single cheapest, :throughput or none
  private-reasoning     confidential + reasoning, :latency suggested
  tee-chat              confidential + text, :latency suggested
  agent-coder           tools + long ctx, failover-only
  custom                build your own from --filter / --require-feature / etc.

Exit codes:
  0 pool built (and alias created on success if --alias)
  1 bad input / no candidates / alias already exists without --replace
  2 Chutes API error
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Callable

from _common import api_key, idp_request, list_models, total_per_1m, effective_prompt_cost


INTENT_SUFFIX = {
    "interactive-fast": ":latency",
    "interactive-rich": ":latency",
    "cheap-background": ":throughput",
    "private-reasoning": ":latency",
    "tee-chat": ":latency",
    "agent-coder": "",
    "custom": "",
}


def filter_interactive_fast(m: dict) -> bool:
    return "text" in (m.get("input_modalities") or []) and total_per_1m(m) > 0


def filter_interactive_rich(m: dict) -> bool:
    feats = m.get("supported_features") or []
    return (
        "reasoning" in feats
        and (m.get("context_length") or 0) >= 32768
        and total_per_1m(m) > 0
    )


def filter_cheap_background(m: dict) -> bool:
    return "text" in (m.get("input_modalities") or []) and total_per_1m(m) > 0


def filter_private_reasoning(m: dict) -> bool:
    feats = m.get("supported_features") or []
    return bool(m.get("confidential_compute")) and "reasoning" in feats


def filter_tee_chat(m: dict) -> bool:
    return bool(m.get("confidential_compute")) and "text" in (m.get("input_modalities") or [])


def filter_agent_coder(m: dict) -> bool:
    feats = m.get("supported_features") or []
    return "tools" in feats and (m.get("context_length") or 0) >= 65536


INTENT_FILTERS: dict[str, Callable[[dict], bool]] = {
    "interactive-fast": filter_interactive_fast,
    "interactive-rich": filter_interactive_rich,
    "cheap-background": filter_cheap_background,
    "private-reasoning": filter_private_reasoning,
    "tee-chat": filter_tee_chat,
    "agent-coder": filter_agent_coder,
    "custom": lambda m: True,
}


def rank_by_cost_ascending(models: list[dict]) -> list[dict]:
    return sorted(models, key=total_per_1m)


def rank_quality_weighted(models: list[dict]) -> list[dict]:
    """For interactive-rich and agent-coder: penalize missing capabilities."""

    def score(m: dict) -> float:
        base = total_per_1m(m) or 1e9
        feats = m.get("supported_features") or []
        if "reasoning" not in feats:
            base *= 1.2
        q = (m.get("quantization") or "").lower()
        if q and q not in ("bf16", "fp16", "fp32"):
            base *= 1.3
        return base

    return sorted(models, key=score)


INTENT_RANKERS = {
    "interactive-fast": rank_by_cost_ascending,
    "interactive-rich": rank_quality_weighted,
    "cheap-background": rank_by_cost_ascending,
    "private-reasoning": rank_by_cost_ascending,
    "tee-chat": rank_by_cost_ascending,
    "agent-coder": rank_quality_weighted,
    "custom": rank_by_cost_ascending,
}


def apply_user_filters(models: list[dict], args: argparse.Namespace) -> list[dict]:
    out = []
    for m in models:
        if args.max_prompt_cost is not None and effective_prompt_cost(m) > args.max_prompt_cost:
            continue
        if args.require_feature:
            feats = m.get("supported_features") or []
            if not all(f in feats for f in args.require_feature):
                continue
        if args.tee_only and not m.get("confidential_compute"):
            continue
        if args.min_context and (m.get("context_length") or 0) < args.min_context:
            continue
        out.append(m)
    return out


def print_pool(models: list[dict], intent: str) -> None:
    suffix = INTENT_SUFFIX.get(intent, "")
    print(f"=== {intent} ({len(models)} models) ===")
    for i, m in enumerate(models, 1):
        p = m.get("pricing") or {}
        ctx = m.get("context_length")
        tee = "TEE" if m.get("confidential_compute") else "    "
        feats = ",".join(m.get("supported_features") or [])
        print(
            f"  {i}. {m['id']}  {tee}  "
            f"prompt=${p.get('prompt'):>6}  completion=${p.get('completion'):>6}  "
            f"ctx={ctx}  [{feats}]"
        )
    print()
    inline = ",".join(m["id"] for m in models)
    print("Inline routing string:")
    print(f"  {inline}{suffix}")
    print()
    print("Example usage:")
    print(f'  model="{inline}{suffix}"')


def create_alias(bearer: str, alias: str, chute_ids: list[str], replace: bool) -> None:
    if replace:
        try:
            idp_request("DELETE", f"/model_aliases/{alias}", bearer=bearer)
            print(f"  deleted existing alias {alias!r}")
        except RuntimeError:
            pass
    idp_request(
        "POST",
        "/model_aliases/",
        bearer=bearer,
        body={"alias": alias, "chute_ids": chute_ids},
    )
    print(f"  alias {alias!r} -> {len(chute_ids)} chute_ids")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--intent", required=True, choices=list(INTENT_FILTERS.keys()))
    p.add_argument("--size", type=int, default=4)
    p.add_argument("--max-prompt-cost", type=float, default=None, help="USD per 1M prompt tokens cap")
    p.add_argument("--require-feature", action="append", default=[], help="repeatable: tools, json_mode, reasoning, structured_outputs")
    p.add_argument("--tee-only", action="store_true")
    p.add_argument("--min-context", type=int, default=None)
    p.add_argument("--alias", default=None, help="If set, POST this as a /model_aliases/ entry")
    p.add_argument("--replace", action="store_true", help="Delete + recreate if alias exists")
    p.add_argument("--dry-run", action="store_true", help="Don't write anything to Chutes")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        all_models = list_models(bearer)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    filt = INTENT_FILTERS[args.intent]
    ranked = INTENT_RANKERS[args.intent]

    pool = [m for m in all_models if filt(m)]
    pool = apply_user_filters(pool, args)
    pool = ranked(pool)
    pool = pool[: args.size]

    if not pool:
        print(
            f"error: no candidates for intent '{args.intent}' after filters.\n"
            f"       Try relaxing --max-prompt-cost / --require-feature / --tee-only.",
            file=sys.stderr,
        )
        return 1

    print_pool(pool, args.intent)

    if args.alias and not args.dry_run:
        chute_ids = [m.get("chute_id") for m in pool if m.get("chute_id")]
        if not chute_ids:
            print(
                "\nwarning: no chute_ids on ranked models; alias not created.",
                file=sys.stderr,
            )
            return 1
        print()
        print(f"Creating alias {args.alias!r}…")
        try:
            create_alias(bearer, args.alias, chute_ids, replace=args.replace)
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
