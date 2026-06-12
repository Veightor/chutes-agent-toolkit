# Page draft: `chutes.ai/agents/claude` — "Chutes in Claude Code & Cowork"

> Status: draft copy for the Chutes site. Facts current as of the 2026-06-11 live verification pass in `chutes-agent-toolkit`; refresh model facts from `GET https://llm.chutes.ai/v1/models` before publication. This page is Claude-specific and links back to the implementation package in `chutes-agent-toolkit`.

---

## Hero

# Claude already knows Chutes.

Claude Code and Claude Cowork get the toolkit's deepest integration: a nine-skill plugin suite, OS-keychain credential storage, and a stdio MCP server. Claude can onboard you to Chutes end to end — including creating the account — and then call frontier open-source models (DeepSeek, Kimi, GLM, Qwen, MiniMax) through the OpenAI API, with the current hosted catalog running under `confidential_compute: true` inside TEEs.

Two commands, no config files:

```
/plugin marketplace add Veightor/chutes-agent-toolkit
/plugin install chutes-ai@chutes-agent-toolkit
```

**Primary CTA:** Get a Chutes key  
**Secondary CTA:** Open the agent toolkit on GitHub

---

## Why Claude users should care

### 1. Two commands install four product lanes

The plugin ships nine skills organized around four lanes: **Use Chutes** (account, keys, models, inference), **Build on Chutes** (Sign in with Chutes [BETA]), **Operate on Chutes** (usage, quotas, fleet ops, TEE attestation), and **Run agents with Chutes** (deploy [BETA], MCP portability, agent registration [BETA]). No YAML, no base-URL plumbing — Claude picks the right skill from a plain-English request.

### 2. Your key lives in the OS keychain, not the transcript

On first use, Claude runs `manage_credentials.py check`; if a profile exists it reads the key silently, so raw secrets never appear in the conversation. Storage is the macOS Keychain, the freedesktop Secret Service on Linux, or an AES-256-GCM encrypted-file fallback — and it persists across sessions and projects. Env vars (`CHUTES_API_KEY`) always override for CI/CD.

### 3. Claude Desktop gets the same toolkit as MCP tools

Prefer tools over skills? The same repo ships a stdio MCP server. Read tools (model list, quota, usage, aliases, chutes, discounts, API keys) are live-verified; write/deploy tools stay [BETA].

```bash
uv tool install chutes-mcp-server \
  --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server
```

### 4. Privacy is a default, not an add-on

The live model object exposes `confidential_compute`. Ask Claude to "prove my model runs in a TEE" and the `chutes-tee` skill fetches real Intel TDX quotes and NVIDIA GPU attestation evidence and parses them byte-level. Shape-only verification is the default verdict; do not claim cryptographic attestation unless the (optional, [BETA]) DCAP validation path actually ran and passed.

---

## 60-second setup

```
# 1. Inside Claude Code / Cowork
/plugin marketplace add Veightor/chutes-agent-toolkit
/plugin install chutes-ai@chutes-agent-toolkit

# 2. Then just ask:
"Set me up with a Chutes account and API key"
```

Claude registers the account, creates the `cpk_` key, and stores it in your OS keychain — the key is never pasted into chat. Already have a key? Ask Claude to save it, or check what's stored (no secrets are printed):

```bash
python plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py check
```

Prefer copying skills by hand instead of the marketplace?

```bash
cp -r plugins/chutes-ai/skills/* ~/.claude/skills/
```

---

## The nine skills

Render as cards; keep the status labels visible — they follow the repo's BETA policy (anything not live-verified keeps its label).

| Skill | What Claude can do with it | Status |
|---|---|---|
| `chutes-ai` | Hub: account, API keys, model discovery, OpenAI-compatible inference, routing basics | verified |
| `chutes-routing` | Failover pools, `:latency`/`:throughput` routing, TEE-only filters, stable model aliases | read paths verified live 2026-06-11 |
| `chutes-tee` | Fetch and parse TDX quotes + NVIDIA GPU attestation evidence for any chute | verified (shape-valid default; crypto pipeline [BETA]) |
| `chutes-usage-and-billing` | Spend, balance, quotas, burst caps, cost breakdowns (read-only) | verified live 2026-06-11 |
| `chutes-sign-in` | Add "Sign in with Chutes" (OAuth 2.0 + OIDC + PKCE) to a Next.js app | [BETA] |
| `chutes-platform-ops` | OAuth app audits, bulk secret rotation, alias governance, token hygiene | mixed; token scripts [BETA] |
| `chutes-deploy` | Deploy vLLM/diffusion/custom chutes, TEE via `tee=True` | [BETA] |
| `chutes-mcp-portability` | MCP server + drop-in configs for Cursor / Cline / Aider / Hermes / Claude Desktop | read tools verified; write tools [BETA] |
| `chutes-agent-registration` | Autonomous agent self-registration via Bittensor hotkey signature | [BETA] |

---

## Demo prompts for Claude

After install, these are good first-run prompts (the mapping below is live-verified):

| Say this | Claude uses |
|---|---|
| "Set me up with a Chutes account and API key" | `chutes-ai`, which registers, creates the key, stores it in your OS keychain (never pasted into chat) |
| "Which Chutes model for tool-calling under $1/M?" | live `/v1/models` + the model picker logic |
| "Build me a failover pool of the 3 cheapest vision models" | `chutes-routing`, which emits the routing string or saves an alias |
| "Prove my model runs in a TEE" | `chutes-tee`, which fetches and parses real TDX/GPU attestation evidence |
| "How much did I spend this week and am I near my quota?" | `chutes-usage-and-billing` |
| "Add Sign in with Chutes to my Next.js app" | `chutes-sign-in` [BETA] |
| "Make Chutes available in Cursor via MCP" | `chutes-mcp-portability` (write tools [BETA]) |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `200` from `/v1/models`, completions fail | `/v1/models` is public and did not validate your key | Validate against an authenticated endpoint; ask Claude to check the keychain profile |
| Requests hit anonymous rate limits (429) | Client sent `X-API-Key` — silently ignored on inference | Use `Authorization: Bearer` with the `cpk_` key, everywhere |
| `default:latency` / `default:throughput` rejected | Routing aliases need a pool configured once at chutes.ai/app → Model Routing | Configure the pool, or use a concrete model ID from `/v1/models` (zero setup) |
| Snippet's model ID stopped working | Model IDs churn with the catalog | Refresh from `GET https://llm.chutes.ai/v1/models` (public source of truth) |
| `chutes-mcp-server` not found | MCP server not installed in PATH | Run the `uv tool install ... --from .../mcp-server` command from this repo |

---

## Page sections for design

1. Hero with the two-command install block.
2. Four cards: Skills, Keychain, MCP, TEE.
3. Nine-skill grid with status badges (BETA labels must render).
4. "Say this → Claude uses" prompt table as an interactive strip.
5. Privacy/TEE explanation with a link to `/agents/private`.
6. Recipe cards linking to `/agents/claude/recipes`.
7. CTA: GitHub toolkit, endpoint guide, `/agents/connect` for other clients.

---

## Links

- Install guide: `README.md` → "Install for Claude (Code / Cowork)"
- Skill sources: `plugins/chutes-ai/skills/`
- Credential store: `docs/credential-store.md` + `plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py`
- MCP server: `plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server/`
- Universal endpoint guide: `docs/endpoint-guide.md`
- Runnable examples: `cookbook/`

---

## Build notes (not page copy)

- **Data sources:** skill names/statuses come from `plugins/chutes-ai/skills/*/SKILL.md` frontmatter and the README's "Still BETA" section; the prompt table is the verified table from `site/pages/connect-your-agent.md`; install commands from `README.md` "Install for Claude (Code / Cowork)".
- **Live-driven vs static:** any model count, price, or concrete model ID must render from `GET https://llm.chutes.ai/v1/models` (public) at build time — never bake into HTML. Skill list and BETA labels are static but must be re-synced from the repo on each plugin release (`plugins/chutes-ai/.claude-plugin/plugin.json` carries the version).
- **BETA labels are policy, not decoration:** `chutes-sign-in` [BETA], `chutes-deploy` [BETA], `chutes-agent-registration` [BETA], MCP write tools [BETA], platform-ops token scripts [BETA], TEE crypto pipeline [BETA]. A label is only removed by a repo commit referencing a recorded verification run — mirror the repo, don't editorialize.
- Never show a raw key; the placeholder convention is `cpk_...` and snippets should read from the keychain or `CHUTES_API_KEY`.
- Auth fact to preserve in any snippet review: Bearer everywhere; `X-API-Key` is silently ignored on inference (verified live 2026-06-11).
- The marketplace slug `Veightor/chutes-agent-toolkit` must track the repo's canonical org if it moves.
