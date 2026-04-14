# Teeify a Chute **[BETA]**

> Source of truth: `PUT /chutes/{chute_id}/teeify`. This doc explains the semantics so agents don't oversell it.

## What "teeify" does

Takes an existing **affine chute** (a deployed chute that is eligible for confidential compute) and creates a TEE-isolated variant of it. Inference on the TEE variant runs inside an Intel TDX hardware enclave. Prompts and responses are hardware-isolated from the Chutes operators, the host OS, and the hypervisor.

Teeify does not:

- Add TEE to a non-affine chute. Only eligible chutes can be teeified.
- Provide automatic attestation verification. It just creates the variant — you still have to fetch and verify `/chutes/{chute_id}/evidence`.
- Remove the original chute. You get a new TEE variant alongside the existing one.

## Request

```
PUT /chutes/{chute_id}/teeify
Authorization: Bearer cpk_...
```

Body is typically empty or a small JSON object with optional metadata. Verify against the live OpenAPI schema.

Response: a new chute id (`chute_id`) and typically a new model id (the same name with a TEE suffix, or a separate fully-qualified id depending on Chutes conventions — do not hardcode the naming).

## What to tell the user

1. **"TEE" is a property exposed via `confidential_compute: true` on `/v1/models`, not a suffix.** Some models happen to be named `...-TEE`; use the boolean as the source of truth.
2. **Hardware isolation is real but does not equal "audited."** The user still needs to fetch attestation evidence (`GET /chutes/{chute_id}/evidence`) and verify the quote / certificate chain before trusting the environment.
3. **Deep verification is wave-2 work** (future `chutes-tee` skill). Today, this skill surfaces the evidence endpoint and tells the user what to do with it manually.
4. **Teeify costs money.** The TEE variant runs on specialized hardware and may cost more per token than the base chute. Check `/pricing` after teeify completes.

## Attestation evidence

```
GET /chutes/{chute_id}/evidence
```

Returns a JSON envelope typically containing:

- The Intel TDX quote (opaque bytes).
- A GPU attestation report (NVIDIA H100 confidential compute).
- The certificate chain used to sign the quote.
- Timestamps and nonce.

To verify the quote properly you need Intel's DCAP tooling and a trusted root certificate. The future `chutes-tee` skill will automate this. For now, if the user asks "is it real TEE," the honest answer is "the evidence endpoint returns a TDX quote — we are not verifying it automatically yet."

## Reverting

Deleting the TEE variant: `DELETE /chutes/{tee_chute_id}`. The original affine chute is untouched.

## Safety reminder

Do not make strong privacy claims to users based solely on the fact that teeify succeeded. Until the evidence is verified, the guarantee is "Chutes says this chute runs in TEE." That is usually true, but "trust me" is not a security claim.
