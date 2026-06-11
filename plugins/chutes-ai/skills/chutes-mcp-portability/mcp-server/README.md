# chutes-mcp-server [BETA]

Stdio MCP server exposing Chutes.ai management + inference endpoints (models, quotas, aliases, usage, evidence, API keys, and gated write tools).

Local-path install (not on PyPI):

```bash
uv tool install chutes-mcp-server --from <repo>/plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

Self-check (no credentials sent, verifies tool registration):

```bash
chutes-mcp-server --self-check
```

Auth: reads `CHUTES_API_KEY` (or the toolkit keychain via `manage_credentials.py`) and sends it as `Authorization: Bearer cpk_...`. See the `chutes-mcp-portability` skill in this repo for client setup (Cursor / Cline / Claude Desktop / Aider).
