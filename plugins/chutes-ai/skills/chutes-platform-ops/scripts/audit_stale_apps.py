#!/usr/bin/env python3
"""Report OAuth apps that look abandoned — zero auths, old age, or both.

Usage:
  python audit_stale_apps.py
  python audit_stale_apps.py --min-age-days 30
  python audit_stale_apps.py --all   # audit the whole platform, not just yours

Read-only. Does NOT delete anything — printing a candidate list is the whole job.

Exit codes:
  0 audit clean
  1 missing credentials
  2 Chutes API error
  3 stale apps found (advisory)
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone

from _common import api_key, idp_request, paginate, my_user_id


def parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--min-age-days", type=int, default=0, help="Only flag apps older than this")
    p.add_argument("--all", action="store_true", help="Audit every app, not just mine")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        all_apps = paginate(bearer, "/idp/apps", page_size=100)
        auths = paginate(bearer, "/idp/authorizations", page_size=100)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.all:
        apps = all_apps
    else:
        try:
            uid = my_user_id(bearer)
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        apps = [a for a in all_apps if a.get("user_id") == uid]

    auth_counts: dict[str, int] = {}
    for a in auths:
        aid = a.get("app_id")
        if aid:
            auth_counts[aid] = auth_counts.get(aid, 0) + 1

    now = datetime.now(timezone.utc)
    min_age = timedelta(days=args.min_age_days)

    zero_auth: list[dict] = []
    old_apps: list[dict] = []

    for a in apps:
        app_id = a.get("app_id")
        created = parse_iso(a.get("created_at"))
        age_days = (now - created).days if created else None
        if args.min_age_days and (age_days is None or age_days < args.min_age_days):
            continue
        auth_n = auth_counts.get(app_id, 0)
        entry = {**a, "_age_days": age_days, "_auths": auth_n}
        if auth_n == 0:
            zero_auth.append(entry)
        elif age_days is not None and age_days >= 90:
            old_apps.append(entry)

    print(f"=== stale OAuth app audit ({'platform' if args.all else 'mine'}) ===")
    print(f"  apps audited: {len(apps)}")
    print()

    if zero_auth:
        print(f"  Zero-authorization apps ({len(zero_auth)}):")
        for e in sorted(zero_auth, key=lambda x: x.get("_age_days") or 0, reverse=True):
            age = f"{e['_age_days']}d" if e["_age_days"] is not None else "?"
            name = (e.get("name") or "?")[:40]
            print(f"    - {name:<40}  app_id={(e.get('app_id') or '')[:12]}...  age={age}")
        print()

    if old_apps:
        print(f"  Apps aged >= 90d with some activity ({len(old_apps)}):")
        for e in sorted(old_apps, key=lambda x: x.get("_age_days") or 0, reverse=True):
            age = f"{e['_age_days']}d" if e["_age_days"] is not None else "?"
            name = (e.get("name") or "?")[:40]
            print(f"    - {name:<40}  app_id={(e.get('app_id') or '')[:12]}...  auths={e['_auths']}  age={age}")
        print()

    if not zero_auth and not old_apps:
        print("  audit clean.")
        return 0

    print("  Recommendation: inspect each before taking action.")
    print("    Delete:    curl -X DELETE -H 'Authorization: Bearer $CHUTES_API_KEY' https://api.chutes.ai/idp/apps/<app_id>")
    print("    Keep:      no action needed")
    return 3


if __name__ == "__main__":
    sys.exit(main())
