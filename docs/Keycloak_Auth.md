# Keycloak Auth Integration

Keycloak is used as the identity provider for all API endpoints. Every request must carry a valid Bearer token issued by Keycloak. Rate limiting is handled by `slowapi` on top of auth.

## Auth Flow

```bash
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Browser   │         │  Keycloak   │         │   FastAPI   │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                        │
       │  1. Login redirect     │                        │
       │──────────────────────>│                        │
       │                       │                        │
       │  2. Auth code (PKCE)  │                        │
       │<──────────────────────│                        │
       │                       │                        │
       │  3. Exchange code     │                        │
       │──────────────────────>│                        │
       │                       │                        │
       │  4. JWT access token  │                        │
       │<──────────────────────│                        │
       │                       │                        │
       │  5. API request + JWT │                        │
       │───────────────────────────────────────────────>│
       │                       │                        │
       │                       │  6. Fetch JWKS (once) │
       │                       │<───────────────────────│
       │                       │                        │
       │                       │  7. JWKS public keys  │
       │                       │───────────────────────>│
       │                       │                        │
       │                       │     8. Verify JWT      │
       │                       │     signature locally  │
       │                       │                        │
       │  9. API response      │                        │
       │<───────────────────────────────────────────────│
```

Steps 1–4 use the `inquisitool-frontend` public client (PKCE, no secret). Steps 6–7 only happen once — JWKS is cached in-process after the first request. All subsequent requests skip straight from step 5 to step 8.

## What Changed

### `docker-compose.yml`

Two new services added:

- `keycloak-db` — Postgres 16 backing store for Keycloak
- `keycloak` — Keycloak 26.2 running in dev mode on port `8080`

```yaml
keycloak:
  image: quay.io/keycloak/keycloak:26.2
  command: start-dev
  ports:
    - "8080:8080"
  depends_on:
    - keycloak-db
```

> `start-dev` is for local development only. For production use `start` with TLS and a proper hostname config.

### `inquisitool/constants.py`

Two new env-backed constants:

```python
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "inquisitool")
```

### `inquisitool/auth.py` (new)

Core auth module with two responsibilities:

**JWT verification (`require_auth`)**

- Fetches Keycloak's public keys from the JWKS endpoint on first request, cached in-process
- Validates the Bearer token: signature, issuer, `kid` match
- Returns the decoded token payload (claims) as a dict

**Rate limiter (`limiter`)**

- `slowapi` `Limiter` instance keyed by remote IP
- Imported by route files that need per-endpoint limits

```python
# JWKS endpoint used:
GET {KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs
```

### `inquisitool/main.py`

- `require_auth` applied as a **global dependency** — all routes require a valid token automatically
- `limiter` attached to `app.state` so `slowapi` can resolve it
- `RateLimitExceeded` exception handler registered globally

```python
app = FastAPI(lifespan=lifespan, dependencies=[Depends(require_auth)])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### `inquisitool/routes/query.py`

`/query/survey` has an explicit rate limit:

```python
@router.post("/survey", response_model=SurveyResponse)
@limiter.limit("30/minute")
async def process_survey(request: SurveyRequest, req: Request): ...
```

### `pyproject.toml`

Three new dependencies:

| Package | Purpose |
| --- | --- |
| `python-jose[cryptography]` | JWT decode and JWKS verification |
| `slowapi` | Rate limiting for FastAPI |
| `httpx` | Async HTTP client to fetch JWKS from Keycloak |

---

## Setup: Getting It Running

### 1. Start Keycloak

```bash
docker-compose up -d keycloak
```

Wait ~30 seconds for Keycloak to be ready, then open `http://localhost:8080`.

### 2. Create the Realm

1. Log in with `admin` / `admin`
2. Hover over `master` in the top-left → click **Create realm**
3. Set **Realm name** to `inquisitool` → **Create**

### 3. Create a Backend Client (for API / service-to-service)

1. Go to **Clients** → **Create client**
2. **Client ID**: `inquisitool-api`
3. **Client authentication**: ON
4. **Authentication flow**: uncheck everything except **Service accounts roles**
5. Save → go to **Credentials** tab → copy the **Client secret**

Get a token for testing:

```bash
curl -X POST http://localhost:8080/realms/inquisitool/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=inquisitool-api" \
  -d "client_secret=<your_client_secret>"
```

### 4. Create a Frontend Client (for browser / SPA — when ready)

1. Go to **Clients** → **Create client**
2. **Client ID**: `inquisitool-frontend`
3. **Client authentication**: OFF (public client)
4. **Authentication flow**: Standard flow only
5. Set **Valid redirect URIs** to your frontend URL (e.g. `http://localhost:3000/*`)
6. Save

The frontend uses the Authorization Code + PKCE flow via `keycloak-js` or any OIDC library.

### 5. Update `.env`

```env
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=inquisitool
```

For Docker Compose (app container talking to Keycloak container):

```env
KEYCLOAK_URL=http://keycloak:8080
```

### 6. Install new dependencies

```bash
pip install -e .
```

### 7. Start the app

```bash
inquisitool run --host 0.0.0.0 --port 8000
```

### 8. Test an authenticated request

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/realms/inquisitool/protocol/openid-connect/token \
  -d "grant_type=client_credentials" \
  -d "client_id=inquisitool-api" \
  -d "client_secret=<your_client_secret>" | jq -r .access_token)

curl http://localhost:8000/campaigns/ -H "Authorization: Bearer $TOKEN"
```

---

## Production Checklist

- Replace `start-dev` with `start` in the Keycloak command and configure `KC_HOSTNAME`
- Set strong `KEYCLOAK_ADMIN_PASSWORD` via secrets, not hardcoded in compose
- Add TLS termination in front of Keycloak (nginx / AWS ALB)
- Switch rate limit key from remote IP to `sub` claim — see `docs/Rate_Limits.md`
- Rotate the Keycloak DB credentials
