---
type: llm
weight: 1
---

Should route to the chutes-mcp-portability skill (BETA). Should install the chutes-mcp-server via uv tool install (from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server), run generate_agent_config.py --target cursor to write .cursor/mcp.json, ensure CHUTES_API_KEY is exported from the keychain via manage_credentials.py, and run chutes-mcp-server --self-check (which calls chutes_list_models with limit=1). Must never embed a raw cpk_ value into the config file; must use ${env:CHUTES_API_KEY}. Must acknowledge that read-only MCP tools graduate out of BETA after a verified call but write/deploy MCP tools stay BETA permanently.
