# Chutes in Cline (VS Code, MCP) **[BETA]**

## Install the server

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

## Generate the snippet

```bash
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py \
  --target cline --out ~/tmp/cline
```

The script writes `~/tmp/cline/cline-mcp-snippet.json`. Cline's MCP config is **not** VS Code `settings.json` — it lives in a global `cline_mcp_settings.json` under VS Code's globalStorage (`.../saoudrizwan.claude-dev/settings/`). Open it via Cline's **MCP Servers → Configure MCP Servers** UI and merge the snippet in:

```json
{
  "mcpServers": {
    "chutes": {
      "command": "chutes-mcp-server",
      "env": { "CHUTES_API_KEY": "${env:CHUTES_API_KEY}" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Per-server `disabled` and `autoApprove` fields are supported by Cline (per docs.cline.bot; config shape unverified end-to-end as of 2026-06-11).

## Set the env var

VS Code on macOS/Linux inherits env from the shell that launched it. If you start VS Code from an application launcher, your `~/.zshrc` / `~/.bashrc` export is the right place for `CHUTES_API_KEY`.

If you want the MCP server's management tools (`chutes_list_api_keys`, `chutes_get_quota`, etc.) to work, also ensure the credential store contains the account fingerprint or export `CHUTES_FINGERPRINT`.

On Windows, set the env var in System → Environment Variables and restart VS Code.

## Verify

Reload the Cline panel. Ask Cline to "list Chutes models with limit 1" — it should call `chutes_list_models` and return a model id.

## Troubleshooting

- **Env var not inherited** — relaunching VS Code from Finder on macOS skips `~/.zshrc`. Launch from a terminal (`code .`) or use `launchctl setenv` to propagate.
- **Write tools blocked** — any `[BETA]` write tool requires an account with deploy permissions.
