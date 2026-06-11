# OAuth Scope Cookbook

> Rule of thumb: start with the smallest scope set that makes your app usable. Add scopes only when a feature actually requires them. Users see the scopes at consent time — long lists spook them.

## Live scope list (verified 2026-06-11 via `GET /idp/scopes`)

| Scope | Grants |
|---|---|
| `profile` / `profile:read` | Read basic profile information (username, user_id) |
| `balance` / `balance:read` | Read account balance |
| `billing:read` | Read billing information, payment history |
| `quota` / `quota:read` | Read quota information and usage |
| `usage` / `usage:read` | Read usage statistics and invocation history |
| `account:read` | Read full account details including quotas, discounts, pricing |
| `account:write` | Modify account settings |
| `secrets:read` | Read secret names (not values) |
| `secrets:write` | Create and manage secrets |
| `chutes:read` | Read chute information and list chutes |
| `chutes:write` | Create and modify chutes |
| `chutes:delete` | Delete chutes |
| `chutes:invoke` | Invoke/run chutes |
| `images:read` / `images:write` / `images:delete` | Read / create+modify / delete images |
| `invocations:read` | Read invocation history and details |
| `admin` | Full access to all resources and actions — never request this for a relying party |

Two caveats:

- `openid` is **not** in the `/idp/scopes` list or in the discovery document's `scopes_supported` (verified 2026-06-11), even though platform OAuth docs describe it as the required base scope and the upstream SIWC package sends it. Keep sending it; whether the IdP requires or ignores it is unverified as of 2026-06-11.
- Platform docs describe a per-chute scope `chutes:invoke:{chute_id}` that limits a token to invoking one specific chute — the tightest delegation available when your app only ever calls one model (unverified as of 2026-06-11).

## Recipes

### 1. Auth-only (minimal)
**Scopes:** `openid`

When to use: You just need to know who the user is and prove they have a Chutes account. No inference, no account data, no billing.

User sees: "This app wants to verify your Chutes identity."

### 2. Delegated inference (default)
**Scopes:** `openid profile chutes:invoke`

When to use: Most apps. User signs in, your server makes inference calls on their behalf using the issued access token. Quota and billing hit **their** account, not yours.

User sees: "This app wants to verify your identity, see your display name, and make AI calls on your behalf."

### 3. Account dashboard
**Scopes:** `openid profile chutes:invoke account:read`

When to use: Your UI shows the user their Chutes username, balance, linked hotkey, or similar profile metadata.

User sees: "... and view your Chutes account details."

### 4. Full spend visibility
**Scopes:** `openid profile chutes:invoke account:read billing:read`

When to use: Usage / spend / quota dashboards. You're showing the user how much of *their* balance *your app's usage* consumed.

User sees: "... and view your Chutes usage and billing."

### 5. Sign-in only, no inference
**Scopes:** `openid profile`

When to use: Your app uses Chutes as an identity provider ("Sign in with Chutes" button next to Google / GitHub) but runs inference somewhere else. No `chutes:invoke` means the issued token is rejected at `llm.chutes.ai`.

User sees: "Verify your Chutes identity and see your display name."

### 6. Single-model app (tightest delegation)
**Scopes:** `openid profile chutes:invoke:{chute_id}`

When to use: Your app only ever invokes one specific chute (e.g. one fixed model). The token cannot invoke anything else even if it leaks. Per-chute scope documented by the platform but unverified as of 2026-06-11 — fall back to plain `chutes:invoke` if the authorize request is rejected.

## Anti-patterns

- **Requesting `billing:read` by default.** Users hate this. Only add when the feature actually exists in the UI.
- **Conflating management and delegation.** `chutes:invoke` scopes the app to the user's inference quota. It does **not** grant app CRUD or account changes. For admin tooling, users should authenticate with an API key, not an OAuth session.
- **Hardcoding scope strings across the codebase.** Put the scope list in one constant (e.g. `CHUTES_SCOPES`) and import it everywhere, so upgrading scopes is a one-line change.
- **Adding scopes "just in case."** Users re-consent every time scopes change. Keep the set tight.

## How scope changes affect existing users

When you change the scope list and the user logs in again, Chutes will show a new consent screen listing the delta. You do not get the new scopes silently. Plan rollouts with this in mind — sudden scope expansion on production is visible and noisy.

## Listing live scopes

The authoritative scope list lives at `GET /idp/scopes` (Bearer `cpk_` auth; verified live 2026-06-11). If you need a dynamic UI (for example, a self-service integrations admin page), fetch the list live instead of hardcoding.
