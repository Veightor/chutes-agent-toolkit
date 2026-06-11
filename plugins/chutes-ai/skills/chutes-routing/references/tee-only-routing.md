# TEE-Only Routing Recipe

> Build a routing pool that only runs inference inside Intel TDX + NVIDIA confidential-compute chutes.

> **2026-06-11 update:** the hosted gateway is now **entirely TEE** — all 13 models on `/v1/models` carry `confidential_compute: true`. TEE-only routing on the hosted catalog is therefore the default, not a subset choice. This recipe still matters for (a) stating intent explicitly, (b) self-deployed chutes (where `tee=True` is opt-in), and (c) future-proofing if a non-TEE tier returns.

## What TEE-only routing is

Hardware isolation via Intel TDX + GPU confidential compute (live attestation evidence shows `arch: "BLACKWELL"` GPU reports as of 2026-06-11; the platform also uses NVIDIA Protected PCIe for the CPU-GPU channel). The host kernel, hypervisor, and even Chutes operators cannot read prompts or responses. Attestation evidence is available at `GET /chutes/{chute_id_or_name}/evidence` (requires a `nonce` query param of exactly 64 hex chars); **deep verification of that evidence is the `chutes-tee` skill's job**, not this skill's.

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

Live probe 2026-06-11: **13 models, all with `confidential_compute=true`** — the whole hosted catalog is TEE-backed (the April 2026 snapshot of 16-of-36 is obsolete; the non-TEE tier was removed). Expect names ending in `-TEE`, but do **not** rely on the suffix — `confidential_compute` on the JSON object is the source of truth (Chutes' own ai-plugin.json says the same).

Current cheapest TEE pool (live `build_pool.py --intent tee-chat` output, 2026-06-11): `Qwen/Qwen3-32B-TEE`, `google/gemma-4-31B-turbo-TEE`, `MiniMaxAI/MiniMax-M2.5-TEE`, `Qwen/Qwen3-235B-A22B-Thinking-2507-TEE`.

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

Before a sensitive request, fetch evidence for each chute_id in the alias. The endpoint **requires a fresh `nonce` query param of exactly 64 hex characters (32 bytes)** — omitting it is a 4xx (`$.query.nonce: required parameter missing`); wrong length gets `Nonce must be exactly 64 hex characters (32 bytes)`. Verified live 2026-06-11.

```bash
CHUTES_API_KEY=$(python manage_credentials.py get --field api_key)
for chute_id in $(curl -s -H "Authorization: Bearer $CHUTES_API_KEY" \
                    https://api.chutes.ai/model_aliases/ | \
                    python3 -c "import sys, json; [print(c) for a in json.load(sys.stdin) if a['alias']=='tee-chat' for c in a['chute_ids']]"); do
  NONCE=$(openssl rand -hex 32)
  curl -s -H "Authorization: Bearer $CHUTES_API_KEY" \
    "https://api.chutes.ai/chutes/$chute_id/evidence?nonce=$NONCE" > "/tmp/evidence-$chute_id.json"
done
```

The response is `{evidence: [{quote, gpu_evidence: [...], instance_id, certificate}, ...], failed_instance_ids: [...]}` — one entry per live instance. Deep quote/chain validation is the `chutes-tee` skill's job (shipped in wave 2) — this recipe only surfaces the raw evidence endpoint. Per-instance evidence also exists at `GET /instances/{instance_id}/evidence`.

## Pool hygiene

- **Monthly audit.** `audit_pool.py --alias tee-chat` warns if a member's `confidential_compute` flag flipped (unlikely but possible across model renames). It also catches removed models — catalog churn is real: a live audit of this account's `default` alias on 2026-06-11 found 3 of 4 pinned chute_ids no longer on `/v1/models`.
- **Don't mix TEE and non-TEE in the same alias.** The whole point is that every member is hardware-isolated. One non-TEE member breaks the guarantee for the whole alias. (Currently moot on the hosted gateway — everything is TEE — but it matters when aliases include self-deployed chutes.)
- **Beware price drift.** Chutes reprices as checkpoints churn. Re-check against your budget after each audit. (The old guidance that TEE costs 2-5× a non-TEE equivalent no longer applies — there is no non-TEE tier to compare against as of 2026-06-11.)

## When TEE-only is the wrong answer

As of 2026-06-11 the hosted gateway is all-TEE, so on Chutes-hosted models you get TEE semantics whether you ask for them or not — `tee-chat` vs `cheap-background` now differ only by ranking, not by isolation. The distinction still matters when:

- **Your pool includes self-deployed chutes.** SDK deploys default to `tee=False`; only `tee=True` deployments are hardware-isolated.
- **You need attestation, not just the flag.** For regulated data, the flag filter is necessary but not sufficient — pair with `chutes-tee` verification.

The rule stands: demand *verified* TEE when the data class requires it; rely on the flag alone only for best-effort privacy.
