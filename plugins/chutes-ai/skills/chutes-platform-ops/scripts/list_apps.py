#!/usr/bin/env python3
"""List OAuth apps, filter to mine (or --all), join with authorization counts.

Usage:
  python list_apps.py
  python list_apps.py --all
  python list_apps.py --with-authorizations
  python list_apps.py --json

Wave-2 finding: /idp/apps?mine=true and ?user_id= are IGNORED server-side;
client-side filter on user_id is the only way.

Exit codes:
  0 ok
  1 bad input / missing credentials
  2 Chutes API error
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import api_key, idp_request, paginate, my_user_id


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--all", action="store_true", help="Show every app, not just yours")
    p.add_argument("--with-authorizations", action="store_true", help="Join each app with its live authorization count")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        all_apps = paginate(bearer, "/idp/apps", page_size=100)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    total = len(all_apps)
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
    if args.with_authorizations:
        try:
            auths = paginate(bearer, "/idp/authorizations", page_size=100)
        except RuntimeError as e:
            print(f"warning: could not fetch authorizations: {e}", file=sys.stderr)
            auths = []
        for a in auths:
            app_id = a.get("app_id")
            if app_id:
                auth_counts[app_id] = auth_counts.get(app_id, 0) + 1

    if args.json:
        out = []
        for a in apps:
            entry = {k: a.get(k) for k in ("app_id", "client_id", "user_id", "name", "description", "redirect_uris", "active", "created_at")}
            if args.with_authorizations:
                entry["authorizations"] = auth_counts.get(a.get("app_id"), 0)
            out.append(entry)
        print(json.dumps(out, indent=2))
        return 0

    scope = "all" if args.all else "mine"
    print(f"=== OAuth apps ({scope}): {len(apps)} of {total} platform-wide ===")
    print()
    header = f"  {'name':<34} {'app_id':<13} {'client_id':<25} {'created':<11} {'active':<7}"
    if args.with_authorizations:
        header += f" {'auths':<5}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for a in sorted(apps, key=lambda x: x.get("created_at") or "", reverse=True):
        name = (a.get("name") or "?")[:33]
        app_id = (a.get("app_id") or "?")[:12] + "..."
        cid = (a.get("client_id") or "?")[:24]
        created = (a.get("created_at") or "?")[:10]
        active = str(a.get("active", False))
        row = f"  {name:<34} {app_id:<13} {cid:<25} {created:<11} {active:<7}"
        if args.with_authorizations:
            row += f" {auth_counts.get(a.get('app_id'), 0):<5}"
        print(row)

    return 0


if __name__ == "__main__":
    sys.exit(main())
