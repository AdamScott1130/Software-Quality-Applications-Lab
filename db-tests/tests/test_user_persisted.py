# db-tests/tests/test_user_attributes_persisted.py

import os
import time
import pytest
import requests

from src.db import get_conn, get_user_entity_id


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


def _create_user_with_attributes(admin_token: str, username: str, email: str, attributes: dict) -> str:
    """
    Create a Keycloak user with custom attributes via Admin API.
    Returns the created user's ID.
    """
    base = _env("KEYCLOAK_BASE_URL").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "master")
    url = f"{base}/admin/realms/{realm}/users"

    payload = {
        "username": username,
        "email": email,
        "enabled": True,
        "attributes": attributes,
    }

    response = requests.post(url, json=payload, headers=_headers(admin_token), timeout=20)
    assert response.status_code == 201, (
        f"Failed to create user '{username}' with attributes: "
        f"{response.status_code} — {response.text}"
    )

    # Retrieve the created user's ID
    search_url = f"{base}/admin/realms/{realm}/users"
    r = requests.get(
        search_url,
        params={"username": username},
        headers=_headers(admin_token),
        timeout=20,
    )
    r.raise_for_status()
    users = r.json()
    assert users, f"User '{username}' not found after creation."
    return users[0]["id"]


def _create_user_without_attributes(admin_token: str, username: str, email: str) -> str:
    """
    Create a Keycloak user without any custom attributes via Admin API.
    Returns the created user's ID.
    """
    base = _env("KEYCLOAK_BASE_URL").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "master")
    url = f"{base}/admin/realms/{realm}/users"

    payload = {
        "username": username,
        "email": email,
        "enabled": True,
    }

    response = requests.post(url, json=payload, headers=_headers(admin_token), timeout=20)
    assert response.status_code == 201, (
        f"Failed to create user '{username}': "
        f"{response.status_code} — {response.text}"
    )

    search_url = f"{base}/admin/realms/{realm}/users"
    r = requests.get(
        search_url,
        params={"username": username},
        headers=_headers(admin_token),
        timeout=20,
    )
    r.raise_for_status()
    users = r.json()
    assert users, f"User '{username}' not found after creation."
    return users[0]["id"]


def _delete_user(admin_token: str, user_id: str) -> None:
    """
    Delete a user via Admin API. Used for cleanup in finally blocks.
    """
    base = _env("KEYCLOAK_BASE_URL").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "master")
    url = f"{base}/admin/realms/{realm}/users/{user_id}"
    requests.delete(url, headers=_headers(admin_token), timeout=20)


def _get_user_attributes_from_db(username: str) -> list:
    """
    Query user_attribute table joined to user_entity for a given username.
    Returns a list of dicts with 'name' and 'value' keys.
    """
    query = """
        SELECT ua.name, ua.value
        FROM user_attribute ua
        JOIN user_entity ue ON ue.id = ua.user_id
        WHERE ue.username = %s;
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (username,))
            return cur.fetchall()


@pytest.mark.db
def test_tc_db_02_user_attributes_persisted_when_set(admin_token):
    """
    TC-DB-02 (Scenario A): Verify user attributes are persisted in
    user_attribute table when attributes are provided during user creation.

    Flow:
      1. Create a user with custom attributes via Admin API.
      2. Query user_attribute joined to user_entity in PostgreSQL.
      3. Assert the expected attribute name/value pairs are present.
      4. Cleanup — delete the test user.
    """
    suffix = int(time.time())
    username = f"attr_user_{suffix}"
    email = f"{username}@example.com"

    # Attributes to set on the user
    expected_attributes = {
        "department": "QA",
        "employeeId": "EMP-9999",
    }

    user_id = None
    try:
        # ------------------------------------------------------------------ #
        # Step 1 — Create user with attributes via Admin API
        # ------------------------------------------------------------------ #
        user_id = _create_user_with_attributes(
            admin_token=admin_token,
            username=username,
            email=email,
            attributes=expected_attributes,
        )

        print(
            f"\n[TC-DB-02A] User '{username}' created with attributes: "
            f"{expected_attributes}"
        )

        # ------------------------------------------------------------------ #
        # Step 2 — Query user_attribute table in PostgreSQL
        # ------------------------------------------------------------------ #
        rows = _get_user_attributes_from_db(username=username)

        # ------------------------------------------------------------------ #
        # Step 3 — Assertions
        # ------------------------------------------------------------------ #

        # 3a — Rows must exist (attributes were set, so DB must have them)
        assert len(rows) > 0, (
            f"No rows found in user_attribute for user '{username}'. "
            f"Expected attributes to be persisted."
        )

        # 3b — Build a dict of what the DB returned for easy comparison
        db_attributes = {row["name"]: row["value"] for row in rows}

        # 3c — Each expected attribute must be present with the correct value
        for attr_name, attr_value in expected_attributes.items():
            assert attr_name in db_attributes, (
                f"Attribute '{attr_name}' not found in user_attribute table. "
                f"DB returned: {db_attributes}"
            )
            assert db_attributes[attr_name] == attr_value, (
                f"Attribute '{attr_name}' value mismatch. "
                f"Expected: '{attr_value}', Got: '{db_attributes[attr_name]}'"
            )

        print(
            f"[TC-DB-02A] PASS — Attributes persisted correctly in DB: "
            f"{db_attributes}"
        )

    finally:
        # ------------------------------------------------------------------ #
        # Step 4 — Cleanup
        # ------------------------------------------------------------------ #
        if user_id:
            _delete_user(admin_token=admin_token, user_id=user_id)


@pytest.mark.db
def test_tc_db_02_no_attributes_when_none_set(admin_token):
    """
    TC-DB-02 (Scenario B): Verify that when no attributes are provided
    during user creation, zero rows exist in user_attribute for that user.

    Flow:
      1. Create a user without any custom attributes via Admin API.
      2. Query user_attribute joined to user_entity in PostgreSQL.
      3. Assert zero rows are returned.
      4. Cleanup — delete the test user.
    """
    suffix = int(time.time()) + 1  # +1 to avoid collision with Scenario A
    username = f"noattr_user_{suffix}"
    email = f"{username}@example.com"

    user_id = None
    try:
        # ------------------------------------------------------------------ #
        # Step 1 — Create user without attributes via Admin API
        # ------------------------------------------------------------------ #
        user_id = _create_user_without_attributes(
            admin_token=admin_token,
            username=username,
            email=email,
        )

        print(
            f"\n[TC-DB-02B] User '{username}' created without attributes."
        )

        # ------------------------------------------------------------------ #
        # Step 2 — Query user_attribute table in PostgreSQL
        # ------------------------------------------------------------------ #
        rows = _get_user_attributes_from_db(username=username)

        # ------------------------------------------------------------------ #
        # Step 3 — Assertions
        # ------------------------------------------------------------------ #

        # 3a — Zero rows is expected and acceptable per TC-DB-02 design
        assert len(rows) == 0, (
            f"Expected 0 attribute rows for user '{username}' (no attributes set), "
            f"but found {len(rows)}: {[dict(r) for r in rows]}"
        )

        print(
            f"[TC-DB-02B] PASS — No attribute rows found in DB for '{username}' "
            f"as expected (none were set during creation)."
        )

    finally:
        # ------------------------------------------------------------------ #
        # Step 4 — Cleanup
        # ------------------------------------------------------------------ #
        if user_id:
            _delete_user(admin_token=admin_token, user_id=user_id)