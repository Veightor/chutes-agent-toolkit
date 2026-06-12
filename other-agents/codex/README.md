# Codex + Chutes

Use Chutes as the OpenAI-compatible inference backend for Codex-style coding agents.

Status: the Chutes endpoint behavior in this guide was verified by this repo's 2026-06-11 refresh. Codex provider surfaces vary by runtime. This guide does not claim that every upstream Codex build ships a built-in Chutes provider; it documents the Chutes setup pattern for Codex-style agents and tools that accept an OpenAI-compatible base URL, Bearer API key, and model value.

## Endpoint Facts

| Setting | Value |
|---|---|
| Inference base URL | `https://llm.chutes.ai/v1` |
| Auth | `Authorization: Bearer $CHUTES_API_KEY` |
| Model source of truth | `https://llm.chutes.ai/v1/models` |
| Useful routing aliases | `default`, `default:latency`, `default:throughput` |
| Account and usage host | `https://api.chutes.ai` |

Use `CHUTES_API_KEY` as the local secret name. Do not paste API keys into agent prompts, committed config, demo transcripts, or issue comments.

## Setup Pattern

Set Chutes credentials in the shell or agent runtime:

```bash
export CHUTES_API_KEY="<store-this-in-your-secret-manager>"
```

For clients that read OpenAI-compatible environment variables, map Chutes into the process environment:

```bash
export OPENAI_BASE_URL="https://llm.chutes.ai/v1"
export OPENAI_API_KEY="$CHUTES_API_KEY"
```

For config-driven agents, use this shape:

```json
{
  "provider": "openai-compatible",
  "base_url": "https://llm.chutes.ai/v1",
  "api_key_env": "CHUTES_API_KEY",
  "model": "default:latency"
}
```

If your Codex runtime does not expose custom provider configuration, keep Chutes in a sidecar tool, SDK-backed task runner, MCP server, or repo-local script until that runtime offers a supported provider surface.

## Smoke Test

This verifies the endpoint shape without reading credentials from files:

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key=os.environ["CHUTES_API_KEY"],
)

response = client.chat.completions.create(
    model="default:latency",
    messages=[
        {
            "role": "user",
            "content": "Reply with one short sentence confirming Chutes is configured.",
        }
    ],
)
print(response.choices[0].message.content)
```

`GET https://llm.chutes.ai/v1/models` is public, so a successful model-list call does not prove the key works. Validate credentials with an authenticated completion or a management read such as `GET https://api.chutes.ai/users/me`.

## Recommended Presets

| Codex-style task | Model value | Why |
|---|---|---|
| Interactive coding | `default:latency` | Optimizes for fastest first token and failover during edit-test loops. |
| Code review | Live model ID with `tools`, `json_mode`, and `reasoning`, or `default:latency` | Use current `/v1/models` metadata when you need explicit capabilities. |
| Planning and architecture | Long-context live model ID with `reasoning` | Context windows and reasoning support change, so query the catalog before recommending a named model. |
| Background docs, summaries, and lint triage | Cheapest suitable live model ID, or `default:throughput` for bulk work | Keeps non-interactive work cost-aware without blocking on one static model. |
| Private or sensitive workflows | Any live model with `confidential_compute: true` | As of 2026-06-11, the hosted LLM catalog is currently all TEE-backed, but the boolean remains the source of truth. |

Avoid hardcoding dated model claims in Codex prompts. Use:

```bash
curl https://llm.chutes.ai/v1/models
```

Then choose from the returned `id`, `pricing`, `context_length`, `input_modalities`, `supported_features`, `supported_sampling_parameters`, and `confidential_compute` fields.

## Demo Prompts

Repository repair:

```text
Audit this repository for the smallest failing test path, patch the bug, and rerun only the relevant test command. Use Chutes through CHUTES_API_KEY and do not print secrets.
```

Review:

```text
Review this diff for correctness risks, missing tests, and stale model assumptions. Ground any Chutes model recommendation in /v1/models.
```

Planning:

```text
Plan a migration from one hardcoded model ID to Chutes routing aliases for interactive coding, code review, and background tasks.
```

TEE-safe copy:

```text
Rewrite this agent landing-page copy so it explains confidential_compute benefits without claiming cryptographic attestation unless DCAP verification ran.
```

## Secure Credential Handling

- Keep the raw API key in a local secret manager, CI secret, or process environment.
- Prefer `CHUTES_API_KEY` as the durable name, then map to `OPENAI_API_KEY` only inside tools that require the OpenAI variable name.
- Do not commit generated configs with literal keys.
- Do not include credential-looking examples in docs. Use `$CHUTES_API_KEY` or redacted placeholders.
- When using this repo's Chutes skills, use `plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py` for keychain-backed storage.

## Limitations

- Chutes is OpenAI-compatible, but not every Codex runtime exposes the same provider knobs.
- Provider-mode setup for a specific Codex build should be verified against that installed build before publishing as first-class support.
- Routing aliases are convenient defaults; use concrete live model IDs when a task requires a specific context window, modality, tool support, or price.
- TEE status should be read from `confidential_compute`, not inferred from the model name.
- Do not claim cryptographic attestation unless the `chutes-tee` verification path actually ran with the required tooling.

## Verification Status

- Chutes Bearer auth on inference and management hosts: live-verified 2026-06-11.
- Public `/v1/models` catalog: live-verified 2026-06-11.
- Paid `POST /v1/chat/completions` with Bearer auth: live-verified 2026-06-11 in the repo refresh notes.
- Codex-specific built-in provider support: not claimed by this repo.
- This guide performs no live Chutes writes, paid deploy calls, or credential reads.

## Related

- `docs/endpoint-guide.md`
- `docs/site-agent-growth-kit.md`
- `data/agent-use-cases.json`
- `other-agents/openai-compatible/README.md`
- `plugins/chutes-ai/skills/chutes-mcp-portability/SKILL.md`
