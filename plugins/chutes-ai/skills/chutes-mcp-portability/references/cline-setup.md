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

The script writes `~/tmp/cline/cline-mcp-snippet.json`. Paste its contents into VS Code's Cline settings under the "MCP Servers" section:

```json
{
  "mcp.servers": {
    "chutes": {
      "command": "chutes-mcp-server",
      "env": { "CHUTES_API_KEY": "${env:CHUTES_API_KEY}" }
    }
  }
}
```

## Set the env var

VS Code on macOS/Linux inherits env from the shell that launched it. If you start VS Code from an application launcher, your `~/.zshrc` / `~/.bashrc` export is the right place for `CHUTES_API_KEY`.

On Windows, set the env var in System → Environment Variables and restart VS Code.

## Verify

Reload the Cline panel. Ask Cline to "list Chutes models with limit 1" — it should call `chutes_list_models` and return a model id.

## Troubleshooting

- **Env var not inherited** — relaunching VS Code from Finder on macOS skips `~/.zshrc`. Launch from a terminal (`code .`) or use `launchctl setenv` to propagate.
- **Write tools blocked** — any `[BETA]` write tool requires an account with deploy permissions.
