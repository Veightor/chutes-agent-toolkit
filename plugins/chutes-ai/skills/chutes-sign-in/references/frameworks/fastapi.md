# Sign in with Chutes — FastAPI **[STUB — upstream pending]**

> **Status: STUB.** The upstream `chutesai/Sign-in-with-Chutes` repository does not yet ship a FastAPI adapter. This skill refuses to run the installer against FastAPI projects until upstream lands.

## What to tell the user

Same as the Express stub: Next.js is the only adapter shipped today. If the user wants to implement manually right now, the flow shape is identical — see `references/oauth-flow.md` and `references/idp-endpoints.md`.

## Minimal manual implementation sketch

```python
from fastapi import APIRouter, Request, HTTPException
import httpx
import secrets
import hashlib
import base64
from urllib.parse import urlencode

router = APIRouter(prefix="/auth/chutes")

AUTHORIZE = "https://api.chutes.ai/idp/authorize"
TOKEN = "https://api.chutes.ai/idp/token"
REVOKE = "https://api.chutes.ai/idp/token/revoke"

def pkce_pair():
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge

@router.get("/login")
async def login(request: Request):
    verifier, challenge = pkce_pair()
    state = secrets.token_urlsafe(32)
    request.session["chutes_verifier"] = verifier
    request.session["chutes_state"] = state
    params = urlencode({
        "response_type": "code",
        "client_id": CHUTES_OAUTH_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile chutes:invoke",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    })
    return RedirectResponse(f"{AUTHORIZE}?{params}")

# ...callback, session, logout follow the same shape.
```

This is a sketch, not a drop-in. Use a real session store (`itsdangerous`, Redis, etc.) and put `CHUTES_OAUTH_CLIENT_ID` / `CHUTES_OAUTH_CLIENT_SECRET` in env, sourced from `manage_credentials.py`.

Prefer to wait for the upstream FastAPI package.
