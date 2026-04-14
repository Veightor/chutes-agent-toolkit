#!/usr/bin/env python3
"""Alias fleet management — list / create / delete with operator semantics.

Usage:
  python alias_crud.py --list
  python alias_crud.py --list --mine           # only aliases with my owner_id (if present)
  python alias_crud.py --create --alias team-fast --chute-id <uuid> --chute-id <uuid>
  python alias_crud.py --delete --alias team-fast --yes
  python alias_crud.py --json

Same endpoints as chutes-routing/build_pool.py and chutes-deploy/alias_deploy.py
but with operator lens: bulk list, destructive ops gated by --yes, no intent
filters.

Exit codes:
  0 ok
  1 bad input / missing credentials / dangerous op without --yes
  2 Chutes API error
"""
from __future__ import annotations

import argparse
import json
import sys

from _common import api_key, idp_request


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument("--list", action="store_true")
    action.add_argument("--create", action="store_true")
    action.add_argument("--delete", action="store_true")
    p.add_argument("--alias", help="Alias name (required for --create / --delete)")
    p.add_argument("--chute-id", dest="chute_ids", action="append", default=[], help="chute UUID (repeatable, for --create)")
    p.add_argument("--replace", action="store_true", help="For --create: delete existing alias first")
    p.add_argument("--yes", action="store_true", help="Required for --delete")
    p.add_argument("--json", action="store_true")
    p.add_argument("--mine", action="store_true", help="With --list, try to filter to aliases owned by my user_id (if owner is exposed)")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.list:
        try:
            aliases = idp_request("GET", "/model_aliases/", bearer=bearer)
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2

        if args.mine:
            try:
                me = idp_request("GET", "/users/me", bearer=bearer)
                uid = me.get("user_id")
            except RuntimeError:
                uid = None
            if uid:
                aliases = [a for a in aliases if a.get("user_id") == uid or a.get("owner_id") == uid]

        if args.json:
            print(json.dumps(aliases, indent=2, default=str))
            return 0

        print(f"=== aliases: {len(aliases)} ===")
        for a in aliases:
            name = a.get("alias", "?")
            chutes = a.get("chute_ids") or []
            created = (a.get("created_at") or "")[:10]
            print(f"  {name:<30}  chutes={len(chutes)}  created={created}")
        return 0

    if args.create:
        if not args.alias or not args.chute_ids:
            print("error: --create requires --alias and at least one --chute-id", file=sys.stderr)
            return 1
        if args.replace:
            try:
                idp_request("DELETE", f"/model_aliases/{args.alias}", bearer=bearer)
                print(f"deleted existing alias {args.alias!r}")
            except RuntimeError:
                pass
        try:
            idp_request(
                "POST",
                "/model_aliases/",
                bearer=bearer,
                body={"alias": args.alias, "chute_ids": args.chute_ids},
            )
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"ok: alias {args.alias!r} -> {len(args.chute_ids)} chute_ids")
        return 0

    if args.delete:
        if not args.alias:
            print("error: --delete requires --alias", file=sys.stderr)
            return 1
        if not args.yes:
            print(f"error: --delete requires --yes (will remove alias {args.alias!r})", file=sys.stderr)
            return 1
        try:
            idp_request("DELETE", f"/model_aliases/{args.alias}", bearer=bearer)
        except RuntimeError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"deleted alias {args.alias!r}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
