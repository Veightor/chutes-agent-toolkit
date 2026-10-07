---
type: llm
weight: 1
---

Should explain model routing strategies (default, default:latency, default:throughput), recommend using default:latency for a chatbot, note that as of 2026-06-11 every hosted model is TEE-backed (confidential_compute=true) so the TEE-only constraint is satisfied by the whole catalog, build a routing pool of 3-4 fast models, and provide working code examples using either inline routing strings or the default alias.
