#!/usr/bin/env python3
"""
Dev-only script to generate a Keycloak access token via client_credentials grant.
Do NOT use in production — client secrets should never be in scripts or shell history there.

Usage:
    python scripts/get_token.py
    python scripts/get_token.py --env .env.staging
    python scripts/get_token.py --raw        # print token only, useful for piping
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def load_env(env_file: str) -> None:
    path = Path(env_file)
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def get_token(keycloak_url: str, realm: str, client_id: str, client_secret: str) -> dict:
    url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/token"
    data = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ Could not reach Keycloak at {keycloak_url}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Keycloak dev token")
    parser.add_argument("--env", default=".env", help="Path to .env file (default: .env)")
    parser.add_argument("--raw", action="store_true", help="Print access token only")
    args = parser.parse_args()

    load_env(args.env)

    keycloak_url = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
    realm = os.environ.get("KEYCLOAK_REALM", "inquisitool")
    client_id = os.environ.get("KEYCLOAK_CLIENT_ID") or _prompt("Client ID")
    client_secret = os.environ.get("KEYCLOAK_CLIENT_SECRET") or _prompt("Client secret", secret=True)

    result = get_token(keycloak_url, realm, client_id, client_secret)

    if args.raw:
        print(result["access_token"])
        return

    expires_in = result.get("expires_in", "?")
    print(f"\n✅ Token acquired (expires in {expires_in}s)\n")
    print(f"Authorization: Bearer {result['access_token']}\n")
    print("── Curl example ──────────────────────────────────────────")
    print(f'curl http://localhost:8000/campaigns/ -H "Authorization: Bearer {result["access_token"]}"')


def _prompt(label: str, secret: bool = False) -> str:
    if secret:
        import getpass

        return getpass.getpass(f"{label}: ")
    return input(f"{label}: ")


if __name__ == "__main__":
    main()
