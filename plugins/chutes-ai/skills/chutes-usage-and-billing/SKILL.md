---
name: chutes-usage-and-billing
status: beta
description: "[BETA STUB — not yet implemented] Chutes.ai usage, quotas, discounts, and billing diagnostics. Use when the user asks about Chutes spend, balance, top-ups, discounts, quota usage, subscription usage, invocation stats, or payment history. Triggers on: chutes usage, chutes billing, chutes quota, chutes discount, chutes balance, invocations stats, subscription usage, payments summary, spend audit."
---

# chutes-usage-and-billing **[BETA — wave 2 stub]**

> **Status: BETA** — stub only. Read-only endpoints are exposed today through the `chutes-mcp-portability` MCP server (`chutes_get_usage`, `chutes_get_quota`, `chutes_get_discounts`). Use that skill until this one is written.

## Scope (when filled in)

- Balance, top-ups (crypto and Stripe), discounts, quotas.
- Per-model invocation stats (LLM and diffusion).
- Subscription usage vs. limits.
- Payment history and TAO summaries.
- "Doctor" workflows for unexpected spend.

## Endpoint map

| Area | Endpoint |
|---|---|
| Quotas | `GET /users/me/quotas`, `GET /users/me/quota_usage/{chute_id}` |
| Discounts | `GET /users/me/discounts` |
| Subscription | `GET /users/me/subscription_usage` |
| LLM stats | `GET /invocations/stats/llm` |
| Diffusion stats | `GET /invocations/stats/diffusion` |
| Usage rollup | `GET /invocations/usage` |
| Exports | `GET /invocations/exports/{year}/{month}/{day}/{hour_format}` |
| Payments | `GET /payments`, `GET /payments/summary/tao` |
| Pricing | `GET /pricing`, `GET /fmv` |

## Status

Do not execute this skill yet. For one-off lookups, use the MCP tools from `chutes-mcp-portability`.
