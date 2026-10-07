---
type: llm
weight: 1
---

Should route to chutes-routing:build_pool.py. Should query live /v1/models, apply the interactive-fast filter (text I/O, cheapest-first), take top N (3-4), print the models with prompt/completion prices, emit an inline routing string with the :latency suffix, and (if --alias is requested) POST /model_aliases/ with {alias, chute_ids:[...]} - NOT {alias, model}. Should not pretend /v1/models has average_ttft/average_tps; client-side ranks by cost, server-side :latency ranks by TTFT.
