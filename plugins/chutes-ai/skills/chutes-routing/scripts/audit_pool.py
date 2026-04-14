#!/usr/bin/env python3
"""Audit an existing Chutes.ai routing pool against live /v1/models.

Usage:
  python audit_pool.py --alias interactive-fast
  python audit_pool.py --routing-string "m1,m2,m3,m4"
  python audit_pool.py --alias tee-chat --delete --yes

Checks each pool member against live data:
  - still exists
  - pricing delta vs. a baseline snapshot (optional)
  - supported_features unchanged
  - confidential_compute flag unchanged

Exit codes:
  0 audit clean
  1 bad input / alias not found
  2 warnings found (stale members, price drift, feature drop)
  3 Chutes API error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import api_key, idp_request, list_models, total_per_1m, effective_prompt_cost


def resolve_pool(bearer: str, alias: str | None, routing_string: str | None) -> list[dict]:
    """Return a list of pool-member dicts with model_id (and chute_id if alias)."""
    if alias:
        all_aliases = idp_request("GET", "/model_aliases/", bearer=bearer)
        matching = [a for a in all_aliases if a.get("alias") == alias]
        if not matching:
            raise RuntimeError(f"alias {alias!r} not found")
        chute_ids = matching[0].get("chute_ids", [])
        return [{"chute_id": cid, "model_id": None} for cid in chute_ids]
    if routing_string:
        base = routing_string.split(":")[0]
        return [{"chute_id": None, "model_id": mid.strip()} for mid in base.split(",") if mid.strip()]
    raise ValueError("must provide --alias or --routing-string")


def resolve_model_for_chute(models: list[dict], chute_id: str) -> dict | None:
    for m in models:
        if m.get("chute_id") == chute_id:
            return m
    return None


def resolve_model_for_id(models: list[dict], model_id: str) -> dict | None:
    for m in models:
        if m.get("id") == model_id:
            return m
    return None


def audit(members: list[dict], live: list[dict], baseline: dict | None) -> list[str]:
    warnings: list[str] = []
    baseline_members = (baseline or {}).get("members", {})

    for mem in members:
        tag = mem.get("model_id") or mem.get("chute_id")
        if mem.get("chute_id"):
            live_model = resolve_model_for_chute(live, mem["chute_id"])
        else:
            live_model = resolve_model_for_id(live, mem["model_id"])

        if live_model is None:
            warnings.append(f"MISSING {tag}: no longer in /v1/models (stale alias/pool)")
            continue

        live_model_id = live_model["id"]
        baseline_entry = baseline_members.get(live_model_id) or baseline_members.get(tag)

        if baseline_entry:
            old_prompt = float(baseline_entry.get("prompt", 0))
            new_prompt = effective_prompt_cost(live_model)
            if old_prompt and abs(new_prompt - old_prompt) / old_prompt > 0.20:
                pct = (new_prompt - old_prompt) / old_prompt * 100
                warnings.append(
                    f"PRICE_DRIFT {live_model_id}: prompt ${old_prompt:.4f} -> ${new_prompt:.4f} ({pct:+.0f}%)"
                )
            old_features = set(baseline_entry.get("features", []))
            new_features = set(live_model.get("supported_features") or [])
            dropped = old_features - new_features
            if dropped:
                warnings.append(f"FEATURE_DROP {live_model_id}: dropped {sorted(dropped)}")
            old_tee = bool(baseline_entry.get("confidential_compute"))
            new_tee = bool(live_model.get("confidential_compute"))
            if old_tee != new_tee:
                warnings.append(f"TEE_FLIP {live_model_id}: confidential_compute {old_tee} -> {new_tee}")
    return warnings


def print_pool_state(members: list[dict], live: list[dict]) -> None:
    print("Pool members:")
    for mem in members:
        if mem.get("chute_id"):
            live_model = resolve_model_for_chute(live, mem["chute_id"])
            tag = mem["chute_id"][:12] + "..."
        else:
            live_model = resolve_model_for_id(live, mem["model_id"])
            tag = mem["model_id"]
        if live_model:
            p = live_model.get("pricing") or {}
            tee = "TEE" if live_model.get("confidential_compute") else "   "
            feats = ",".join(live_model.get("supported_features") or [])
            print(f"  {tag}  ok  {tee}  id={live_model['id']}  prompt=${p.get('prompt')}  ctx={live_model.get('context_length')}  [{feats}]")
        else:
            print(f"  {tag}  MISSING")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--alias", help="existing alias to audit")
    grp.add_argument("--routing-string", help="comma-separated model ids (optionally with :strategy suffix)")
    p.add_argument("--baseline", help="path to a baseline JSON for drift detection")
    p.add_argument("--delete", action="store_true", help="delete the alias after audit (requires --yes)")
    p.add_argument("--yes", action="store_true", help="confirm destructive operations")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        members = resolve_pool(bearer, args.alias, args.routing_string)
    except (RuntimeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        live = list_models(bearer)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3

    print_pool_state(members, live)
    print()

    baseline = None
    if args.baseline:
        try:
            baseline = json.loads(Path(args.baseline).read_text())
        except Exception as e:
            print(f"  warning: could not read baseline {args.baseline}: {e}", file=sys.stderr)

    warnings = audit(members, live, baseline)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  ! {w}")
        if args.delete:
            print("\nNot deleting: audit found warnings. Re-run without --delete to inspect.", file=sys.stderr)
            return 2
        return 2

    print("audit clean.")

    if args.delete:
        if not args.alias:
            print("error: --delete requires --alias", file=sys.stderr)
            return 1
        if not args.yes:
            print(f"error: --delete requires --yes (will remove alias {args.alias!r})", file=sys.stderr)
            return 1
        try:
            idp_request("DELETE", f"/model_aliases/{args.alias}", bearer=bearer)
            print(f"deleted alias {args.alias!r}")
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
