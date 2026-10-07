---
type: llm
weight: 1
---

Should give the two-command plugin install (/plugin marketplace add Veightor/chutes-agent-toolkit, /plugin install chutes-ai@chutes-agent-toolkit), store the key via manage_credentials.py in the OS keychain rather than pasting it into chat, and recommend a model by checking live /v1/models metadata (supported_features, pricing, context) or scripts/pick_model.py rather than asserting a stale named model. Must use Bearer auth facts and the cpk_... format placeholder, never a real-looking key.
