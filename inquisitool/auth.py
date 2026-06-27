import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from inquisitool.constants import KEYCLOAK_REALM, KEYCLOAK_URL

bearer = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)

_jwks_cache: dict = {}


async def _get_jwks() -> dict:
    if not _jwks_cache:
        url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            resp.raise_for_status()
            _jwks_cache.update(resp.json())
    return _jwks_cache


async def require_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    token = credentials.credentials
    try:
        jwks = await _get_jwks()
        header = jwt.get_unverified_header(token)
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if key is None:
            raise HTTPException(status_code=401, detail="Unknown signing key")
        issuer = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
        payload = jwt.decode(token, key, algorithms=[header["alg"]], options={"verify_aud": False}, issuer=issuer)
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def get_current_user(request: Request) -> dict:
    """Retrieve the token payload stored on the request state (set by require_auth)."""
    return request.state.user
