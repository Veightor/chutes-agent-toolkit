---
name: chutes-usage-and-billing
description: "Read-only Chutes.ai usage, quota, discount, and billing diagnostics for Hermes users. Triggers on: chutes usage, chutes billing, chutes quota, chutes discount, chutes balance, chutes spend, subscription usage, payments summary, cost breakdown, monthly usage, quota guard."
version: 0.2.0
author: Chutes Agent Toolkit
license: MIT
metadata:
  hermes:
    tags: [chutes, billing, usage, quotas, spend, hermes]
    status: verified-live
---

# Chutes Usage and Billing for Hermes

> Status: VERIFIED LIVE 2026-04-13. This is a read-only Hermes entry point for the full skill at `plugins/chutes-ai/skills/chutes-usage-and-billing/`.

## When to use this skill

Use when a Hermes user asks:
- How much am I spending on Chutes?
- What are my current balance, subscription caps, discounts, and quotas?
- What consumed my recent token usage?
- Am I about to hit a monthly, 4-hour burst, global, or per-chute quota?

This skill does not top up, pay invoices, or mutate billing state. Top-ups happen out-of-band in the Chutes dashboard.

## Hermes-facing workflow

Run from the repo root:

```bash
python plugins/chutes-ai/skills/chutes-usage-and-billing/scripts/spend_summary.py
python plugins/chutes-ai/skills/chutes-usage-and-billing/scripts/cost_breakdown.py --since 2026-04-01
python plugins/chutes-ai/skills/chutes-usage-and-billing/scripts/quota_guard.py
python plugins/chutes-ai/skills/chutes-usage-and-billing/scripts/download_export.py --recent --out /tmp/chutes-recent.csv
```

## Deep references

- `plugins/chutes-ai/skills/chutes-usage-and-billing/SKILL.md`
- `docs/credential-store.md`
- `docs/api-reference.md`

## Important live findings

- Personal spend comes from `/users/me/subscription_usage` and `/users/{user_id}/usage`.
- `/payments` and `/payments/summary/tao` are platform-wide aggregates, not personal billing ledgers.
- Invocation exports are platform-wide CSV snapshots, not JSON and not personal spend reports.

## Safety rules

- Never print `cpk_` values; scripts use `manage_credentials.py` for auth.
- Treat this skill as read-only. Do not automate dashboard top-ups or payment flows.
