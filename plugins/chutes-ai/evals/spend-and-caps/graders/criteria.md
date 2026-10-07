---
type: llm
weight: 1
---

Should route to chutes-usage-and-billing:spend_summary.py + quota_guard.py. Must pull balance from /users/me, subscription caps (four_hour + monthly) from /users/me/subscription_usage, discounts from /users/me/discounts, price overrides from /users/me/price_overrides, and TAO rate from /fmv. Must clearly label these as PERSONAL data and NOT confuse them with /payments/summary/tao (which is platform-wide TAO deposits, not the user's bill). Must show ASCII progress bars against caps and warn at 70/85/95 percent.
