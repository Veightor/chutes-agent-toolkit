# OAuth Scope Cookbook

> **Status: BETA** — mirrors `plugins/chutes-ai/skills/chutes-sign-in/references/scope-cookbook.md` so operators and planners can find it in `docs/`. The skill file is the source of truth during the BETA window.

## Rule of thumb

Start with the smallest scope set that makes your app usable. Add scopes only when a feature actually requires them. Users see the scopes on the consent screen — long lists spook them.

## Recipes

### 1. Auth-only (minimal)
**Scopes:** `openid`

You just need to know who the user is. No inference, no account data, no billing.

### 2. Delegated inference (default for most apps)
**Scopes:** `openid profile chutes:invoke`

User signs in, your server makes inference calls on their behalf using the access token. Quota and billing hit **their** account.

### 3. Account dashboard
**Scopes:** `openid profile chutes:invoke account:read`

Adds the ability to show the user their Chutes username, balance, linked hotkey, or similar profile metadata.

### 4. Full spend visibility
**Scopes:** `openid profile chutes:invoke account:read billing:read`

Usage / spend / quota dashboards. You're showing the user how much of *their* balance *your app's usage* consumed.

### 5. Sign-in only, no inference
**Scopes:** `openid profile`

Your app uses Chutes purely as an identity provider. No `chutes:invoke` means the issued token will be rejected at `llm.chutes.ai`.

## Anti-patterns

- **Requesting `billing:read` by default.** Only add when the feature exists in the UI.
- **Conflating management and delegation.** `chutes:invoke` is user-delegated inference. It does not grant app CRUD or account management — for admin tooling, authenticate with an API key, not an OAuth session.
- **Hardcoding scope strings across the codebase.** Put them in one constant and import it.
- **Adding scopes "just in case."** Users re-consent every time scopes change.

## Listing live scopes

The authoritative scope list lives at `GET /idp/scopes`. If you need a dynamic self-service integrations page, fetch the list live.

## Related

- `docs/sign-in-with-chutes.md`
- `docs/oauth-app-management.md`
- `plugins/chutes-ai/skills/chutes-sign-in/references/scope-cookbook.md` (source)
