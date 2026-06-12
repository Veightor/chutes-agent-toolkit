# Page draft: `chutes.ai/agents/private` — "Private inference, provable"

> Status: draft copy, ready for design. Technical claims trace to the 2026-06-11 live attestation run in [chutes-agent-toolkit](https://github.com/Veightor/chutes-agent-toolkit) (`chutes-tee` skill). Keep the honesty framing; it is the differentiator. Horizontal rules mark page-section boundaries for the designer.

---

# Your prompts are sealed in hardware. Here's the receipt.

Every model hosted on Chutes runs inside a Trusted Execution Environment: Intel TDX enclaves with attested GPUs. That is the whole catalog, with no premium tier. Node operators cannot read your agent's traffic, and neither can we. You can verify this yourself, from a public endpoint, right now.

---

## What a TEE buys your agent

Agents handle the stuff people won't paste into a chatbox: codebases, contracts, medical notes, financial records. On Chutes, prompts and completions are processed inside hardware enclaves where memory is encrypted at the silicon level, invisible to the host OS, the hypervisor, and whoever operates the GPU node.

This matters more on a decentralized network, where you have no idea who runs the box. The security model doesn't ask you to trust them, because the box can prove what it's running.

Routing pools can be confidential by construction: filter on `confidential_compute: true` in `/v1/models` and today you'll match every model in the catalog.

---

## Don't trust us. Fetch the evidence.

Every chute serves live attestation evidence. Golden measurements are public; per-chute quotes take one authenticated GET:

```bash
# Golden measurements the fleet should match (public)
curl https://api.chutes.ai/servers/tee/measurements

# Fresh evidence for a specific chute (nonce = 64 hex chars you choose)
curl "https://api.chutes.ai/chutes/<chute_id>/evidence?nonce=<your-64-hex-nonce>" \
  -H "Authorization: Bearer $CHUTES_API_KEY"
```

What comes back is a real Intel TDX v4 quote plus NVIDIA GPU attestation for every instance serving that model. The [agent toolkit's `chutes-tee` skill](https://github.com/Veightor/chutes-agent-toolkit/tree/main/plugins/chutes-ai/skills/chutes-tee) parses these end to end. Its latest live run saw 14 instances on Blackwell GPUs, 5KB TDX quotes, and per-GPU attestation reports.

One honesty rule we hold ourselves to: parsing a quote proves its shape and contents, while cryptographic proof requires running Intel DCAP against it. The toolkit reports `shape-valid` until that pipeline runs, because under-claiming beats hand-waving.

---

## TEE-only routing in one line

```python
# Build your pool only from confidential-compute models, with failover
models = [m["id"] for m in get("https://llm.chutes.ai/v1/models")["data"]
          if m["confidential_compute"]]
model = ",".join(models[:3])   # "zai-org/GLM-5-TEE,deepseek-ai/DeepSeek-V3.2-TEE,..."
```

---

## FAQ

**Is there a performance or price penalty for TEE?**
TEE is the default and only tier. The pricing on `/v1/models` is the TEE price.

**Can Chutes employees see my prompts?**
No. Inference happens inside the enclave; the platform routes encrypted traffic to attested instances.

**What about the 25% research discount proxy?**
That is the explicit opposite trade: traffic through `research-data-opt-in-proxy.chutes.ai` is recorded for research. Sensitive workloads stay on `llm.chutes.ai`.

**What hardware is this?**
Intel TDX CPUs fronting NVIDIA GPUs (Hopper and Blackwell observed in fleet attestation), with per-GPU attestation reports in the evidence bundle.

---

## CTA band

**Run the agent you couldn't run on a black-box API.**
[Get a key](https://chutes.ai/auth/start) · [Fetch a real quote](https://api.chutes.ai/servers/tee/measurements) · [chutes-tee verification toolkit](https://github.com/Veightor/chutes-agent-toolkit/tree/main/plugins/chutes-ai/skills/chutes-tee)

---

## Build notes (not page copy)

- The "whole catalog" claim must render live: compute `all(m.confidential_compute)` from `/v1/models` at build time, and if it ever goes false the page should degrade to "N of M models" automatically rather than lie.
- The evidence endpoint requires a 64-hex `nonce` query param and Bearer auth; the golden-measurements endpoint is public. Both live-verified 2026-06-11.
- Consider an interactive "fetch evidence now" demo hitting the measurements endpoint client-side. It is public, so no key handling is needed.
- Copy review will want to escalate `shape-valid` to "cryptographically verified". Decline; the credibility of this page rests on that restraint.
