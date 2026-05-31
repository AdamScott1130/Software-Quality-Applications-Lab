# db-tests/tests/test_no_orphan_sessions.py

import os
import pytest
import requests

from src.db import get_conn


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


def _get_all_realm_users(admin_token: str) -> list:
    """
    Fetch all users in the realm via Admin API.
    GET /admin/realms/{realm}/users?max=1000
    Returns a list of user objects.
    """
    base = _env("KEYCLOAK_BASE_URL").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "master")
    url = f"{base}/admin/realms/{realm}/users"

    response = requests.get(
        url,
        headers=_headers(admin_token),
        params={"max": 1000},
        timeout=20,
    )
    assert response.status_code == 200, (
        f"Failed to fetch realm users: "
        f"{response.status_code} — {response.text}"
    )
    return response.json()


def _get_active_sessions_for_user(admin_token: str, user_id: str) -> list:
    """
    Fetch active sessions for a single user via Admin API.
    GET /admin/realms/{realm}/users/{user_id}/sessions
    Returns a list of session objects (empty if no active sessions).
    """
    base = _env("KEYCLOAK_BASE_URL").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "master")
    url = f"{base}/admin/realms/{realm}/users/{user_id}/sessions"

    response = requests.get(url, headers=_headers(admin_token), timeout=20)
    if response.status_code == 404:
        return []
    assert response.status_code == 200, (
        f"Failed to fetch sessions for user_id '{user_id}': "
        f"{response.status_code} — {response.text}"
    )
    return response.json()


def _get_all_user_entity_ids() -> set:
    """
    Fetch all user UUIDs directly from the PostgreSQL user_entity table.
    This is the source of truth for users that actually exist in the DB.
    """
    query = "SELECT id FROM user_entity;"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
    return {row["id"] for row in rows}


@pytest.mark.db
def test_tc_db_08_no_orphan_sessions(admin_token):
    """
    TC-DB-08: Verify no orphan sessions exist (US-004) — Database

    An orphan session is an active session whose userId does not correspond
    to any existing user in the user_entity table. This would indicate a
    data integrity issue — a session persisting for a deleted or non-existent
    user.

    Note on storage:
      Keycloak 17+ in start-dev mode stores sessions in Infinispan, not
      PostgreSQL. The Admin API is used to retrieve active sessions and
      the DB is queried for the authoritative list of existing user IDs.
      A session is considered orphaned if its userId does not appear in
      user_entity.

    Flow:
      1. Fetch all known user IDs from PostgreSQL user_entity (DB).
      2. Fetch all users from the Keycloak realm (Admin API).
      3. For each realm user, fetch their active sessions (Admin API).
      4. For each active session, verify the session userId exists in
         the user_entity table.
      5. Assert zero orphan sessions found.
    """

    # ------------------------------------------------------------------ #
    # Step 1 — Fetch all valid user IDs from PostgreSQL user_entity
    # ------------------------------------------------------------------ #
    valid_user_ids = _get_all_user_entity_ids()

    print(
        f"\n[TC-DB-08] Found {len(valid_user_ids)} user(s) in user_entity table."
    )

    # ------------------------------------------------------------------ #
    # Step 2 — Fetch all users from the Keycloak realm
    # ------------------------------------------------------------------ #
    realm_users = _get_all_realm_users(admin_token=admin_token)

    print(
        f"[TC-DB-08] Found {len(realm_users)} user(s) in Keycloak realm."
    )

    # ------------------------------------------------------------------ #
    # Step 3 & 4 — For each realm user, check their active sessions
    # ------------------------------------------------------------------ #
    orphan_sessions = []
    total_sessions_checked = 0

    for user in realm_users:
        user_id = user.get("id")
        username = user.get("username", "unknown")

        sessions = _get_active_sessions_for_user(
            admin_token=admin_token,
            user_id=user_id,
        )

        for session in sessions:
            total_sessions_checked += 1
            session_user_id = session.get("userId")

            # An orphan is a session whose userId is not in user_entity
            if session_user_id not in valid_user_ids:
                orphan_sessions.append({
                    "session_id": session.get("id"),
                    "session_userId": session_user_id,
                    "fetched_under_username": username,
                })

    print(
        f"[TC-DB-08] Checked {total_sessions_checked} active session(s) "
        f"across {len(realm_users)} realm user(s)."
    )

    # ------------------------------------------------------------------ #
    # Step 5 — Assert no orphan sessions found
    # ------------------------------------------------------------------ #
    assert len(orphan_sessions) == 0, (
        f"Found {len(orphan_sessions)} orphan session(s) — sessions whose "
        f"userId does not exist in user_entity:\n"
        + "\n".join(
            f"  session_id={s['session_id']}, "
            f"userId={s['session_userId']}, "
            f"fetched_under={s['fetched_under_username']}"
            for s in orphan_sessions
        )
    )

    print(
        f"[TC-DB-08] PASS — No orphan sessions found. "
        f"All {total_sessions_checked} active session(s) reference valid users."
    )