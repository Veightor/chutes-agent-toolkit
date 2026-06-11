# Chutes in Cursor (MCP) **[BETA]**

## Install the server

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

`uv tool install` puts `chutes-mcp-server` on your PATH.

## Generate the config

From the repo root:

```bash
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py \
  --target cursor --out /path/to/your/workspace
```

This writes `.cursor/mcp.json` at the workspace root:

```json
{
  "mcpServers": {
    "chutes": {
      "command": "chutes-mcp-server",
      "env": { "CHUTES_API_KEY": "${env:CHUTES_API_KEY}" }
    }
  }
}
```

## Set the env var for your shell

```bash
export CHUTES_API_KEY=$(python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py get --field api_key)
```

If you want the MCP server's management tools (`chutes_list_api_keys`, `chutes_get_quota`, etc.) to work, also ensure the credential store contains the account fingerprint or export `CHUTES_FINGERPRINT`.

Do this in the shell profile (`~/.zshrc`, `~/.bashrc`) that Cursor inherits. Cursor reads `${env:CHUTES_API_KEY}` from the environment, not from `.env.local`.

## Restart Cursor

File → Restart Window (or kill and relaunch). Cursor discovers MCP servers at startup.

## Verify

In Cursor, open the MCP panel and expand the `chutes` server. You should see the tools from the MCP tool map. Call `chutes_list_models` with `limit=1`; it should return a model id.

## Troubleshooting

- **"Command not found: chutes-mcp-server"** — `uv tool` binaries live in `~/.local/bin`; make sure it's on PATH.
- **401 Unauthorized** — `CHUTES_API_KEY` is either empty or the wrong profile's key. Run `manage_credentials.py list-profiles` and `manage_credentials.py get --field api_key` to confirm.
- **Tools show up but one fails** — check `[BETA]` write tools specifically; they require an account with deploy permissions.
