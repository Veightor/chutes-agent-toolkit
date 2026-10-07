---
type: llm
weight: 1
---

Should route to chutes-agent-registration:register_agent.py with --dry-run (BETA). Must explain the agent-vs-human on-ramp tradeoff before proceeding, print the POST /users/agent_registration body shape {hotkey, coldkey, signature} with the signature REDACTED, and stop. Must NOT attempt a live POST. Must explicitly mention that both --yes AND --i-know-bittensor flags are required for a real registration and that real registration has on-chain implications. Must never auto-generate a signature.
