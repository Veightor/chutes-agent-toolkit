# Rolling Updates on Chutes **[BETA]**

> `GET /chutes/rolling_updates` — still present in `api.chutes.ai/openapi.json` (verified 2026-06-11).

## What a rolling update is

When a chute's underlying image or configuration changes, Chutes will roll the update out across the pool of nodes running the chute instead of cutting over all at once. This is **server-side and automatic**: it is triggered when a code/image change to an existing chute lands (e.g. a new image build completing) — there is no user-facing CLI command for rollouts, and updates to existing chutes do not incur a new deployment fee (verified in the chutes-api source and SDK README, 2026-06-11). Implications:

- Some callers continue to hit the old revision for a brief window.
- A new revision is warming up on some nodes while the old one is still serving on others.
- If the new revision fails warmup, the rollout halts and the old revision stays up.

## Inspecting updates in flight

```
GET /chutes/rolling_updates
Authorization: Bearer cpk_...
```

Returns something like:

```json
[
  {
    "chute_id": "chute_...",
    "name": "myuser/qwen3-8b",
    "old_revision": "abc123",
    "new_revision": "def456",
    "state": "in_progress",
    "old_instances": 3,
    "new_instances": 1,
    "started_at": "2026-04-13T..."
  }
]
```

States worth knowing:

- `pending` — new revision queued but not yet building.
- `building` — image is building for the new revision.
- `rolling` — some nodes on the new revision, some on the old.
- `complete` — all instances are on the new revision.
- `halted` — a node failed warmup, rollout paused. Inspect build logs via `GET /images/{image_id}/logs`.

## What agents should do with this

- When a user says "my chute seems flaky" or "some calls are slow," check this endpoint before blaming the network. A mid-rollout chute can have mixed behavior.
- When you deploy via `deploy_vllm.py --redeploy` or equivalent, tail the rolling update state in a second terminal.
- Do not automatically force-reset a halted rollout. The safer path is: inspect build logs, fix the cause, push a new build. Force-reset is out of scope for this skill.

## Related

- `GET /images/{image_id}/logs` — build logs for the new revision.
- `GET /chutes/warmup/{chute_id_or_name}` — warmup status for instances already on the new revision.
- `chutes_list_chutes` in the `chutes-mcp-portability` MCP server — includes chute status fields that flag rollouts.
