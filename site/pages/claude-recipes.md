# Page draft: `chutes.ai/agents/claude/recipes` — "Claude + Chutes recipes"

> Status: draft copy for the Chutes site. Use as cards, accordions, or short docs beneath the Claude landing page. Keep deep implementation details in the GitHub toolkit; every recipe below is backed by a file in `chutes-agent-toolkit`.

---

## Intro

# Recipes for running Claude on Chutes

Use these when you want more than "install the plugin": keychain-backed onboarding, project-level defaults, MCP tools in Claude Desktop, routing pools, TEE evidence, and porting your setup to other editors.

Each recipe follows the same rules: Chutes is OpenAI-compatible at `https://llm.chutes.ai/v1`, auth is `Authorization: Bearer` with a `cpk_` key (never `X-API-Key`), and the public `GET /v1/models` list is the source of truth for model IDs.

---

## Recipe 1: Install the plugin in two commands

**Use when:** You want the full nine-skill suite in Claude Code or Claude Cowork.

```
/plugin marketplace add Veightor/chutes-agent-toolkit
/plugin install chutes-ai@chutes-agent-toolkit
```

**Verify:** ask *"What open-source models are available on Chutes?"* — Claude should answer from the live `/v1/models` catalog via the `chutes-ai` hub skill.

**No marketplace?** Copy the skills directly:

```bash
cp -r plugins/chutes-ai/skills/* ~/.claude/skills/
```

---

## Recipe 2: Let Claude onboard you end to end

**Use when:** You don't have a Chutes account or key yet.

Say:

> "Set me up with a Chutes account and API key"

The `chutes-ai` hub skill registers the account, creates the `cpk_` key, and stores it in your OS keychain via `manage_credentials.py` — the raw key is never pasted into chat. In later sessions, skills run `manage_credentials.py check` first and read the key silently.

**Caveat:** the registration fingerprint is the master credential, shown once — back it up when Claude tells you to.

---

## Recipe 3: Check and use the keychain credential store

**Use when:** You want to confirm what's stored, or use the key in a shell without echoing it.

```bash
# Status check — backend, profiles, permissions; prints no secrets
python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py check

# Export for a script without echoing the secret
export CHUTES_API_KEY="$(python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py get --field api_key)"
```

Backends auto-detect: macOS Keychain → Linux Secret Service → AES-256-GCM encrypted-file fallback. Env vars (`CHUTES_API_KEY`, `CHUTES_PROFILE`, …) always override stored values for CI/CD. Full reference: `docs/credential-store.md`.

---

## Recipe 4: Make any project Chutes-native with CLAUDE.md

**Use when:** A project should know the Chutes rules in every session, with or without the plugin.

Drop this into the project's `CLAUDE.md`:

```markdown
## Chutes inference
- Base URL `https://llm.chutes.ai/v1` (OpenAI-compatible), auth `Authorization: Bearer $CHUTES_API_KEY`.
- Never send `X-API-Key`; it is silently ignored on inference.
- Never hardcode model IDs: discover via `GET https://llm.chutes.ai/v1/models` (public) and
  check `supported_features` / `pricing` before choosing.
- For resilience pass a pool: `model="<id1>,<id2>,<id3>"` (append `:latency` or `:throughput`).
```

---

## Recipe 5: Drive Chutes by asking, not configuring

**Use when:** You want routing, attestation, or billing answers without touching a config file.

| Say this | Claude uses |
|---|---|
| "Which Chutes model for tool-calling under $1/M?" | live `/v1/models` + the model picker logic |
| "Build me a failover pool of the 3 cheapest vision models" | `chutes-routing`, which emits the routing string or saves an alias |
| "Prove my model runs in a TEE" | `chutes-tee`, which fetches and parses real TDX/GPU attestation evidence |
| "How much did I spend this week and am I near my quota?" | `chutes-usage-and-billing` |
| "Add Sign in with Chutes to my Next.js app" | `chutes-sign-in` [BETA] |

**Caveat:** `chutes-tee` ships with shape-only verification as the default verdict; cryptographic validation is optional tooling [BETA]. Claude will state the verification level rather than overclaim.

---

## Recipe 6: Add Chutes tools to Claude Desktop via MCP

**Use when:** You want Chutes as MCP tools (Claude Desktop or any MCP client) instead of skills.

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

**What this unlocks:** verified read tools — model listing, quota, usage, aliases, chute listing, discounts, API key reads. Write/deploy tools (`chutes_deploy_vllm`, `chutes_set_alias`, `chutes_create_api_key`, …) stay [BETA]; their tool descriptions are prefixed `[BETA]` so clients display it. Keep those labels visible.

---

## Recipe 7: Port your Chutes setup to other editors

**Use when:** You've set things up with Claude and want the same backend in Cursor, Cline, or Aider.

```bash
python plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py \
  --target cursor,cline,aider
```

Emits drop-in config snippets per client (also accepts `hermes` and `system-prompt` targets). Or just ask: *"Make Chutes available in Cursor via MCP"* — the `chutes-mcp-portability` skill handles it (write tools [BETA]).

---

## Recipe 8: Pick a model from live metadata

**Use when:** A snippet needs a concrete model ID for tools, JSON, vision, or long context.

1. Need latest availability? `GET https://llm.chutes.ai/v1/models` (public, no key).
2. Need tools or JSON? Prefer models whose `supported_features` advertises them; verify critical paths with a minimal request.
3. Need private? Require `confidential_compute: true` (currently the whole hosted catalog).
4. Need cheap loops or broad context? Sort by `pricing` or `context_length`.

**Local helper:**

```bash
python scripts/pick_model.py --task agentic --routing latency
```

Example IDs like `deepseek-ai/DeepSeek-V3.2-TEE` in snippets are examples only — IDs churn; the live list is the source of truth. `default:latency` / `default:throughput` aliases require a pool configured once at chutes.ai/app → Model Routing; concrete IDs work with zero setup.

---

## Troubleshooting card

| Symptom | Likely cause | Fix |
|---|---|---|
| `200` from `/v1/models`, completions fail | `/v1/models` is public and did not validate your key | Validate against an authenticated endpoint; re-check the keychain profile with `manage_credentials.py check` |
| Anonymous 429 rate limits despite a key | Client sent `X-API-Key`, which is silently ignored on inference | Use `Authorization: Bearer cpk_...` everywhere |
| `default:latency` rejected | No routing pool configured | Set one up once at chutes.ai/app → Model Routing, or use a concrete ID from `/v1/models` |
| Stale model ID in an old snippet | Catalog churn | Refresh from `GET https://llm.chutes.ai/v1/models` |
| `chutes-mcp-server` not found | Not installed in PATH | Run the `uv tool install ... --from .../mcp-server` command from this repo |
| Key showed up in a shell command | Bypassed the credential store | Use the Recipe 3 export pattern; secrets are never passed as command-line arguments |

---

## Which lane do I want?

- **Claude Code / Cowork, full power** → Recipe 1 (plugin). Skills cover all four product lanes and use the keychain.
- **Claude Desktop, or another MCP client** → Recipe 6 (MCP server). Read tools verified; writes [BETA].
- **A single project, minimal footprint** → Recipe 4 (CLAUDE.md block). No plugin, just the rules.
- **Leaving for another editor** → Recipe 7 (config generator).

---

## Build notes (not page copy)

- **Data sources:** install commands and skill statuses from `README.md`; the prompt table is the verified table in `site/pages/connect-your-agent.md`; the CLAUDE.md block is the same one published there — keep the two pages byte-identical or single-source it in the CMS; credential CLI from `README.md` "Secure credential store" + `docs/credential-store.md`; runnable snippets trace to `cookbook/README.md` (all examples live-verified 2026-06-11).
- **Live-driven vs static:** model IDs, counts, and prices must render from `GET https://llm.chutes.ai/v1/models`; recipes' command text is static but must track these source-of-truth files: `plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py`, `plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py`, `plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server/`, `scripts/pick_model.py`.
- **BETA labels:** keep `chutes-sign-in` [BETA], MCP write tools [BETA], and the TEE cryptographic pipeline [BETA] exactly as the repo carries them; labels graduate only via a repo commit referencing a verification run.
- Never render a raw key; the placeholder is `cpk_...` and recipes read from the keychain or `CHUTES_API_KEY`.
- Turn each recipe into a card with a "copy" button and a "deep guide" link into the GitHub toolkit.
