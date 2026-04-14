#!/usr/bin/env python3
"""Report Chutes.ai quota posture (subscription + global + per-chute).

Usage:
  python quota_guard.py
  python quota_guard.py --chute <chute_id>
  python quota_guard.py --alias <alias_name>
  python quota_guard.py --json

Read-only. Warns at 70% / 85% / 95% usage against any cap.

Exit codes:
  0 all clear
  1 missing credentials
  2 Chutes API error
  3 any cap is over 85% full (advisory — not enforcement)
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import api_key, idp_request, pct_bar


WARN_LOW = 0.70
WARN_MID = 0.85
WARN_HIGH = 0.95


def check_pct(pct: float) -> tuple[str, int]:
    if pct >= WARN_HIGH:
        return "CRIT", 3
    if pct >= WARN_MID:
        return "WARN", 3
    if pct >= WARN_LOW:
        return "OK-ish", 0
    return "OK", 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chute", action="append", default=[], help="chute_id to spot-check (repeatable)")
    p.add_argument("--alias", help="check every chute_id behind this alias")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        sub = idp_request("GET", "/users/me/subscription_usage", bearer=bearer)
        quotas = idp_request("GET", "/users/me/quotas", bearer=bearer)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    results: dict = {"subscription": None, "quotas": [], "per_chute": []}
    overall_exit = 0

    # Subscription caps
    if sub.get("subscription"):
        monthly = sub.get("monthly") or {}
        four_hour = sub.get("four_hour") or {}
        for label, cap_obj in (("monthly", monthly), ("four_hour", four_hour)):
            use = float(cap_obj.get("usage", 0.0))
            cap = float(cap_obj.get("cap", 0.0))
            pct = (use / cap) if cap > 0 else 0.0
            level, rc = check_pct(pct)
            overall_exit = max(overall_exit, rc)
            results["subscription"] = results.get("subscription") or {}
            results["subscription"][label] = {
                "usage": use, "cap": cap, "pct": pct, "level": level,
                "reset_at": cap_obj.get("reset_at"),
            }

    # Global quotas
    if isinstance(quotas, list):
        for q in quotas:
            results["quotas"].append(q)

    # Per-chute via --chute or --alias
    chute_ids_to_check = list(args.chute)
    if args.alias:
        try:
            all_aliases = idp_request("GET", "/model_aliases/", bearer=bearer)
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        matching = [a for a in all_aliases if a.get("alias") == args.alias]
        if not matching:
            print(f"error: alias {args.alias!r} not found", file=sys.stderr)
            return 1
        chute_ids_to_check.extend(matching[0].get("chute_ids", []))

    for cid in chute_ids_to_check:
        try:
            qu = idp_request("GET", f"/users/me/quota_usage/{cid}", bearer=bearer)
        except RuntimeError as e:
            results["per_chute"].append({"chute_id": cid, "error": str(e)})
            continue
        quota = int(qu.get("quota", 0) or 0)
        used = float(qu.get("used", 0.0) or 0.0)
        pct = (used / quota) if quota > 0 else 0.0
        level, rc = check_pct(pct)
        overall_exit = max(overall_exit, rc)
        results["per_chute"].append({
            "chute_id": cid, "quota": quota, "used": used, "pct": pct, "level": level,
        })

    if args.json:
        print(json.dumps(results, indent=2, default=str))
        return overall_exit

    # Pretty print
    print("=== Chutes quota posture ===")
    if results.get("subscription"):
        sub_res = results["subscription"]
        monthly = sub_res.get("monthly") or {}
        four_hour = sub_res.get("four_hour") or {}
        for label, obj in (("monthly", monthly), ("four_hour", four_hour)):
            if not obj:
                continue
            print(
                f"  sub.{label:<10} ${obj['usage']:>8.4f} / ${obj['cap']:>8.4f}  "
                f"{pct_bar(obj['usage'], obj['cap'])}  [{obj['level']}]"
            )
    else:
        print("  subscription:  (pay-as-you-go, no subscription caps)")

    print()
    if results["quotas"]:
        print("  global quotas:")
        for q in results["quotas"]:
            scope = q.get("chute_id") or "?"
            if scope == "*":
                scope = "(global)"
            print(f"    - {scope}: quota={q.get('quota')}  default={q.get('is_default')}")
    else:
        print("  global quotas:  (none)")

    print()
    if results["per_chute"]:
        print("  per-chute:")
        for r in results["per_chute"]:
            if "error" in r:
                print(f"    - {r['chute_id'][:12]}...  ERROR: {r['error']}")
                continue
            cid = r["chute_id"][:12] + "..."
            print(
                f"    - {cid}  used={r['used']:.2f} / quota={r['quota']}  "
                f"{pct_bar(r['used'], r['quota'])}  [{r['level']}]"
            )

    return overall_exit


if __name__ == "__main__":
    sys.exit(main())
