# db-tests/tests/test_int_login_verify_session.py
#
# TC-INT-03: Login via token endpoint and verify session via Admin API
# Integration test — API layer (token endpoint login) → API layer (Admin session endpoint)
#
# NOTE: Keycloak running in start-dev mode stores sessions IN MEMORY, not in
# PostgreSQL. Direct queries on user_session return 0 rows even after a
# successful login. Session existence is validated via the Admin API instead.
#
# Run:  pytest tests/test_int_login_verify_session.py -v
#       pytest -m integration -v

import os
import time
import requests
import pytest
from src.keycloak_api import get_admin_token, reset_user_password


def _login_as_user(base_url: str, realm: str, username: str, password: str) -> dict:
    """
    Perform a Resource Owner Password Credentials (ROPC) login
    for a regular user and return the full token response.
    """
    url = f"{base_url}/realms/{realm}/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": username,
        "password": password,
    }
    r = requests.post(url, data=data, timeout=20)
    r.raise_for_status()
    return r.json()


@pytest.mark.integration
def test_int_login_verify_session(created_user):
    """
    TC-INT-03: Login via token endpoint and verify session via Admin API.

    Steps:
    1) Use created_user fixture to get a live Keycloak user
    2) Set a known password via Admin API (required before user can log in)
    3) Login as that user via the token endpoint
    4) Assert HTTP 200 and access_token returned
    5) Query active sessions via Admin API GET /users/{id}/sessions
    6) Assert at least one session exists for the user
    7) Assert the session belongs to the correct user (userId matches)

    Why Admin API and not DB:
    Keycloak in start-dev mode stores sessions in-memory only.
    The user_session table in PostgreSQL remains empty even after a
    successful login. The Admin API is the correct verification layer here.
    """

    base_url = os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "master")
    password = "IntSession_P@ss1!"

    username = created_user["username"]
    user_id = created_user["id"]

    # ── Step 1: Set password so user can authenticate ──
    admin_token = get_admin_token()
    reset_user_password(
        base_url=base_url,
        realm=realm,
        user_id=user_id,
        admin_token=admin_token,
        password=password,
        temporary=False,
    )

    # Small buffer to allow Keycloak to process the password update
    time.sleep(1)

    # ── Step 2: Login via token endpoint ──
    token_response = _login_as_user(base_url, realm, username, password)

    assert "access_token" in token_response, (
        "Login did not return an access_token. "
        "Check that the user exists and password was set correctly."
    )

    # ── Step 3: Verify session via Admin API ──
    # start-dev mode does not persist sessions to PostgreSQL,
    # so we verify via the Admin API session endpoint instead.
    sessions_url = f"{base_url}/admin/realms/{realm}/users/{user_id}/sessions"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }
    r = requests.get(sessions_url, headers=headers, timeout=20)

    assert r.status_code == 200, (
        f"Failed to retrieve sessions from Admin API: {r.status_code} {r.text}"
    )

    sessions = r.json()

    # ── Step 4: Assert session row exists ──
    assert len(sessions) >= 1, (
        f"No active session found for user '{username}' (id={user_id}) after login. "
        "Expected at least one session from the Admin API."
    )

    # ── Step 5: Assert session belongs to the correct user ──
    assert sessions[0]["userId"] == user_id, (
        f"Session userId mismatch. Expected '{user_id}', "
        f"got '{sessions[0].get('userId')}'"
    )