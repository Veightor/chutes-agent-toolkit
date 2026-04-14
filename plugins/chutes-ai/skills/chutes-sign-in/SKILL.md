---
name: chutes-sign-in
description: "Add Sign in with Chutes (OAuth 2.0 + OIDC + PKCE) to a user's application. Use this skill when the user wants to register a Chutes OAuth app, vendor the chutesai/Sign-in-with-Chutes Next.js package into their project, wire up sign-in routes, manage scopes, store client credentials in the OS keychain, or rotate a client secret. Triggers on: sign in with chutes, SIWC, OAuth app, /idp/apps, cid_, csc_, chutes oauth, PKCE chutes, chutes login button, useChutesSession, Next.js chutes auth, rotate oauth secret."
---

# chutes-sign-in

> **Status: VERIFIED LIVE 2026-04-13** via `docs/chutes-maxi-wave-2.md` Track C.4. Full end-to-end exercised against a real Chutes account: `register_oauth_app.py` → `install_siwc.py` → `verify_siwc.py` (steps 1-3) → `rotate_secret.py` → cleanup. Real OAuth app created, real SIWC files vendored into a scratch Next.js App Router project, client secret rotated, app deleted.
>
> **Graduated:** `register_oauth_app.py`, `install_siwc.py`, `rotate_secret.py`, the skill itself.
>
> **Still BETA — `verify_siwc.py`** — steps 1-3 (files / env / keychain match) passed live but step 4 (dev server `/api/auth/chutes/session` hit) was not exercised (would require `npm install` + `npm run dev`, out of scope for automated verification). Stays BETA until step 4 is exercised end-to-end.
>
> **Wave-2 bug fixes that live verification caught:**
>
> 1. **Wrong upstream source paths.** `install_siwc.py` + `verify_siwc.py` + `references/frameworks/nextjs.md` assumed `packages/nextjs/app/api/auth/chutes/<name>/route.ts` but upstream stores them as flat files at `packages/nextjs/api/auth/chutes/<name>.ts` with a "copy me to `app/api/auth/chutes/<name>/route.ts`" comment. Installer now performs the directory + filename transform during copy.
> 2. **`rotate_secret.py` passed `client_id` as the URL segment** on `POST /idp/apps/{X}/regenerate-secret`; API requires the `app_id` UUID. Added `app_id` to `manage_credentials.py` field whitelist, `register_oauth_app.py` now stores it on creation, `rotate_secret.py` reads it from the keychain with a clear migration error if a legacy profile lacks it.

## What this skill does

Turns any Next.js App Router application into a Chutes OAuth relying party by:

1. Registering an OAuth app on Chutes via `POST /idp/apps`.
2. Storing the returned `cid_...` / `csc_...` in the OS keychain via `manage_credentials.py`.
3. Vendoring the upstream `chutesai/Sign-in-with-Chutes` Next.js package at a pinned commit into the target project.
4. Writing `.env.local` entries for the OAuth client id / secret and app URL.
5. Offering a diff to wire `<SignInButton />` into the user's top-level layout.
6. Verifying the flow against the dev server and `/idp/token/introspect`.
7. Later: rotating the client secret via `POST /idp/apps/{id}/regenerate-secret` without leaking it to transcript.

SIWC upstream today ships the Next.js App Router package; Pages Router / Express / FastAPI are tracked but not yet shipped. This skill detects the target and gracefully degrades.

## Prerequisites

- The user already has a Chutes account and API key (run `chutes-ai` first if not).
- The target project is a Next.js 14+ App Router app (or the user accepts a stubbed walkthrough for other frameworks).
- Python 3.10+ for the helper scripts.
- `git` on PATH for the SIWC vendor step.

## Walkthrough

### Step 1 — detect the target framework

Before touching anything, detect:

- `package.json` present → read `dependencies.next`. `< 14.0.0` → warn and ask to upgrade first.
- `src/app/` or `app/` directory → App Router ✓
- `pages/` directory only → Pages Router → **stub path** (print upstream tracking link, stop).
- No `package.json`, Python `fastapi` in `requirements.txt` → FastAPI → **stub path**.
- Node but not Next.js (Express in deps) → Express → **stub path**.

Stub paths should not register an OAuth app. Pointing at the upstream repo and stopping is the correct behavior until SIWC ships those adapters.

### Step 2 — choose scopes

Default: `openid profile chutes:invoke`. Always confirm before adding:

- `account:read` — lets the app display username / balance. Add when the UI shows account info.
- `billing:read` — lets the app display usage / quotas. Add only when the app needs spend visibility.

Point the user at `references/scope-cookbook.md` for least-privilege recipes.

### Step 3 — register the OAuth app

Run the registration helper (never paste secrets into the chat):

```bash
python <skill-scripts-dir>/register_oauth_app.py \
  --name "My App" \
  --homepage-url https://myapp.example.com \
  --redirect-uri http://localhost:3000/api/auth/chutes/callback \
  --redirect-uri https://myapp.example.com/api/auth/chutes/callback \
  --scope openid --scope profile --scope chutes:invoke \
  --profile oauth.my-app
```

The script:

1. Pulls the Chutes `cpk_` API key from `manage_credentials.py get --field api_key`.
2. POSTs `/idp/apps` with the supplied metadata.
3. Captures `client_id` (`cid_...`) and `client_secret` (`csc_...`) from the response.
4. Writes both into the keychain under the given `--profile` (e.g. `oauth.my-app`) as `client_id` / `client_secret`.
5. Prints the `client_id` to stdout (not the secret), followed by the profile name.

Confirm with:

```bash
python <skill-scripts-dir>/manage_credentials.py check
```

### Step 4 — vendor the SIWC Next.js package

```bash
python <skill-scripts-dir>/install_siwc.py --target /path/to/next-app --profile oauth.my-app
```

What it does:

1. Clones `https://github.com/chutesai/Sign-in-with-Chutes` at a pinned commit into `~/.chutes/cache/siwc/<sha>/`.
2. Copies `packages/nextjs/{lib/chutesAuth.ts,lib/serverAuth.ts,hooks/useChutesSession.ts,app/api/auth/chutes/*,components/SignInButton.tsx}` into the target project.
3. Respects `src/` vs flat layout. Idempotent — prompts before overwriting an existing file.
4. Appends to `.env.local` (creating it if missing) using `manage_credentials.py get` subprocesses so the secret never touches transcript:

   ```
   CHUTES_OAUTH_CLIENT_ID=<from keychain>
   CHUTES_OAUTH_CLIENT_SECRET=<from keychain>
   NEXT_PUBLIC_APP_URL=http://localhost:3000
   ```

5. Prints a summary of files copied and a patch for the user's top-level layout showing where to drop `<SignInButton />`. **Never auto-edits the layout** — the user confirms and applies the diff themselves.

### Step 5 — start dev server and test the flow

```bash
cd /path/to/next-app
npm run dev
```

The user clicks the SignInButton. Browser redirects to Chutes, they authorize, and bounce back to `/api/auth/chutes/callback`. `useChutesSession` returns the user session.

### Step 6 — verify programmatically

```bash
python <skill-scripts-dir>/verify_siwc.py --target /path/to/next-app --profile oauth.my-app
```

The verifier:

1. Hits `GET http://localhost:3000/api/auth/chutes/session` and asserts a 200 or 401 shape (not a 500).
2. If an access token is available in the current session, `POST /idp/token/introspect` and assert `active: true`, `scope` includes the requested scopes, `client_id` matches keychain.
3. Returns exit 0 / 1 / 2 so it can be wired into CI later.

### Step 7 — rotate the client secret (when needed)

```bash
python <skill-scripts-dir>/rotate_secret.py --profile oauth.my-app
```

1. `POST /idp/apps/{id}/regenerate-secret` where `{id}` is the stored `client_id` (resolved via the keychain profile).
2. Overwrite the `client_secret` field in the keychain.
3. Print a prominent reminder: **redeploy any running service that loaded the old secret** (Next.js on Vercel, production backends, etc.). The skill does not auto-redeploy — too much blast radius.

---

## Endpoint map (`/idp/*`)

See `references/idp-endpoints.md` for the full list. Summary:

| Action | Method | Path |
|---|---|---|
| Create OAuth app | POST | `/idp/apps` |
| List my OAuth apps | GET | `/idp/apps` |
| Get one app | GET | `/idp/apps/{app_id}` |
| Update app metadata | PATCH | `/idp/apps/{app_id}` |
| Delete app | DELETE | `/idp/apps/{app_id}` |
| Regenerate client secret | POST | `/idp/apps/{app_id}/regenerate-secret` |
| List available scopes | GET | `/idp/scopes` |
| List authorizations | GET | `/idp/authorizations` |
| Revoke authorization | DELETE | `/idp/authorizations/{app_id}` |
| Token introspect | POST | `/idp/token/introspect` |
| Token revoke | POST | `/idp/token/revoke` |
| Userinfo | GET | `/idp/userinfo` |

## Scripts in this skill

| Script | Purpose | Status |
|---|---|---|
| `scripts/register_oauth_app.py` | `POST /idp/apps` + store in keychain | VERIFIED (2026-04-13) |
| `scripts/install_siwc.py` | Vendor upstream Next.js package + write env | VERIFIED (2026-04-13, with wave-2 path-transform fix) |
| `scripts/verify_siwc.py` | Hit session route + introspect token | **[BETA]** — steps 1-3 verified; step 4 (dev server) not exercised |
| `scripts/rotate_secret.py` | `POST /idp/apps/{id}/regenerate-secret` | VERIFIED (2026-04-13, with wave-2 app_id fix) |

## Safety rules

- **Never echo `csc_...` into the conversation** — all secret handling routes through `manage_credentials.py` via subprocess.
- **Never auto-edit user source files** — vendor into a package directory, print a diff for the layout, let the user apply it.
- **Never commit `.env.local`** — the skill assumes the target project already has `.env.local` in `.gitignore` and warns if it is not.
- **Never skip framework detection** — registering an OAuth app against the wrong framework gives users a dead-end integration.
- **Never auto-redeploy on secret rotation** — print the reminder and stop.

## Related skills

- `chutes-ai` (hub) — prerequisite for the API key.
- `chutes-platform-ops` (wave 2 stub) — broader OAuth app lifecycle beyond SIWC setup (introspect, revoke, audit authorizations).
- `chutes-mcp-portability` **[BETA]** — exposes `chutes_oauth_introspect` as an MCP tool for any MCP-aware client.
