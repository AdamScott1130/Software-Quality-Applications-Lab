# db-tests/tests/test_int_logout_invalidates_session.py
#
# TC-INT-04: Logout invalidates refresh token and ends session
# Integration test — chains three API interactions:
#   Layer 1: Token endpoint  → login, get refresh_token
#   Layer 2: Admin API       → logout (invalidate session server-side)
#   Layer 3: Token endpoint  → attempt refresh, assert rejected
#
# WHY THIS IS AN INTEGRATION TEST:
#   This test does not test any single endpoint in isolation.
#   It validates that a state change triggered in one API layer
#   (logout via Admin API) correctly propagates to another layer
#   (token endpoint), making the refresh token unusable.
#   The result of step 2 must affect the behaviour of step 3 —
#   that cross-layer dependency is what makes this an integration test.
#
# NOTE on DB session check:
#   TC-INT-04 originally included a DB query on user_session to verify
#   the session was removed. This is not possible in start-dev mode
#   (Keycloak stores sessions in-memory, not PostgreSQL). The session
#   invalidation is instead confirmed via the token endpoint behaviour:
#   a valid refresh token becoming invalid after logout is observable
#   proof that the session was ended server-side.
#
# Run:  pytest tests/test_int_logout_invalidates_session.py -v
#       pytest -m integration -v

import os
import time
import requests
import pytest
from src.keycloak_api import get_admin_token, reset_user_password


def _base_url() -> str:
    return os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080").rstrip("/")


def _realm() -> str:
    return os.getenv("KEYCLOAK_REALM", "master")


def _admin_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@pytest.mark.integration
def test_int_logout_invalidates_session(created_user):
    """
    TC-INT-04: Logout invalidates refresh token and ends session.

    Integration chain (three layers):
      1) Token endpoint   — login as user, capture refresh_token
      2) Admin API        — logout user server-side (session invalidated)
      3) Token endpoint   — attempt refresh using captured token → must fail

    This validates that session invalidation in the Admin API layer
    propagates correctly to the Auth API layer. A refresh token that
    was valid before logout must be rejected after logout.

    Layers crossed: Auth API → Session Management API → Auth API
    """
    base = _base_url()
    realm = _realm()
    password = "IntLogout_P@ss1!"
    username = created_user["username"]
    user_id = created_user["id"]

    # ── Step 1: Set password so the user can log in ──
    admin_token = get_admin_token()
    reset_user_password(
        base_url=base,
        realm=realm,
        user_id=user_id,
        admin_token=admin_token,
        password=password,
        temporary=False,
    )
    time.sleep(1)

    # ── Step 2: Login — capture the refresh token ──
    # Layer 1: Token endpoint creates a session and issues a refresh token
    token_url = f"{base}/realms/{realm}/protocol/openid-connect/token"
    r = requests.post(
        token_url,
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": username,
            "password": password,
        },
        timeout=20,
    )
    assert r.status_code == 200, (
        f"TC-INT-04 FAILED at Step 2: Login failed: {r.status_code} {r.text}"
    )
    refresh_token = r.json().get("refresh_token")
    assert refresh_token, "TC-INT-04 FAILED at Step 2: No refresh_token in login response"

    # ── Step 3: Logout via Admin API ──
    # Layer 2: Admin API invalidates the session server-side
    logout_url = f"{base}/admin/realms/{realm}/users/{user_id}/logout"
    r = requests.post(
        logout_url,
        headers=_admin_headers(admin_token),
        timeout=20,
    )
    assert r.status_code == 204, (
        f"TC-INT-04 FAILED at Step 3: Logout failed: {r.status_code} {r.text}"
    )

    # ── Step 4: Attempt token refresh using the now-invalidated token ──
    # Layer 3: Token endpoint must reject the refresh token
    # because the session was ended in Layer 2
    r = requests.post(
        token_url,
        data={
            "grant_type": "refresh_token",
            "client_id": "admin-cli",
            "refresh_token": refresh_token,
        },
        timeout=20,
    )

    # ── Step 5: Assert the refresh was rejected ──
    assert r.status_code == 400, (
        f"TC-INT-04 FAILED at Step 5: Expected 400 after logout, got {r.status_code}. "
        "Refresh token should have been invalidated by logout but was accepted."
    )

    error_body = r.json()
    assert error_body.get("error") == "invalid_grant", (
        f"TC-INT-04 FAILED: Expected error='invalid_grant', got '{error_body.get('error')}'"
    )
    assert "Session not active" in error_body.get("error_description", ""), (
        f"TC-INT-04 FAILED: Expected 'Session not active' in error_description, "
        f"got: '{error_body.get('error_description')}'"
    )