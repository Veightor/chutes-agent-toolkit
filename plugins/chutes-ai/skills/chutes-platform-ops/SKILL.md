---
name: chutes-platform-ops
description: "Chutes.ai platform operator flows: OAuth app inventory + audits, client-secret rotation at fleet scale, token introspection and revocation, authorization management, model alias CRUD as an operator task. Use when the user asks to audit their OAuth apps, rotate secrets across many apps, introspect or revoke tokens, inspect authorizations, or manage model aliases as a team-level operator. Triggers on: chutes oauth app audit, list oauth apps, stale oauth apps, rotate all secrets, token introspect, token revoke, authorizations, /idp/apps, /idp/token, alias CRUD, fleet operator, chutes doctor."
---

# chutes-platform-ops

> **Status: VERIFIED LIVE 2026-04-13** via `docs/chutes-maxi-wave-2.md` Track A.3 — `list_apps.py`, `audit_stale_apps.py`, and `alias_crud.py` exercised against the dev Chutes account. `introspect_token.py` and `revoke_token.py` **cannot be live-exercised without a real OAuth access token**; both are documented here and marked individually BETA until a SIWC session produces a token to test them with.

## What this skill does

Complements `chutes-sign-in` (single-app) and `chutes-deploy` (single-chute) with **fleet-scale** operator flows:

- **App inventory.** Paginate `/idp/apps`, filter to mine, join with authorization counts.
- **Stale-app audit.** Find OAuth apps with zero active authorizations, or old apps you forgot about.
- **Bulk secret rotation.** Rotate many apps at once with dry-run support.
- **Token hygiene.** Introspect / revoke OAuth access tokens in incident response.
- **Alias fleet management.** List / create / delete / re-point aliases as a governance surface (same endpoints as `chutes-deploy:alias_deploy.py` but focused on ops, not deploy).

## Walkthrough

### Step 1 — inventory

```bash
python <skill-scripts-dir>/list_apps.py
python <skill-scripts-dir>/list_apps.py --all        # include other users' apps (platform-wide)
python <skill-scripts-dir>/list_apps.py --with-authorizations
```

Prints a table of your OAuth apps joined with live authorization counts:

```
=== my OAuth apps (16 of 425 platform-wide) ===
  name                            app_id        client_id              created     active  auths
  Chutes Dropzone Local           f8769b1c...   cid_nkjg2ilriy5q...   2026-04-10  True    2
  Agent Test App                  38c3f2d6...   cid_eura0kxgeqbm...   2026-03-12  True    0
  AI Week Presentation Port 3000  bbd1c6db...   cid_6nsmkugxzkbi...   2026-03-06  True    1
  ...
```

**Wave-2 finding:** `GET /idp/apps?mine=true` and `?user_id=<uuid>` are **ignored** by the server — the response stays platform-wide paginated (425 total on the test account). `list_apps.py` paginates all pages and filters by `user_id` client-side.

### Step 2 — audit stale apps

```bash
python <skill-scripts-dir>/audit_stale_apps.py
python <skill-scripts-dir>/audit_stale_apps.py --min-age-days 30
```

Reports apps that look abandoned:

- **Zero authorizations** — no user has ever signed in with this app.
- **Created > N days ago** — aged, candidate for review.
- **No activity** — heuristic based on missing recent authorizations.

Pure read-only report. Does **not** delete anything.

```
=== stale OAuth app audit ===
  Apps with zero active authorizations (candidates for cleanup):
    - teryeure          app_id=d78bef04...  age=57d
    - Test apppy        app_id=7eae13c6...  age=57d
    - Agent Test App    app_id=38c3f2d6...  age=33d

  Total audited: 16 of your apps
  Recommendation: inspect each before deleting — some may be staged for a future launch.
```

### Step 3 — bulk secret rotation

```bash
# DRY RUN (always first)
python <skill-scripts-dir>/rotate_all.py --match "Test*" --dry-run

# Actually rotate (requires explicit --yes)
python <skill-scripts-dir>/rotate_all.py --match "Test*" --yes
```

Matches app names against a glob, iterates matching apps, calls `POST /idp/apps/{app_id}/regenerate-secret` for each, and writes the new secret to a per-app keychain profile (e.g. `oauth.rotate-20260414T013559-<slug>`). Default: **dry-run**.

**Safety guarantees:**
- `--dry-run` prints the matched set and exits without writing.
- `--yes` is required to actually rotate; omitting it makes the script refuse even without `--dry-run`.
- No parallelism — rotations happen one-at-a-time so a mid-run crash doesn't fan out.
- New secrets are stored in fresh keychain profiles so the old ones are not overwritten until you explicitly `manage_credentials.py delete`.
- The script **never prints** a `csc_` value; only redacted previews.

### Step 4 — token introspection (incident response)

```bash
python <skill-scripts-dir>/introspect_token.py --token <token_from_session>
```

Wraps `POST /idp/token/introspect` (RFC 7662). Returns `{active, scope, client_id, username, exp, sub, ...}`.

When to use: you suspect a token leaked, or you want to confirm a specific OAuth session is still valid.

> **Status BETA:** this script has NOT been live-verified because the wave-2 verification environment has no real OAuth access token on hand (would require completing a full SIWC browser flow). Graduates as soon as one verified call lands.

### Step 5 — token revocation

```bash
python <skill-scripts-dir>/revoke_token.py --token <access_or_refresh_token>
```

Wraps `POST /idp/token/revoke`. Returns `{revoked: true}` on success. Use this on detected credential leaks or forced-logout scenarios.

> **Status BETA:** same as introspection — not yet exercised live.

### Step 6 — alias fleet management

```bash
python <skill-scripts-dir>/alias_crud.py --list
python <skill-scripts-dir>/alias_crud.py --create --alias team-fast --chute-id <uuid> --chute-id <uuid>
python <skill-scripts-dir>/alias_crud.py --delete --alias team-fast --yes
```

Same endpoints as `chutes-routing:build_pool.py` and `chutes-deploy:alias_deploy.py`, but with an operator lens: bulk list with owner/size, create with explicit chute_ids (no intent filter), delete with `--yes` gate.

When to use each:
- `chutes-routing:build_pool.py` — when you're choosing a pool from an **intent**.
- `chutes-deploy:alias_deploy.py` — when you're pinning an alias **during or right after a deploy**.
- `chutes-platform-ops:alias_crud.py` — when you're managing the alias fleet as an operator task disconnected from any specific deploy or intent.

## Endpoint map

| Area | Method | Path |
|---|---|---|
| List OAuth apps (platform-wide) | GET | `/idp/apps?page=<n>&limit=<n>` |
| Read one app | GET | `/idp/apps/{app_id}` |
| Update metadata | PATCH | `/idp/apps/{app_id}` |
| Delete app | DELETE | `/idp/apps/{app_id}` |
| Regenerate client secret | POST | `/idp/apps/{app_id}/regenerate-secret` |
| List scopes | GET | `/idp/scopes` — returns `{scopes: {<name>: <description>}}` |
| List authorizations (yours) | GET | `/idp/authorizations` — paginated `{total, page, limit, items}` |
| Revoke authorization by app | DELETE | `/idp/authorizations/{app_id}` |
| Introspect token | POST | `/idp/token/introspect` body `{token}` |
| Revoke token | POST | `/idp/token/revoke` body `{token}` |
| OIDC userinfo | GET | `/idp/userinfo` — **needs OAuth access token, not `cpk_`** (401 otherwise) |
| List aliases | GET | `/model_aliases/` |
| Create alias | POST | `/model_aliases/` body `{alias, chute_ids: [uuid, ...]}` |
| Delete alias | DELETE | `/model_aliases/{alias}` |

**Wave-2 finding:** `/idp/scopes` returns 22 named scopes including `admin`, `profile[:read]`, `balance[:read]`, `billing:read`, `quota[:read]`, `usage[:read]`, `account:{read,write}`, `chutes:{read,write,delete,invoke}`, `images:{read,write,delete}`, `invocations:read`, `secrets:{read,write}`. The standard OIDC `openid` scope is NOT in this list — it is still accepted by `POST /idp/apps` (wave-1 `register_oauth_app.py` confirmed it), just not enumerated here.

**Wave-2 finding:** `GET /idp/userinfo` returns HTTP 401 `{"detail":"Invalid or expired token"}` when called with a `cpk_` management API key. The endpoint is OAuth-access-token-only, per OIDC spec. Document, don't try to call it from operator scripts.

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/list_apps.py` | Paginate + filter my apps, join with authorizations | VERIFIED (2026-04-13) |
| `scripts/audit_stale_apps.py` | Zero-auth / old-age audit report | VERIFIED (2026-04-13) |
| `scripts/rotate_all.py` | Bulk secret rotation with dry-run + per-app keychain profiles | VERIFIED (dry-run, 2026-04-13) |
| `scripts/introspect_token.py` | `POST /idp/token/introspect` wrapper | **[BETA]** — needs a live OAuth access token to exercise |
| `scripts/revoke_token.py` | `POST /idp/token/revoke` wrapper | **[BETA]** — same |
| `scripts/alias_crud.py` | Alias list/create/delete with `--yes` gate for destructive ops | VERIFIED (2026-04-13) |

## Safety rules

- **Destructive ops require explicit `--yes`.** `rotate_all.py`, `alias_crud.py --delete`, `audit_stale_apps.py --delete` all refuse to mutate state without it. Dry-run is the default everywhere.
- **`rotate_all.py` is sequential, not parallel.** A mid-run failure leaves a partial rotation and the script reports where it stopped; you re-run with `--skip-until <app_id>` to continue.
- **Never print `csc_` values.** Rotation stores new secrets via `manage_credentials.py` under timestamped profiles. Only redacted previews appear on stdout.
- **Never delete apps from an audit.** `audit_stale_apps.py` is advisory; deletion is user-initiated via `DELETE /idp/apps/{app_id}` explicitly.
- **OAuth token operations require caution.** `revoke_token.py` breaks every session using that token. Log who you ran it against and why.

## Related skills

- `chutes-sign-in` — single-app SIWC integrator; pair with this skill for bulk operator work.
- `chutes-routing` — `build_pool.py` is the intent-driven alias creator; `alias_crud.py` here is the lower-level CRUD.
- `chutes-usage-and-billing` — audit spend on the account running these ops.
- `chutes-mcp-portability` — `chutes_oauth_introspect` exposes introspect via MCP (still BETA there for the same reason — needs a live token).
