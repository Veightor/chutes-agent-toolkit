---
type: llm
weight: 1
---

Should use other-agents/codex/README.md and docs/endpoint-guide.md. Must explain the OpenAI-compatible base URL https://llm.chutes.ai/v1, CHUTES_API_KEY as the durable secret name, Bearer auth, and a model value: a live model ID from /v1/models, or a routing alias such as default:latency once a routing pool is configured at chutes.ai/app -> Model Routing. Must not paste real-looking credentials (the cpk_... format placeholder is fine). Must state that Codex-specific built-in provider support is not claimed unless the installed runtime exposes that provider surface.
