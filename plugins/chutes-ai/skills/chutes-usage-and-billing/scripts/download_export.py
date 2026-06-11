#!/usr/bin/env python3
"""Fetch a platform-wide hourly export snapshot from /invocations/exports/.

Usage:
  python download_export.py --year 2026 --month 04 --day 13 --hour 14 [--out FILE]

The hour path segment must be zero-padded WITH a `.csv` suffix
(e.g. /invocations/exports/2026/04/13/14.csv) — re-verified live 2026-06-11.
A bare hour returns HTTP 400 "Invalid format"; `.json` is rejected too.
The response is written to the output file (default: stdout).

Known platform state as of 2026-06-11:
  - Latest available hourly export is 2026-04-20; later dates return 404
    "Invocations export not found".
  - GET /invocations/exports/recent returns HTTP 500 (server-side), so
    --recent is broken until the platform fixes it.

**These exports are platform-wide**, not personal spend. Use spend_summary.py
or cost_breakdown.py for personal data.

Exit codes:
  0 ok
  1 bad input / missing credentials
  2 Chutes API error
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from _common import api_key, CHUTES_API_BASE


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--day", type=int, required=True)
    p.add_argument("--hour", type=int, required=True, help="0-23")
    p.add_argument("--out", help="output path (default: stdout)")
    p.add_argument("--recent", action="store_true", help="Ignore date args; fetch /invocations/exports/recent")
    args = p.parse_args()

    try:
        bearer = api_key()
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.recent:
        path = "/invocations/exports/recent"
    else:
        # `.csv` suffix is required on the hour segment (HTTP 400 without it;
        # re-verified live 2026-06-11).
        path = f"/invocations/exports/{args.year}/{args.month:02d}/{args.day:02d}/{args.hour:02d}.csv"

    # Exports are CSV (wave-2 A.2 finding). Do a raw fetch so we don't try
    # to JSON-parse the body.
    url = CHUTES_API_BASE.rstrip("/") + path
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {bearer}", "Accept": "text/csv, application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read()
            content_type = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300] if e.fp else ""
        print(f"error: HTTP {e.code} on {path}: {detail}", file=sys.stderr)
        return 2
    except urllib.error.URLError as e:
        print(f"error: network: {e.reason}", file=sys.stderr)
        return 2

    if args.out:
        Path(args.out).write_bytes(body)
        print(f"wrote {len(body)} bytes to {args.out} ({content_type or 'unknown content-type'})")
    else:
        sys.stdout.buffer.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
