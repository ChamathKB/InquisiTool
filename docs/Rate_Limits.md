# Rate Limits

Rate limiting is handled by `slowapi` (backed by Redis) and applied per IP address. Auth is handled by Keycloak — a valid Bearer token is required on all endpoints.

## Current Limits

| Endpoint                              | Method | Limit       |
|---------------------------------------|--------|-------------|
| `/query/survey`                       | POST   | 30 / minute |
| All others (global default via auth)  | ANY    | unlimited*  |

> *Global auth enforcement is in place but no blanket rate limit is set. Add `@limiter.limit(...)` per route as needed (see below).

## Adding Limits to Other Routes

Import and apply the limiter decorator to any route handler:

```python
from inquisitool.auth import limiter

@router.post("/")
@limiter.limit("10/minute")
async def my_endpoint(request: Request): ...
```

`slowapi` requires the FastAPI `Request` object to be present as a parameter — it is already present on all existing routes.

## Limit String Format

Limits follow the `limits` library syntax:

| String            | Meaning                        |
|-------------------|--------------------------------|
| `"30/minute"`     | 30 requests per minute         |
| `"100/hour"`      | 100 requests per hour          |
| `"5/second"`      | 5 requests per second          |
| `"1000/day"`      | 1000 requests per day          |

Multiple limits can be stacked:

```python
@limiter.limit("5/second;100/hour")
```

## Rate Limit Key

Currently keyed by **remote IP** (`get_remote_address`). To key by authenticated user instead (recommended once Keycloak is fully set up):

```python
from slowapi.util import get_remote_address

def get_user_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    return user["sub"] if user else get_remote_address(request)

limiter = Limiter(key_func=get_user_id)
```

Then update `auth.py` to store the token payload on `request.state.user` inside `require_auth`.

## Response on Limit Exceeded

Returns `HTTP 429 Too Many Requests`:

```json
{"error": "Rate limit exceeded: 30 per 1 minute"}
```

Handled globally by `_rate_limit_exceeded_handler` registered in `main.py`.
