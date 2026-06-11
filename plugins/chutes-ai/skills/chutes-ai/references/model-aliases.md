# Model Aliases — Reference

> Source of truth: `GET https://api.chutes.ai/model_aliases/`. Always query live for the current alias set.

## What an alias is

A **model alias** is a stable semantic handle that points at one Chutes model (or a routing pool). Instead of hardcoding a volatile model ID like `deepseek-ai/DeepSeek-V3.2-TEE`, you create an alias like `interactive-fast` and point your code at that. When a better model lands, you repoint the alias — no code change. (Case in point: the entire non-TEE catalog was removed between April and June 2026 — every hardcoded non-TEE ID broke, every alias just needed a repoint.)

Aliases are a team-level operational primitive. They encode policy ("our fast lane = X") in one place.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/model_aliases/` | List all aliases (yours + public) |
| `POST` | `/model_aliases/` | Create an alias (body: `{ "alias": "...", "chute_ids": ["<chute_uuid>", ...] }` — the openapi `ModelAliasCreate` schema requires `chute_ids`, verified 2026-06-11; there is no `model` field) |
| `DELETE` | `/model_aliases/{alias}` | Remove an alias |

Bearer auth against `api.chutes.ai`, same `cpk_` key (GET verified live 2026-06-11).

## Recommended alias packs

Pick one or two packs when onboarding a team. Each alias maps to a category, not a specific model, so they stay meaningful across model churn.

### Interactive / chat pack
| Alias | Intent | Example target |
|---|---|---|
| `interactive-fast` | Lowest TTFT, cheap | `google/gemma-4-31B-turbo-TEE` or a `default:latency` pool |
| `interactive-rich` | Balanced quality + speed for chat UIs | `zai-org/GLM-5-TEE` or `moonshotai/Kimi-K2.5-TEE` |
| `interactive-long` | Long-context interactive (262k) | `Qwen/Qwen3.5-397B-A17B-TEE` |

### Private / confidential pack
| Alias | Intent | Example target |
|---|---|---|
| `private-reasoning` | TEE reasoning for sensitive workflows | `zai-org/GLM-5.1-TEE` |
| `private-chat` | TEE chat | `deepseek-ai/DeepSeek-V3.2-TEE` |
| `tee-chat` | Alias form of the above, easier to remember | Same |

Note: as of 2026-06-11 every hosted LLM is `confidential_compute: true`, so the "private" pack currently equals the whole catalog — it stays useful as a guarantee if non-TEE serving ever returns.

### Batch / cost pack
| Alias | Intent | Example target |
|---|---|---|
| `cheap-background` | Lowest-cost model for non-interactive work | `unsloth/Mistral-Nemo-Instruct-2407-TEE` (cheapest as of 2026-06-11) |
| `batch-high-throughput` | Max TPS for bulk summarization | `default:throughput` over a custom pool |

### Agent / tool-use pack
| Alias | Intent | Example target |
|---|---|---|
| `agent-coder` | Tool-calling code model | `moonshotai/Kimi-K2.6-TEE`; budget: `MiniMaxAI/MiniMax-M2.5-TEE` |
| `agent-reasoner` | Reasoning + tool use | `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE` |

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
