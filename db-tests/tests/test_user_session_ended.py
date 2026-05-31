# db-tests/tests/test_user_session_ended.py

import os
import time
import pytest
import requests

from src.keycloak_api import reset_user_password


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _login_as_user(username: str, password: str) -> dict:
    """
    Log in as the test user via ROPC grant.
    Returns full token response JSON including refresh_token.
    """
    base = _env("KEYCLOAK_BASE_URL").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "master")
    url = f"{base}/realms/{realm}/protocol/openid-connect/token"

    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": username,
        "password": password,
    }

    response = requests.post(url, data=data, timeout=20)
    assert response.status_code == 200, (
        f"Login failed for '{username}': "
        f"{response.status_code} — {response.text}"
    )
    return response.json()


def _logout_user(refresh_token: str) -> None:
    """
    Logout the user by invalidating their refresh token.
    POST /realms/{realm}/protocol/openid-connect/logout
    Keycloak returns 204 No Content on success.
    """
    base = _env("KEYCLOAK_BASE_URL").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "master")
    url = f"{base}/realms/{realm}/protocol/openid-connect/logout"

    data = {
        "client_id": "admin-cli",
        "refresh_token": refresh_token,
    }

    response = requests.post(url, data=data, timeout=20)
    assert response.status_code in (200, 204), (
        f"Logout failed: {response.status_code} — {response.text}"
    )


def _get_user_sessions(admin_token: str, user_id: str) -> list:
    """
    Fetch active sessions for a user via the Keycloak Admin API.
    GET /admin/realms/{realm}/users/{user_id}/sessions
    Returns a list of session objects (empty list means no active sessions).
    """
    base = _env("KEYCLOAK_BASE_URL").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "master")
    url = f"{base}/admin/realms/{realm}/users/{user_id}/sessions"

    response = requests.get(url, headers=_headers(admin_token), timeout=20)
    assert response.status_code == 200, (
        f"Failed to fetch sessions for user_id '{user_id}': "
        f"{response.status_code} — {response.text}"
    )
    return response.json()


@pytest.mark.db
def test_tc_db_05_logout_ends_user_session(admin_token, created_user):
    """
    TC-DB-05: Verify logout removes/ends session (US-005) — Database

    Note on storage:
      Same as TC-DB-04 — Keycloak 17+ in start-dev mode holds sessions in
      Infinispan, not PostgreSQL. The Admin API is the authoritative source
      for active session state and is used for all assertions here.

    Flow:
      1. Set a password for the test user (Admin API — setup only).
      2. Log in as the test user — confirms a session is created (pre-condition).
      3. Verify session exists before logout (pre-condition assertion).
      4. Logout using the refresh token from the login response.
      5. Wait briefly for Keycloak to invalidate the session.
      6. Fetch sessions again and assert the list is now empty.
    """
    base_url = _env("KEYCLOAK_BASE_URL")
    realm = os.getenv("KEYCLOAK_REALM", "master")

    username = created_user["username"]
    user_id = created_user["id"]
    test_password = "TC_DB05_P@ssw0rd!"

    # ------------------------------------------------------------------ #
    # Step 1 — Set password via Admin API (setup, not under test)
    # ------------------------------------------------------------------ #
    reset_user_password(
        base_url=base_url,
        realm=realm,
        user_id=user_id,
        admin_token=admin_token,
        password=test_password,
        temporary=False,
    )

    # ------------------------------------------------------------------ #
    # Step 2 — Log in as the test user to create a session
    # ------------------------------------------------------------------ #
    token_response = _login_as_user(username=username, password=test_password)
    refresh_token = token_response.get("refresh_token")

    assert refresh_token, (
        "Login response did not include a refresh_token — "
        "cannot proceed with logout test."
    )

    # Allow Keycloak to register the session
    time.sleep(2)

    # ------------------------------------------------------------------ #
    # Step 3 — Pre-condition: confirm session exists before logout
    # ------------------------------------------------------------------ #
    sessions_before = _get_user_sessions(admin_token=admin_token, user_id=user_id)

    assert len(sessions_before) > 0, (
        f"Pre-condition failed: no active session found for '{username}' "
        f"after login. Cannot verify logout behaviour."
    )

    session_id_before = sessions_before[0].get("id")
    print(
        f"\n[TC-DB-05] Pre-logout session confirmed: {session_id_before}"
    )

    # ------------------------------------------------------------------ #
    # Step 4 — Logout using the refresh token
    # ------------------------------------------------------------------ #
    _logout_user(refresh_token=refresh_token)

    # ------------------------------------------------------------------ #
    # Step 5 — Wait for Keycloak to invalidate the session
    # ------------------------------------------------------------------ #
    time.sleep(2)

    # ------------------------------------------------------------------ #
    # Step 6 — Assertions: session must no longer exist
    # ------------------------------------------------------------------ #
    sessions_after = _get_user_sessions(admin_token=admin_token, user_id=user_id)

    assert len(sessions_after) == 0, (
        f"Session for user '{username}' still active after logout. "
        f"Expected 0 sessions, found {len(sessions_after)}. "
        f"Session IDs still present: {[s.get('id') for s in sessions_after]}"
    )

    print(
        f"[TC-DB-05] PASS — Session '{session_id_before}' successfully "
        f"ended for user '{username}' after logout."
    )