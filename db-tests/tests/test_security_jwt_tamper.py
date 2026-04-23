# db-tests/tests/test_security_jwt_tamper.py
#
# TC-SEC-01: JWT token tampering is rejected by Keycloak
# Security test — validates that a structurally valid but tampered JWT
# is rejected with 401 Unauthorized on a protected endpoint.
#
# Run:  pytest tests/test_security_jwt_tamper.py -v
#       pytest -m security -v

import os
import base64
import json
import requests
import pytest
from src.keycloak_api import get_admin_token


def _base_url() -> str:
    return os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080").rstrip("/")


def _realm() -> str:
    return os.getenv("KEYCLOAK_REALM", "master")


def _pad(b64: str) -> str:
    """Add back base64 padding that JWTs strip out."""
    return b64 + "=" * (4 - len(b64) % 4)


def _tamper_jwt(token: str) -> str:
    """
    Decode the JWT payload, modify a claim, re-encode, and reassemble.
    The signature is left UNCHANGED — so the token is structurally valid
    but cryptographically invalid. Keycloak must reject it.
    """
    parts = token.split(".")
    assert len(parts) == 3, "Token does not look like a JWT (expected 3 parts)"

    header, payload_b64, signature = parts

    # Decode payload
    payload_json = base64.urlsafe_b64decode(_pad(payload_b64)).decode("utf-8")
    payload = json.loads(payload_json)

    # Tamper: modify the preferred_username claim
    original_username = payload.get("preferred_username", "admin")
    payload["preferred_username"] = "hacker"
    payload["sub"] = "00000000-0000-0000-0000-000000000000"  # fake subject UUID

    # Re-encode payload (no padding, as per JWT spec)
    tampered_json = json.dumps(payload, separators=(",", ":"))
    tampered_b64 = base64.urlsafe_b64encode(tampered_json.encode()).decode().rstrip("=")

    # Reassemble with ORIGINAL signature — signature no longer matches payload
    tampered_token = f"{header}.{tampered_b64}.{signature}"

    return tampered_token, original_username


@pytest.mark.security
def test_tc_sec_01_tampered_jwt_is_rejected():
    """
    TC-SEC-01: Tampered JWT token is rejected with 401 Unauthorized.

    Steps:
    1) Obtain a valid admin access token via the token endpoint
    2) Tamper with the JWT payload (modify username + subject claims)
    3) Keep the original signature intact (signature no longer matches)
    4) Send a request to a protected Admin API endpoint using the tampered token
    5) Assert 401 Unauthorized — Keycloak must detect the invalid signature

    This validates that Keycloak enforces JWT signature verification and
    cannot be bypassed by manipulating token claims directly.
    """

    base = _base_url()
    realm = _realm()

    # ── Step 1: Obtain a valid token ──
    token_url = f"{base}/realms/{realm}/protocol/openid-connect/token"
    r = requests.post(
        token_url,
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": os.getenv("KEYCLOAK_ADMIN_USER", "admin"),
            "password": os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin"),
        },
        timeout=20,
    )
    assert r.status_code == 200, f"Could not obtain token for tampering test: {r.text}"
    valid_token = r.json()["access_token"]

    # ── Step 2: Tamper with the JWT payload ──
    tampered_token, original_username = _tamper_jwt(valid_token)

    assert tampered_token != valid_token, "Tampering did not modify the token"

    # ── Step 3: Send request with tampered token to a protected endpoint ──
    protected_url = f"{base}/admin/realms/{realm}/users"
    headers = {"Authorization": f"Bearer {tampered_token}"}
    r = requests.get(protected_url, headers=headers, timeout=20)

    # ── Step 4: Assert rejection ──
    assert r.status_code == 401, (
        f"TC-SEC-01 FAILED: Expected 401 Unauthorized for tampered JWT, "
        f"got {r.status_code}. "
        f"Original username was '{original_username}', tampered to 'hacker'. "
        "Keycloak accepted a token with an invalid signature — this is a critical security failure."
    )