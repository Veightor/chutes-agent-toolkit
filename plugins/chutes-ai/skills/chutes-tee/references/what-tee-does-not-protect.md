# What TEE (honestly) does not protect

> When a chute advertises `confidential_compute: true`, prompts and responses run inside an Intel TDX enclave on a Hopper GPU with NVIDIA confidential compute enabled. That's a real property — but it's not "my data is safe." Here's what it doesn't guarantee.

## What TEE does protect

Against an attacker who:

- Has **host-level** access (root on the box, hypervisor, Chutes operator).
- Tries to read RAM directly, snapshot memory, or tamper with the model binary.
- Tries to intercept prompts / responses **in transit** across the host's memory paths between CPU enclave and GPU.

TDX + GPU confidential compute make all three extraordinarily difficult — the model weights and the prompt/response buffers live in encrypted memory regions that are only unsealed inside the enclave.

## What TEE does not protect against

### 1. The model itself
If the model has been fine-tuned to log prompts to an external service, TEE does not stop that — the model runs *inside* the TEE and is trusted to do what it says it does. You are trusting the measured code (the `mrtd` value) to be honest. Verify the measurement against a known-good value before trusting the output.

### 2. Prompt injection
Users (or content you feed into the prompt) can still jailbreak the model, extract training data, trick it into running tools. TEE is a memory-safety property, not a behavioral one.

### 3. Output inspection *after* the TEE
The TEE boundary ends at the HTTP response. Once the response leaves `llm.chutes.ai`, you're in normal network-over-TLS territory. Any intermediary you add (proxy, edge function, logging middleware) is outside the TEE envelope.

### 4. Log drift
Chutes' own infrastructure — billing, rate-limiting, routing — may incidentally log metadata about your requests (token counts, timestamps, which model you hit). This metadata is not the content of the prompt, but it's still telemetry. Check Chutes' privacy policy; TEE does not address the metadata side channel.

### 5. Side channels
- **Timing.** TEE doesn't protect against timing attacks on the model's decode path.
- **Memory access patterns** when the kernel pages enclave memory to disk. TDX blocks most of these but some remain.
- **Power consumption** on the host. Extremely unlikely in practice but theoretically possible.

### 6. Compromised attestation pipeline
If NVIDIA's trust root or Intel's DCAP trust root is itself compromised, the whole attestation chain is unsound. This is the "we trust Intel" assumption and it's baked into every TDX deployment everywhere.

### 7. Supply chain
The BIOS / firmware / driver stack on the Chutes host is not covered by the TDX quote alone — it has its own measurement infrastructure (SRTM/DRTM/TPM). Auditing the full supply chain is a bigger job than attestation.

### 8. "Deep verification" that you didn't actually run
If `chutes-tee` reports `verdict: shape-valid` instead of `verdict: verified`, the cryptographic guarantees are NOT active — you only checked that the envelope looks right. Do not present shape-valid as "verified" to an auditor; it isn't.

## Rule of thumb

TEE is necessary but not sufficient for "privacy-preserving AI inference." Pair with:

- **Known-good `mrtd` reference** captured at deploy time, with monitoring alerts on drift.
- **Attestation verification on every session** (not cached), to prevent time-of-check-to-time-of-use drift.
- **Strict scope on what enters the prompt** — TEE doesn't save you from a prompt containing something it shouldn't.
- **End-to-end encryption of the prompt/response** at the application layer if your threat model includes network intermediaries.

## The one thing TEE absolutely guarantees (when verified)

That the exact code with the measured hashes ran the inference, inside a hardware-isolated region, on an attested GPU, against the nonce you supplied. Nothing less, nothing more. Everything else is application-level.
