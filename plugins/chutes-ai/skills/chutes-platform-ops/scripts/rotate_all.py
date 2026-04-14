#!/usr/bin/env python3
"""Bulk-rotate client secrets across many OAuth apps.

Usage:
  python rotate_all.py --match "Test*" --dry-run          # always first
  python rotate_all.py --match "Test*" --yes              # actually rotate
  python rotate_all.py --match "*" --yes --skip-until <app_id>   # resume after failure

Matches app NAMES (case-insensitive fnmatch). Iterates matching apps
sequentially — no parallelism — so a mid-run crash leaves a partial state
you can reason about.

Safety:
  - dry-run is the default behavior when --yes is NOT passed.
  - Each rotated secret is stored under a fresh keychain profile of the form
    oauth.rotate-<timestamp>-<name-slug>. The old profile (if any) is not
    touched.
  - The script NEVER prints a full csc_ value — only redacted previews.

Exit codes:
  0 dry-run printed, or all rotations succeeded
  1 bad input / missing credentials / --yes missing on live run
  2 Chutes API error mid-run (check output for the app_id that failed)
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from datetime import datetime

from _common import api_key, idp_request, paginate, put_secret, redact, my_user_id


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:40] or "unnamed"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--match", required=True, help="fnmatch pattern against app names (e.g. 'Test*', '*')")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--yes", action="store_true", help="Required for real rotation")
    p.add_argument("--skip-until", help="Resume after this app_id; earlier apps are skipped")
    p.add_argument("--all", action="store_true", help="Match apps across the whole platform, not just mine")
    args = p.parse_args()

    if not args.dry_run and not args.yes:
        print("error: refuse to rotate without --yes. Use --dry-run to preview.", file=sys.stderr)
        return 1

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

    if args.all:
        apps = all_apps
    else:
        try:
            uid = my_user_id(bearer)
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        apps = [a for a in all_apps if a.get("user_id") == uid]

    pattern = args.match
    matched = [a for a in apps if fnmatch.fnmatchcase((a.get("name") or "").lower(), pattern.lower())]

    if args.skip_until:
        idx = next((i for i, a in enumerate(matched) if a.get("app_id") == args.skip_until), None)
        if idx is None:
            print(f"warning: --skip-until {args.skip_until} not in matched set; ignoring", file=sys.stderr)
        else:
            matched = matched[idx + 1 :]

    print(f"=== rotate_all.py ===")
    print(f"  pattern:  {pattern}")
    print(f"  matched:  {len(matched)} apps")
    print(f"  dry-run:  {args.dry_run}")
    print()
    for a in matched:
        name = a.get("name") or "?"
        app_id = a.get("app_id") or "?"
        print(f"  - {name}  app_id={app_id[:12]}...")
    print()

    if args.dry_run:
        print("dry-run: no rotations performed.")
        return 0

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    failed_app_id: str | None = None
    for a in matched:
        app_id = a.get("app_id")
        name = a.get("name") or "?"
        profile = f"oauth.rotate-{timestamp}-{slugify(name)}"
        print(f"rotating {name[:40]}  app_id={app_id[:12]}...")
        try:
            resp = idp_request("POST", f"/idp/apps/{app_id}/regenerate-secret", bearer=bearer, body={})
        except RuntimeError as e:
            print(f"  FAIL: {e}", file=sys.stderr)
            failed_app_id = app_id
            break

        new_secret = resp.get("client_secret") or resp.get("clientSecret")
        client_id = resp.get("client_id") or a.get("client_id") or "?"
        if not new_secret:
            print(f"  FAIL: response missing client_secret", file=sys.stderr)
            failed_app_id = app_id
            break

        try:
            put_secret("client_id", client_id, profile=profile)
            put_secret("client_secret", new_secret, profile=profile)
            put_secret("app_id", app_id, profile=profile)
        except RuntimeError as e:
            print(f"  CRITICAL: rotated on server but keychain write failed: {e}", file=sys.stderr)
            print(f"            Profile name that would have held it: {profile}", file=sys.stderr)
            failed_app_id = app_id
            break

        print(f"  ok  profile={profile}  new_secret={redact(new_secret)}")

    if failed_app_id:
        print(
            f"\nStopped at app_id={failed_app_id}. To resume: "
            f"rotate_all.py --match {pattern!r} --yes --skip-until {failed_app_id}",
            file=sys.stderr,
        )
        return 2

    print(f"\nok: rotated {len(matched)} apps. Redeploy every dependent service.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
