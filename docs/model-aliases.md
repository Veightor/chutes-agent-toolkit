# Model Aliases on Chutes

> **Status: BETA** — the alias skill walkthrough is wave-2 (`chutes-routing`). Today aliases are exposed through `chutes-deploy` (`alias_deploy.py`), the `chutes-mcp-portability` MCP server (`chutes_list_aliases`, `chutes_set_alias`, `chutes_delete_alias`), and this doc. The skill reference at `plugins/chutes-ai/skills/chutes-ai/references/model-aliases.md` is the source of truth.

## Why aliases

A **model alias** is a stable semantic handle that points at a Chutes model or routing pool. Instead of hardcoding `deepseek-ai/DeepSeek-V3-0324` across your team, you define `interactive-fast` once and repoint it when a better model lands. Code does not change.

Aliases encode policy ("our fast lane = X") in one place, which is the single most useful operational primitive Chutes offers.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/model_aliases/` | List aliases (yours + any public ones) |
| `POST` | `/model_aliases/` | Create an alias (`{"alias": "...", "model": "..."}`) |
| `DELETE` | `/model_aliases/{alias}` | Remove an alias |

Bearer auth with `cpk_`, same as the rest of `api.chutes.ai`.

## Recommended alias packs

Pick one or two packs when onboarding a team. Each alias names a category, not a specific model, so they survive model churn.

### Interactive / chat pack
| Alias | Intent |
|---|---|
| `interactive-fast` | Lowest TTFT, small context |
| `interactive-rich` | Balanced quality + speed for chat UIs |
| `interactive-long` | Long-context interactive |

### Private / confidential pack
| Alias | Intent |
|---|---|
| `private-reasoning` | TEE reasoning for sensitive workflows |
| `private-chat` | TEE chat (a.k.a. `tee-chat`) |
| `tee-chat` | Convenient shorthand for the above |

### Batch / cost pack
| Alias | Intent |
|---|---|
| `cheap-background` | Lowest-cost model for non-interactive work |
| `batch-high-throughput` | Max TPS for bulk summarization |

### Agent / tool-use pack
| Alias | Intent |
|---|---|
| `agent-coder` | Tool-calling code model |
| `agent-reasoner` | Reasoning + tool use |

## Creating aliases

From the command line, during deploy:

```bash
python plugins/chutes-ai/skills/chutes-deploy/scripts/deploy_vllm.py \
  --model Qwen/Qwen3-8B --gpu h100 --alias interactive-fast
```

Or standalone:

```bash
python plugins/chutes-ai/skills/chutes-deploy/scripts/alias_deploy.py \
  --alias interactive-fast --model myuser/qwen3-8b
```

Or from any MCP client via `chutes_set_alias` (a **[BETA]** write tool).

## Using aliases in inference calls

Aliases slot straight into the OpenAI-compatible `model` parameter:

```python
client.chat.completions.create(
    model="interactive-fast",
    messages=[...],
)
```

They compose naturally with routing strategies — append `:latency` or `:throughput` to an alias-resolved pool, or use an alias as one entry in a comma-separated inline routing string.

## Lifecycle notes

- Aliases are scoped to your account by default. List calls return yours plus any public aliases.
- Renaming is not supported: delete + recreate. Do this in a blue/green switch so callers don't hit a gap.
- An alias pointing at a removed model starts returning errors — aliases are pointers that sometimes need repair.

## Why this matters more than it looks

Chutes ships new checkpoints weekly. Hardcoded model ids rot. Aliases give:

- **Policy in one place** — "switch all background jobs to a cheaper model" is one alias repoint, not a grep sweep.
- **Agent ergonomics** — agents get stable, human-meaningful handles they can reason about.
- **Failover pairing** — aliases compose naturally with `default:latency` / `default:throughput` pools.
- **Team conventions** — alias packs become a shared vocabulary across many agents.

## Related

- `plugins/chutes-ai/skills/chutes-ai/references/model-aliases.md` (source)
- `plugins/chutes-ai/skills/chutes-deploy/scripts/alias_deploy.py`
- `plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server/server.py` (`chutes_set_alias`)
- `plugins/chutes-ai/skills/chutes-routing/SKILL.md` (wave-2 stub — full routing recipes)
