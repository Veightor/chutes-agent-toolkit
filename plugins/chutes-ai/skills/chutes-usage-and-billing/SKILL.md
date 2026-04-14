---
name: chutes-usage-and-billing
description: "Chutes.ai usage, quotas, discounts, and billing diagnostics. Use when the user asks about Chutes spend, balance, top-ups, discounts, quota usage, subscription usage, invocation stats, payment history, or 'why is my bill high'. Triggers on: chutes usage, chutes billing, chutes quota, chutes discount, chutes balance, chutes spend, invocations stats, subscription usage, payments summary, spend audit, cost breakdown, monthly usage, four_hour burst, quota guard."
---

# chutes-usage-and-billing

> **Status: VERIFIED LIVE 2026-04-13** via `docs/chutes-maxi-wave-2.md` Track A.2 — every script's endpoint was exercised against the dev Chutes account, data shapes confirmed, output tables verified.

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
  balance:                $14.01 USD
  TAO fair market value:  $256.55

  subscription:           $20/month
  monthly cap:            $0.08 / $100.00  (99.9% remaining, resets 2026-05-02)
  4-hour burst cap:       $0.00 / $8.33    (100% remaining, resets 2026-04-14 04:00 UTC)

  active discounts:       (none)
  price overrides:        (none)

  last 24h requests:      8
  last 24h tokens:         7,330 in / 10,293 out
```

All data pulled live — no cached values. If you just deposited and the balance looks wrong, wait a minute for the deposit to credit and re-run.

### Step 2 — Cost / usage breakdown

```bash
python <skill-scripts-dir>/cost_breakdown.py --since 2026-04-01
python <skill-scripts-dir>/cost_breakdown.py --since 2026-04-01 --csv > spend.csv
```

Time-bucketed breakdown from `/users/{user_id}/usage`:

```
=== personal usage: 2026-04-01 -> 2026-04-14 ===
  bucket                 count  in_tokens   out_tokens  amount
  2026-04-10 18:00          8      7330       10293     $0.00
  2026-04-11 09:00         12     14200       18502     $0.00
  2026-04-13 23:00         42     82104       95210     $0.07
  ...
  TOTAL                    64    103634      124005     $0.07
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

**Wave-2 finding:** `/payments` returns a **global** list (13564+ entries), not user-scoped. `/payments/summary/tao` returns `{today, this_month, total}` — also **platform-wide TAO deposits**, not personal. Personal spend comes from `/users/me/subscription_usage` and `/users/{user_id}/usage`, not `/payments`.

### Step 5 — Downloadable exports

```bash
python <skill-scripts-dir>/download_export.py --recent --out /tmp/chutes-recent.csv --year 2026 --month 04 --day 13 --hour 14
python <skill-scripts-dir>/download_export.py --year 2026 --month 04 --day 13 --hour 14 --out /tmp/chutes-hour.csv
```

Fetches `/invocations/exports/{year}/{month}/{day}/{hour_format}` or `/invocations/exports/recent` snapshots. These are **platform-wide hourly exports** — useful for benchmarking the catalog, not for personal spend auditing. Writes the raw bytes to disk; load into DuckDB / Pandas downstream if needed (wave-3 pipeline idea).

**Wave-2 finding:** exports are returned as **CSV** (`text/csv; charset=utf-8`), not JSON. Columns: `invocation_id,chute_id,chute_user_id,function_name,image_id,image_user_id,instance_id,miner_uid,miner_hotkey,started_at,completed_at,error_message,compute_multiplier,metrics`. The script uses a raw urllib fetch rather than the JSON-expecting `idp_request` helper. `HEAD /invocations/exports/recent` returns 404 but `GET` works — quirky but confirmed live.

## Endpoint map

| Area | Endpoint | Returns |
|---|---|---|
| Balance | `GET /users/me` | `{balance, payment_address, hotkey, coldkey, permissions, ...}` (instantaneous) |
| Subscription caps | `GET /users/me/subscription_usage` | `{subscription, monthly_price, four_hour: {usage, cap, remaining, reset_at}, monthly: {usage, cap, remaining, reset_at}}` |
| Quotas | `GET /users/me/quotas` | list of `{chute_id, quota, is_default, effective_date, ...}` entries |
| Per-chute quota usage | `GET /users/me/quota_usage/{chute_id}` | `{quota, used}` |
| Discounts | `GET /users/me/discounts` | list (often empty) |
| Price overrides | `GET /users/me/price_overrides` | list (often empty) |
| Time-bucketed personal usage | `GET /users/{user_id}/usage?page=0&limit=25` | paginated `{total, page, limit, items: [{bucket, amount, count, input_tokens, output_tokens}, ...]}` |
| Platform LLM stats | `GET /invocations/stats/llm` | ~77k list of `{chute_id, name, date, total_requests, total_input_tokens, total_output_tokens, average_tps, average_ttft}` — **aggregate / global**, NOT your personal usage |
| Platform diffusion stats | `GET /invocations/stats/diffusion` | similar shape |
| Platform rollup | `GET /invocations/usage` | ~2400 list of `{chute_id, date, usd_amount, invocation_count}` — **global**, not yours |
| Hourly export | `GET /invocations/exports/{y}/{m}/{d}/{hh}` | platform-wide hourly JSON |
| Platform payments summary | `GET /payments/summary/tao` | `{today, this_month, total}` — **platform-wide TAO deposits**, not yours |
| Global payments list | `GET /payments?page=...` | paginated global payment history |
| TAO / USD rate | `GET /fmv` | `{tao: <usd>}` |
| Platform pricing | `GET /pricing` | `{tao_usd, compute_unit_estimate, gpu_price_estimates}` — NOT per-model token pricing |

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/spend_summary.py` | One-screen balance + caps + discounts + last-24h token counts | VERIFIED (2026-04-13) |
| `scripts/cost_breakdown.py` | Time-bucketed personal usage with --since / --csv | VERIFIED (2026-04-13) |
| `scripts/quota_guard.py` | Subscription + global + per-chute quota check with --chute / --alias | VERIFIED (2026-04-13) |
| `scripts/download_export.py` | Fetch a platform-wide hourly export snapshot | VERIFIED (2026-04-13) |

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
