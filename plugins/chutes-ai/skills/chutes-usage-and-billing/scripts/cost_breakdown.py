#!/usr/bin/env python3
"""Time-bucketed personal usage breakdown from /users/{user_id}/usage.

Usage:
  python cost_breakdown.py [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--csv]

Paginates /users/{user_id}/usage, filters by date range, prints a table
(or CSV to stdout with --csv). The endpoint is hourly-bucketed, not
per-chute — there is no group_by=chute parameter (wave-2 live probe
confirmed /users/{id}/usage?group_by=chute returns HTTP 400).

Exit codes:
  0 ok
  1 missing credentials / bad input
  2 Chutes API error
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from typing import Iterable

from _common import api_key, idp_request


def parse_date(s: str) -> datetime:
    try:
        d = datetime.strptime(s, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"bad date {s!r} (want YYYY-MM-DD): {e}") from None
    return d.replace(tzinfo=timezone.utc)


def fetch_all_usage(bearer: str, user_id: str) -> list[dict]:
    items: list[dict] = []
    page = 0
    page_size = 100
    while True:
        r = idp_request(
            "GET",
            f"/users/{user_id}/usage?page={page}&limit={page_size}",
            bearer=bearer,
        )
        batch = r.get("items", [])
        items.extend(batch)
        total = r.get("total") or 0
        if (page + 1) * page_size >= total or not batch:
            break
        page += 1
        if page > 200:  # safety stop at 20000 rows
            break
    return items


def filter_and_sort(items: Iterable[dict], since: datetime | None, until: datetime | None) -> list[dict]:
    out = []
    for it in items:
        bucket = it.get("bucket")
        if not bucket:
            continue
        try:
            b = datetime.fromisoformat(bucket)
        except ValueError:
            continue
        if b.tzinfo is None:
            b = b.replace(tzinfo=timezone.utc)
        if since and b < since:
            continue
        if until and b > until:
            continue
        out.append({**it, "_parsed": b})
    out.sort(key=lambda x: x["_parsed"])
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--since", help="YYYY-MM-DD lower bound (UTC, inclusive)")
    p.add_argument("--until", help="YYYY-MM-DD upper bound (UTC, inclusive)")
    p.add_argument("--csv", action="store_true", help="Emit CSV instead of a table")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        me = idp_request("GET", "/users/me", bearer=bearer)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    user_id = me.get("user_id")
    if not user_id:
        print("error: /users/me did not return user_id", file=sys.stderr)
        return 2

    try:
        since = parse_date(args.since) if args.since else None
        until = parse_date(args.until) if args.until else None
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        all_items = fetch_all_usage(bearer, user_id)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    filtered = filter_and_sort(all_items, since, until)

    total_in = total_out = total_count = 0
    total_amount = 0.0
    if args.csv:
        w = csv.writer(sys.stdout)
        w.writerow(["bucket", "count", "input_tokens", "output_tokens", "amount_usd"])
        for it in filtered:
            w.writerow([
                it["_parsed"].isoformat(),
                it.get("count", 0),
                it.get("input_tokens", 0),
                it.get("output_tokens", 0),
                it.get("amount", 0.0),
            ])
            total_count += int(it.get("count", 0))
            total_in += int(it.get("input_tokens", 0))
            total_out += int(it.get("output_tokens", 0))
            total_amount += float(it.get("amount", 0.0))
    else:
        since_str = since.strftime("%Y-%m-%d") if since else "(all)"
        until_str = until.strftime("%Y-%m-%d") if until else "(now)"
        print(f"=== personal usage: {since_str} -> {until_str} ===")
        print(f"  user: {me.get('username')}  total buckets: {len(filtered)}")
        print()
        print(f"  {'bucket':<20} {'count':>7} {'in_tokens':>12} {'out_tokens':>12} {'amount':>10}")
        print(f"  {'-' * 65}")
        for it in filtered:
            bucket = it["_parsed"].strftime("%Y-%m-%d %H:%M")
            c = int(it.get("count", 0))
            ti = int(it.get("input_tokens", 0))
            to = int(it.get("output_tokens", 0))
            amt = float(it.get("amount", 0.0))
            print(f"  {bucket:<20} {c:>7} {ti:>12,} {to:>12,} ${amt:>8.4f}")
            total_count += c
            total_in += ti
            total_out += to
            total_amount += amt
        print(f"  {'-' * 65}")
        print(f"  {'TOTAL':<20} {total_count:>7} {total_in:>12,} {total_out:>12,} ${total_amount:>8.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
