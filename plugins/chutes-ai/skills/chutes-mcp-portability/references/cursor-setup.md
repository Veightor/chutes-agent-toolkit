# Chutes in Cursor **[BETA]**

There are two ways to use Chutes inside Cursor:

- **Option A — Chutes as your model provider** (chat/agent models, OpenAI-compatible). Easiest; all in Cursor's Settings UI. Covered by the video below.
- **Option B — Chutes MCP server** (tools like `chutes_list_models`, `chutes_get_quota`). For driving the Chutes API as agent tools.

---

## Option A — Use Chutes models in Cursor (OpenAI-compatible) **[BETA]**

> 📹 **Walkthrough (90s):** [How to use Chutes in Cursor](https://x.com/chutes_ai/status/2020924504583594312)
> _Silent screen recording from @chutes_ai — the steps below transcribe it._

Cursor lets you point its OpenAI provider at any OpenAI-compatible endpoint. Chutes serves one at `https://llm.chutes.ai/v1`, so you can run open-source models (DeepSeek, Kimi, Qwen, …) in Cursor's chat/agent.

### 1. Create a Chutes API key

1. Go to **[chutes.ai/app/api](https://chutes.ai/app/api)** → **API Keys**.
2. Click **Create API Key**, give it a name (e.g. `cursor - demo`), and click **Create**.
3. **Copy the key immediately** — it starts with `cpk_` and is shown only once ("You won't be able to see it again!").

### 2. Point Cursor at the Chutes endpoint

In Cursor, click the **settings (gear) icon → Models**, then expand **API Keys**:

1. Enable **Override OpenAI Base URL** and set it to:
   ```
   https://llm.chutes.ai/v1
   ```
   (This replaces the default `https://api.openai.com/v1`.)
2. Enable **OpenAI API Key** and paste your Chutes `cpk_…` key into that field.

### 3. Add a Chutes model

1. Find a model ID on **[chutes.ai](https://chutes.ai/app)** — open the model card and copy its full name, e.g. `moonshotai/Kimi-K2.5-TEE`.
2. In the **Add or search model** box, type the full model ID.
3. Cursor shows "No models available" → click **+ Add Custom Model**. The model appears in the list with its toggle enabled.

### 4. Select and test

1. In the agent/chat panel, open the model dropdown (**Switch Model**, `⌘/`) and pick your custom Chutes model.
2. Send a test message. You're now running on Chutes. 🎉

### Notes & caveats **[BETA]**

- The base-URL override applies to Cursor's **OpenAI** provider, so while it's on, OpenAI models route to Chutes instead. Toggle **Override OpenAI Base URL** off to go back to OpenAI.
- Use the **exact** model ID from the Chutes model card — custom models are not validated until first use, so a typo just fails at request time.
- Cursor's own features (Tab completion, Composer/Auto) may still use Cursor's built-in models; this path covers the chat/agent model you explicitly select.
- Pricing/quota is per your Chutes plan (the demo account shows a $3/month, 300 requests/day Base plan).

---

## Option B — Chutes MCP server **[BETA]**

### Install the server

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

`uv tool install` puts `chutes-mcp-server` on your PATH. The `--from <local path>` form is required — the package is not published on PyPI (404 verified 2026-06-11). If you hit "Readme file does not exist" on an older checkout, update: a 2026-06-11 fix added the `mcp-server/README.md` that `pyproject.toml` declares, which had broken every `--from` build.

### Generate the config

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

### Set the env var for your shell

```bash
export CHUTES_API_KEY=$(python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py get --field api_key)
```

If you want the MCP server's management tools (`chutes_list_api_keys`, `chutes_get_quota`, etc.) to work, also ensure the credential store contains the account fingerprint or export `CHUTES_FINGERPRINT`.

Do this in the shell profile (`~/.zshrc`, `~/.bashrc`) that Cursor inherits. Cursor reads `${env:CHUTES_API_KEY}` from the environment, not from `.env.local`.

### Restart Cursor

File → Restart Window (or kill and relaunch). Cursor discovers MCP servers at startup.

### Verify

In Cursor, open the MCP panel and expand the `chutes` server. You should see the tools from the MCP tool map. Call `chutes_list_models` with `limit=1`; it should return a model id.

### Troubleshooting

- **"Command not found: chutes-mcp-server"** — `uv tool` binaries live in `~/.local/bin`; make sure it's on PATH.
- **401 Unauthorized** — `CHUTES_API_KEY` is either empty or the wrong profile's key. Run `manage_credentials.py list-profiles` and `manage_credentials.py get --field api_key` to confirm.
- **Tools show up but one fails** — check `[BETA]` write tools specifically; they require an account with deploy permissions.
