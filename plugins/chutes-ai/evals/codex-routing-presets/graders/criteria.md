---
type: llm
weight: 1
---

Should recommend default:latency for interactive edit-test loops and default:throughput for long or batch background work (noting the default alias family requires a routing pool configured once in the Chutes dashboard), and concrete live model IDs only after checking /v1/models for required features, context, modalities, pricing, and confidential_compute. Should mention that /v1/models does not expose TTFT/TPS and that latency/throughput strategy is handled by routing or /invocations/stats/llm. Should avoid stale named-model certainty.
