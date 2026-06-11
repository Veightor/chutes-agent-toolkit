---
name: chutes-usage-and-billing
description: "Chutes.ai usage, quotas, discounts, and billing diagnostics. Use when the user asks about Chutes spend, balance, top-ups, discounts, quota usage, subscription usage, invocation stats, payment history, or 'why is my bill high'. Triggers on: chutes usage, chutes billing, chutes quota, chutes discount, chutes balance, chutes spend, invocations stats, subscription usage, payments summary, spend audit, cost breakdown, monthly usage, four_hour burst, quota guard."
---

# chutes-usage-and-billing

> **Status: RE-VERIFIED LIVE 2026-06-11** (originally verified 2026-04-13 via `docs/chutes-maxi-wave-2.md` Track A.2). `spend_summary.py`, `cost_breakdown.py`, and `quota_guard.py` re-exercised end-to-end against the dev Chutes account; data shapes confirmed. The export endpoints changed since April — see Step 5.

## What this skill does

Answers three questions:

1. **"How much am I spending right now?"** — balance, subscription caps, current usage, active discounts, price overrides.
2. **"What's been consuming my spend?"** — time-bucketed breakdown of personal usage with token counts.
3. **"Am I about to hit a cap?"** — 4-hour burst + monthly subscription caps + per-chute quota checks for the chutes you care about.

This is a **read-only** skill. It never mutates billing state. Top-ups via crypto or Stripe happen out-of-band on the Chutes dashboard; the skill explains where to go but does not automate the flow.

## Walkthrough

### Step 1 — Quick spend summary

```bash
python <skill-scripts-dir>/spend_summary.py
```

Prints a one-screen table:

```
=== Chutes spend summary for @<username> ===
  balance:                $14.0054 USD
  TAO fair market value:  $211.3307

  subscription:           $20/month
  monthly cap:            $  4.7127 / $100.0000  [....................]   4.7%
                            resets 2026-05-02 15:48 UTC
  4-hour burst cap:       $  0.1093 / $  8.3333  [....................]   1.3%
                            resets 2026-06-11 20:00 UTC

  active discounts:       (none)
  price overrides:        (none)

  last 24h requests:      59
  last 24h tokens:         563,194 in /   3,723 out
```

All data pulled live — no cached values. If you just deposited and the balance looks wrong, wait a minute for the deposit to credit and re-run.

**Quirk (observed live 2026-06-11):** `monthly.reset_at` can lag — the API returned a reset date in the past (2026-05-02 on 2026-06-11) while `usage`/`remaining` tracked correctly. Trust the dollar figures, not the monthly reset timestamp.

**Plan tiers** (chutes.ai/pricing, 2026-06-11): **Plus $10/mo** (bundled quota + 6% off PAYG beyond it), **Pro $20/mo** (larger quota + 10% off PAYG beyond it), **Enterprise** (custom). The $20 Pro plan maps to the $100/month usage cap and $8.33 rolling 4-hour burst cap shown above (live-verified response shape); exact Plus-tier caps are not published in the static pricing page (unverified as of 2026-06-11). [BETA] A 25% discount is also available by opting into the research data-sharing proxy (`https://research-data-opt-in-proxy.chutes.ai/v1`, per chutes.ai/llms.txt) — enrollment shows up in `/users/me/discounts`; not exercised on this account.

### Step 2 — Cost / usage breakdown

```bash
python <skill-scripts-dir>/cost_breakdown.py --since 2026-06-01
python <skill-scripts-dir>/cost_breakdown.py --since 2026-06-01 --csv > spend.csv
```

Time-bucketed breakdown from `/users/{user_id}/usage`:

```
=== personal usage: 2026-06-08 -> (now) ===
  bucket                 count  in_tokens   out_tokens  amount
  2026-06-08 16:00          3     36,013         961    $0.00
  2026-06-10 03:00          6     64,558         451    $0.00
  2026-06-11 14:00         22    351,288       2,266    $0.00
  ...
  TOTAL                   104  1,042,391       8,771    $0.00
```

**Wave-2 finding:** the `/users/{user_id}/usage` endpoint returns **time-bucketed** data (by hour), not per-chute breakdown. There is no `group_by=chute` query parameter — probing `?group_by=chute` returns HTTP 400 `undeclared parameter`. Per-chute personal cost isolation is not available via a single endpoint; `quota_guard.py` hits `/users/me/quota_usage/{chute_id}` one chute at a time when you need per-chute data.

### Step 3 — Quota posture (am I going to hit a cap)

```bash
python <skill-scripts-dir>/quota_guard.py
```

Reports:
- **Subscription caps.** 4-hour and monthly — same data as `spend_summary.py`, plus a visual bar. Warns at 70% / 85% / 95% usage.
- **Global quota.** `/users/me/quotas` — warns on any non-default quota nearing its cap.
- **Per-chute quotas for chutes you use.** Optional `--chute <chute_id>` to spot-check, or `--alias <name>` to check every chute_id behind an alias.

Read-only. Wave 2 does NOT wire this into a daemon or alerting loop — that's a future wave-3 idea.

### Step 4 — Payment history and top-up

```bash
python <skill-scripts-dir>/spend_summary.py --show-topup-hint
```

Prints top-up instructions:

- **Crypto (TAO / SN64 / alpha tokens):** send to `payment_address` from `/users/me`. Auto-converts at `fmv` TAO rate. Credits within minutes. Non-refundable.
- **Stripe:** dashboard → `https://chutes.ai/app/api/billing-balance` → "Add Balance" → "Top up with Stripe".

For personal payment history on **your** account, use `/payments?page=0&limit=<n>` and filter client-side to your `payment_address`. `spend_summary.py --payments` does this filter for you.

**Wave-2 finding:** `/payments` returns a **global** list (13564+ entries as of 2026-04-13), not user-scoped. `/payments/summary/tao` returns `{today, this_month, total}` — also **platform-wide TAO deposits**, not personal (shape re-verified 2026-06-11; lifetime `total` ≈ 2.18M). Personal spend comes from `/users/me/subscription_usage` and `/users/{user_id}/usage`, not `/payments`.

### Step 5 — Downloadable exports

```bash
python <skill-scripts-dir>/download_export.py --year 2026 --month 04 --day 13 --hour 14 --out /tmp/chutes-hour.csv
python <skill-scripts-dir>/download_export.py --recent --out /tmp/chutes-recent.csv --year 2026 --month 04 --day 13 --hour 14
```

Fetches `/invocations/exports/{year}/{month}/{day}/{hour}.csv` or `/invocations/exports/recent` snapshots. These are **platform-wide hourly exports** — useful for benchmarking the catalog, not for personal spend auditing. Writes the raw bytes to disk; load into DuckDB / Pandas downstream if needed (wave-3 pipeline idea).

**Re-verified 2026-06-11 — three changes since the 2026-04-13 verification:**

1. **The hour path segment now requires a `.csv` suffix** (`/invocations/exports/2026/04/13/14.csv`). A bare zero-padded hour returns HTTP 400 `{"detail":"Invalid format: 14"}`; `.json` is also rejected — CSV is the only accepted format. `download_export.py` has been updated to append `.csv`.
2. **Exports appear frozen at 2026-04-20.** That is the latest date with a downloadable export (200, `text/csv`); every later date probed (2026-04-21 through 2026-06-11) returns 404 `Invocations export not found`. Whether export generation resumes is unknown (unverified as of 2026-06-11).
3. **`GET /invocations/exports/recent` returns HTTP 500** as of 2026-06-11 (server-side error; it worked on 2026-04-13). `--recent` is broken until the platform fixes it.

Columns (re-verified 2026-06-11 against the 2026-04-13 export): `parent_invocation_id,invocation_id,chute_id,chute_user_id,function_name,image_id,image_user_id,instance_id,miner_uid,miner_hotkey,started_at,completed_at,error_message,compute_multiplier,bounty,metrics` — `parent_invocation_id` and `bounty` were added since the wave-2 doc. The script uses a raw urllib fetch rather than the JSON-expecting `idp_request` helper.

## Endpoint map

| Area | Endpoint | Returns |
|---|---|---|
| Balance | `GET /users/me` | `{balance, payment_address, hotkey, coldkey, permissions, ...}` (instantaneous) |
| Subscription caps | `GET /users/me/subscription_usage` | `{subscription, custom, monthly_price, anchor_date, effective_date, updated_at, four_hour: {usage, cap, remaining, reset_at}, monthly: {usage, cap, remaining, reset_at}}` (shape re-verified 2026-06-11; `monthly.reset_at` may lag) |
| Quotas | `GET /users/me/quotas` | list of `{chute_id, quota, is_default, effective_date, ...}` entries |
| Per-chute quota usage | `GET /users/me/quota_usage/{chute_id}` | `{quota, used}` |
| Discounts | `GET /users/me/discounts` | list (often empty) |
| Price overrides | `GET /users/me/price_overrides` | list (often empty) |
| Time-bucketed personal usage | `GET /users/{user_id}/usage?page=0&limit=25` | paginated `{total, page, limit, items: [{bucket, amount, count, input_tokens, output_tokens}, ...]}` |
| Platform LLM stats | `GET /invocations/stats/llm` | ~77k list of `{chute_id, name, date, total_requests, total_input_tokens, total_output_tokens, average_tps, average_ttft}` — **aggregate / global**, NOT your personal usage |
| Platform diffusion stats | `GET /invocations/stats/diffusion` | similar shape |
| Platform rollup | `GET /invocations/usage` | ~2400 list of `{chute_id, date, usd_amount, invocation_count}` — **global**, not yours |
| Hourly export | `GET /invocations/exports/{y}/{m}/{d}/{hh}.csv` | platform-wide hourly CSV (`.csv` suffix required; latest available export is 2026-04-20 as of 2026-06-11) |
| Platform payments summary | `GET /payments/summary/tao` | `{today, this_month, total}` — **platform-wide TAO deposits**, not yours |
| Global payments list | `GET /payments?page=...` | paginated global payment history |
| TAO / USD rate | `GET /fmv` | `{tao: <usd>}` |
| Platform pricing | `GET /pricing` | `{tao_usd, compute_unit_estimate, gpu_price_estimates}` — NOT per-model token pricing |

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/spend_summary.py` | One-screen balance + caps + discounts + last-24h token counts | VERIFIED (2026-06-11) |
| `scripts/cost_breakdown.py` | Time-bucketed personal usage with --since / --csv | VERIFIED (2026-06-11) |
| `scripts/quota_guard.py` | Subscription + global + per-chute quota check with --chute / --alias | VERIFIED (2026-06-11) |
| `scripts/download_export.py` | Fetch a platform-wide hourly export snapshot | VERIFIED for historical hours through 2026-04-20 (2026-06-11, after `.csv` path fix); `--recent` broken server-side (HTTP 500 as of 2026-06-11) |

## Safety rules

- **Never write to billing state.** This skill is strictly read-only. Top-ups happen out-of-band on the dashboard.
- **Never print `cpk_` values.** All scripts pipe auth through `manage_credentials.py` subprocess.
- **Always distinguish personal from platform data.** Most `/invocations/*` and `/payments*` endpoints return global/aggregate data. The scripts label their output clearly so a user doesn't confuse the two and panic at a $2M platform total.
- **Cache warnings are advisory.** Subscription caps are enforced server-side; we just surface them early. A green `quota_guard.py` does not promise that the next request will succeed — it promises that, as of the last poll, you're not near the cap.

## Related skills

- `chutes-ai` (hub) — prerequisite credential setup.
- `chutes-routing` — pair with `cost-aware-routing.md` for spending discipline via pool construction.
- `chutes-mcp-portability` — `chutes_get_usage`, `chutes_get_quota`, `chutes_get_discounts` expose the same data via MCP to any agent.
- `chutes-platform-ops` (stub) — operator-tier audits that span multiple users/apps.
