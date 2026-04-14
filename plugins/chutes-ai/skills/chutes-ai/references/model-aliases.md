# Model Aliases — Reference

> Source of truth: `GET https://api.chutes.ai/model_aliases/`. Always query live for the current alias set.

## What an alias is

A **model alias** is a stable semantic handle that points at one Chutes model (or a routing pool). Instead of hardcoding a volatile model ID like `deepseek-ai/DeepSeek-V3-0324`, you create an alias like `interactive-fast` and point your code at that. When a better model lands, you repoint the alias — no code change.

Aliases are a team-level operational primitive. They encode policy ("our fast lane = X") in one place.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/model_aliases/` | List all aliases (yours + public) |
| `POST` | `/model_aliases/` | Create an alias (body: `{ "alias": "...", "model": "..." }`) |
| `DELETE` | `/model_aliases/{alias}` | Remove an alias |

Bearer auth against `api.chutes.ai`, same `cpk_` key.

## Recommended alias packs

Pick one or two packs when onboarding a team. Each alias maps to a category, not a specific model, so they stay meaningful across model churn.

### Interactive / chat pack
| Alias | Intent | Example target |
|---|---|---|
| `interactive-fast` | Lowest TTFT, small context | Qwen/Qwen3-8B or a `default:latency` pool |
| `interactive-rich` | Balanced quality + speed for chat UIs | DeepSeek-V3 |
| `interactive-long` | Long-context interactive | Qwen3-Long or GLM long-context |

### Private / confidential pack
| Alias | Intent | Example target |
|---|---|---|
| `private-reasoning` | TEE reasoning for sensitive workflows | A `confidential_compute: true` reasoning model |
| `private-chat` | TEE chat | TEE-variant of DeepSeek-V3 |
| `tee-chat` | Alias form of the above, easier to remember | Same |

### Batch / cost pack
| Alias | Intent | Example target |
|---|---|---|
| `cheap-background` | Lowest-cost model for non-interactive work | Pick the current cheapest in `/v1/models` |
| `batch-high-throughput` | Max TPS for bulk summarization | `default:throughput` over a custom pool |

### Agent / tool-use pack
| Alias | Intent | Example target |
|---|---|---|
| `agent-coder` | Tool-calling code model | A code model with `"tools"` in `supported_features` |
| `agent-reasoner` | Reasoning + tool use | DeepSeek-R1 variant |

## Why aliases beat hardcoded IDs

- **Model churn is constant.** New checkpoints and quantizations land on Chutes every week. Hardcoded IDs rot.
- **Policy in one place.** "Switch all our background jobs to a cheaper model" = one alias repoint, not a grep-and-sweep.
- **Agent ergonomics.** Agents get stable, human-meaningful handles they can reason about.
- **Failover pairing.** Aliases compose naturally with `default:latency` / `default:throughput` pools and inline comma-separated routing strings.
- **Team conventions.** Alias packs become a shared vocabulary across the company or across multiple agents.

## Lifecycle notes

- Aliases are scoped to your account by default. List calls return yours + any public ones.
- Renaming is not supported; delete + recreate. Do this in a blue/green switch to avoid gaps.
- An alias pointing at a removed model will start returning an error — treat aliases as pointers that need occasional repair.

## Related skills

- **Create aliases during deploy:** `chutes-deploy` → `alias_deploy.py` **[BETA]**
- **Alias packs / routing recipes:** `chutes-routing` (wave 2 stub)
- **Alias CRUD as an operator flow:** `chutes-platform-ops` (wave 2 stub)
- **Alias list/set/delete from any MCP client:** `chutes-mcp-portability` **[BETA]** → `chutes_list_aliases`, `chutes_set_alias`, `chutes_delete_alias`
