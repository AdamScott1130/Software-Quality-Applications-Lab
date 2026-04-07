# db-tests/tests/test_user_session_created.py

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
    Perform a Resource Owner Password Credentials (ROPC) login for the
    test user. Returns the full token response JSON.
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


def _get_user_sessions(admin_token: str, user_id: str) -> list:
    """
    Fetch active sessions for a user via the Keycloak Admin API.
    GET /admin/realms/{realm}/users/{user_id}/sessions
    Returns a list of session objects (may be empty).
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
def test_tc_db_04_login_creates_user_session(admin_token, created_user):
    """
    TC-DB-04: Verify login creates a user session (US-004)

    Note on storage:
      Keycloak 17+ running in start-dev mode stores sessions in Infinispan
      (in-memory cache) rather than writing them to the PostgreSQL user_session
      table. The table will always be empty in this setup. Session existence is
      therefore validated through the Keycloak Admin API, which reads directly
      from the same Infinispan store that Keycloak itself uses — this is the
      authoritative source of truth for active sessions.

    Flow:
      1. Set a password for the test user (Admin API — setup only).
      2. Record the time just before login (for recency check).
      3. Log in as the test user via token endpoint (triggers session creation).
      4. Wait briefly for Keycloak to register the session.
      5. Fetch active sessions via Admin API.
      6. Assert session exists with correct fields and recent start time.
    """
    base_url = _env("KEYCLOAK_BASE_URL")
    realm = os.getenv("KEYCLOAK_REALM", "master")

    username = created_user["username"]
    user_id = created_user["id"]
    test_password = "TC_DB04_P@ssw0rd!"

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
    # Step 2 — Record time just before login (epoch seconds)
    #          Keycloak Admin API returns session 'start' in epoch seconds
    # ------------------------------------------------------------------ #
    login_time_s = int(time.time())

    # ------------------------------------------------------------------ #
    # Step 3 — Log in as the test user (this triggers session creation)
    # ------------------------------------------------------------------ #
    _login_as_user(username=username, password=test_password)

    # ------------------------------------------------------------------ #
    # Step 4 — Brief pause to allow Keycloak to register the session
    # ------------------------------------------------------------------ #
    time.sleep(2)

    # ------------------------------------------------------------------ #
    # Step 5 — Fetch active sessions via Admin API
    # ------------------------------------------------------------------ #
    sessions = _get_user_sessions(admin_token=admin_token, user_id=user_id)

    # ------------------------------------------------------------------ #
    # Step 6 — Assertions
    # ------------------------------------------------------------------ #

    # 6a — At least one session must exist after login
    assert len(sessions) > 0, (
        f"No active sessions found for user '{username}' (id={user_id}) "
        f"after successful login. Expected at least 1 session."
    )

    # 6b — Grab the most recent session (sorted by 'start' descending)
    latest_session = sorted(sessions, key=lambda s: s.get("start", 0), reverse=True)[0]

    # 6c — Session must have an ID (non-empty string)
    session_id = latest_session.get("id")
    assert session_id and len(str(session_id)) > 0, (
        "Session 'id' is missing or empty — expected a UUID string."
    )

    # 6d — Session must be linked to the correct user
    assert latest_session.get("userId") == user_id, (
        f"Session userId mismatch. "
        f"Expected: {user_id}, Got: {latest_session.get('userId')}"
    )

    # 6e — Session username must match
    assert latest_session.get("username") == username, (
        f"Session username mismatch. "
        f"Expected: '{username}', Got: '{latest_session.get('username')}'"
    )

    # 6f — 'start' timestamp must be present and recent (within 60s of login)
    session_start = latest_session.get("start")
    assert session_start is not None, (
        "Session 'start' field is missing — expected an epoch timestamp."
    )

    sixty_seconds = 60
    assert session_start >= (login_time_s - sixty_seconds), (
        f"Session 'start' ({session_start}) is older than 60 seconds "
        f"before login (login_time_s={login_time_s}). "
        f"This session may not belong to this test run."
    )

    # 6g — Session must reference at least one active client
    clients = latest_session.get("clients", {})
    assert len(clients) > 0, (
        "Session 'clients' is empty — expected at least one active client."
    )
    assert "admin-cli" in clients.values(), (
        f"Expected 'admin-cli' in session clients, got: {clients}"
    )

    print(
        f"\n[TC-DB-04] PASS — Session confirmed for '{username}':\n"
        f"  session_id : {session_id}\n"
        f"  userId     : {latest_session.get('userId')}\n"
        f"  start      : {session_start}\n"
        f"  ipAddress  : {latest_session.get('ipAddress', 'n/a')}\n"
        f"  clients    : {latest_session.get('clients', {})}"
    )