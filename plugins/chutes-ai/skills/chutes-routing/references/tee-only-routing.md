# TEE-Only Routing Recipe

> Build a routing pool that only runs inference inside Intel TDX + NVIDIA H100 confidential-compute chutes.

## What TEE-only routing is

Hardware isolation via Intel TDX + GPU confidential compute. The host kernel, hypervisor, and even Chutes operators cannot read prompts or responses. Attestation evidence is available at `GET /chutes/{chute_id}/evidence`; **deep verification of that evidence is wave-2 `chutes-tee` skill work**, not this skill.

The honest caveat: **TEE-only routing without attestation verification is "Chutes says this chute runs in TEE."** That's usually true, but it's a server-side assertion, not a cryptographic proof. For regulated use cases, pair this recipe with `chutes-tee` attestation before trusting it.

## The recipe

```bash
python plugins/chutes-ai/skills/chutes-routing/scripts/build_pool.py \
  --intent tee-chat \
  --size 4 \
  --alias tee-chat
```

`build_pool.py` with `--intent tee-chat` filters `/v1/models` for `confidential_compute=true` and text I/O, ranks by cost, picks the top N, and creates a stable alias.

## What you get

Wave-2 live probe showed **16 models with `confidential_compute=true`** out of 36 total — roughly half the catalog is TEE-backed. That's enough for a diverse pool. Expect names ending in `-TEE`, but do **not** rely on the suffix — `confidential_compute` on the JSON object is the source of truth.

## Strategy

Pair `tee-chat` with `:latency`:

```python
response = client.chat.completions.create(
    model="tee-chat:latency",
    messages=[...],
)
```

Chutes re-ranks TEE members by live TTFT each request. Failover stays within the TEE set.

## Hard-mode: verify every chute

Before a sensitive request, fetch evidence for each chute_id in the alias:

```bash
CHUTES_API_KEY=$(python manage_credentials.py get --field api_key)
for chute_id in $(curl -s -H "Authorization: Bearer $CHUTES_API_KEY" \
                    https://api.chutes.ai/model_aliases/ | \
                    python3 -c "import sys, json; [print(c) for a in json.load(sys.stdin) if a['alias']=='tee-chat' for c in a['chute_ids']]"); do
  curl -s -H "Authorization: Bearer $CHUTES_API_KEY" \
    "https://api.chutes.ai/chutes/$chute_id/evidence" > "/tmp/evidence-$chute_id.json"
done
```

Deep quote/chain validation is the `chutes-tee` skill's job. Wave 2's version of this flow ships as `chutes-tee` — this recipe only surfaces the raw evidence endpoint.

## Pool hygiene

- **Monthly audit.** `audit_pool.py --alias tee-chat` warns if a member's `confidential_compute` flag flipped (unlikely but possible across model renames).
- **Don't mix TEE and non-TEE in the same alias.** The whole point is that every member is hardware-isolated. One non-TEE member breaks the guarantee for the whole alias.
- **Beware price drift.** TEE chutes often run on more expensive hardware (H100 with confidential compute mode enabled). Expect `pricing.prompt` to be 2-5× higher than the non-TEE equivalent. Re-check against your budget after each audit.

## When TEE-only is the wrong answer

- **High-throughput batch jobs with non-sensitive data.** TEE hardware is scarcer and pricier. `cheap-background` on non-TEE is usually the right answer.
- **Tool-calling agents with no user PII.** `agent-coder` is usually enough; TEE adds cost without adding value.
- **Experimentation and prototyping.** Start on non-TEE, move to `tee-chat` when you actually handle sensitive data.

The rule: TEE when the data class demands it, not by default.
