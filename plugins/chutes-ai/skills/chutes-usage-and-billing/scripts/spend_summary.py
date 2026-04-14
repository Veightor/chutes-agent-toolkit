#!/usr/bin/env python3
"""One-screen Chutes.ai spend summary.

Usage:
  python spend_summary.py [--json] [--show-topup-hint]

Pulls live:
  GET /users/me                  (balance, payment_address)
  GET /users/me/subscription_usage (caps)
  GET /users/me/discounts
  GET /users/me/price_overrides
  GET /users/{user_id}/usage?page=0&limit=24  (last 24h buckets for token counts)
  GET /fmv                        (TAO/USD rate)

Exit codes:
  0 ok
  1 missing credentials
  2 Chutes API error
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from _common import api_key, idp_request, pct_bar, fmt_usd


def _iso_short(s: str | None) -> str:
    if not s:
        return "(none)"
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return s


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true", help="Raw JSON instead of table")
    p.add_argument("--show-topup-hint", action="store_true", help="Append crypto + Stripe instructions")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        me = idp_request("GET", "/users/me", bearer=bearer)
        sub = idp_request("GET", "/users/me/subscription_usage", bearer=bearer)
        discounts = idp_request("GET", "/users/me/discounts", bearer=bearer)
        overrides = idp_request("GET", "/users/me/price_overrides", bearer=bearer)
        fmv = idp_request("GET", "/fmv", bearer=bearer)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    # Best-effort last-24h token counts (paginated, so grab first 25 buckets)
    user_id = me.get("user_id")
    tokens_in = tokens_out = req_count = 0
    if user_id:
        try:
            usage = idp_request("GET", f"/users/{user_id}/usage?page=0&limit=25", bearer=bearer)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            for item in usage.get("items", []):
                bucket = item.get("bucket")
                if not bucket:
                    continue
                try:
                    b = datetime.fromisoformat(bucket)
                except ValueError:
                    continue
                if b.tzinfo is None:
                    b = b.replace(tzinfo=timezone.utc)
                if b >= cutoff:
                    tokens_in += int(item.get("input_tokens", 0))
                    tokens_out += int(item.get("output_tokens", 0))
                    req_count += int(item.get("count", 0))
        except RuntimeError:
            pass

    if args.json:
        print(json.dumps({
            "me": me,
            "subscription_usage": sub,
            "discounts": discounts,
            "price_overrides": overrides,
            "fmv": fmv,
            "last_24h": {"requests": req_count, "input_tokens": tokens_in, "output_tokens": tokens_out},
        }, indent=2))
        return 0

    balance = me.get("balance") or 0.0
    username = me.get("username") or "?"
    tao_usd = fmv.get("tao") or 0.0

    print(f"=== Chutes spend summary for @{username} ===")
    print(f"  balance:                ${balance:.4f} USD")
    print(f"  TAO fair market value:  ${tao_usd:.4f}")
    print()

    if sub.get("subscription"):
        print(f"  subscription:           ${sub.get('monthly_price', 0):.0f}/month")
        monthly = sub.get("monthly") or {}
        four_hour = sub.get("four_hour") or {}
        m_use = float(monthly.get("usage", 0.0))
        m_cap = float(monthly.get("cap", 0.0))
        m_reset = _iso_short(monthly.get("reset_at"))
        h_use = float(four_hour.get("usage", 0.0))
        h_cap = float(four_hour.get("cap", 0.0))
        h_reset = _iso_short(four_hour.get("reset_at"))
        print(f"  monthly cap:            {fmt_usd(m_use)} / {fmt_usd(m_cap)}  {pct_bar(m_use, m_cap)}")
        print(f"                            resets {m_reset}")
        print(f"  4-hour burst cap:       {fmt_usd(h_use)} / {fmt_usd(h_cap)}  {pct_bar(h_use, h_cap)}")
        print(f"                            resets {h_reset}")
    else:
        print(f"  subscription:           (pay-as-you-go, no subscription)")
    print()

    if discounts:
        print(f"  active discounts:       {len(discounts)}")
        for d in discounts:
            print(f"    - {d.get('name', '?')}: {d.get('pct', '?')}%  scope={d.get('scope', '?')}")
    else:
        print(f"  active discounts:       (none)")

    if overrides:
        print(f"  price overrides:        {len(overrides)}")
        for o in overrides:
            print(f"    - {o.get('model', '?')}  prompt={o.get('prompt', '?')}  completion={o.get('completion', '?')}")
    else:
        print(f"  price overrides:        (none)")
    print()

    print(f"  last 24h requests:      {req_count}")
    print(f"  last 24h tokens:         {tokens_in:>7,} in / {tokens_out:>7,} out")

    if args.show_topup_hint:
        print()
        print("=== Top up ===")
        pay = me.get("payment_address") or "(see dashboard)"
        print(f"  Crypto (TAO / SN64 / alpha tokens): send to {pay}")
        print(f"  Stripe: https://chutes.ai/app/api/billing-balance -> Add Balance -> Top up with Stripe")

    return 0


if __name__ == "__main__":
    sys.exit(main())
