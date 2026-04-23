# db-tests/tests/test_int_role_assignment_db_and_claims.py
#
# TC-INT-05: Role assignment reflected in DB and retrievable via Admin API
# Integration test — chains three system layers:
#   Layer 1: Admin API POST → assign realm role to user
#   Layer 2: Database       → verify user_role_mapping table reflects assignment
#   Layer 3: Admin API GET  → confirm role retrievable via role-mappings endpoint
#
# WHY THIS IS AN INTEGRATION TEST:
#   This test validates the full role assignment pipeline end-to-end.
#   An administrative write (role assignment) must persist to the database
#   AND be retrievable through a separate API read. Each layer is independently
#   verifiable, but the test validates the contract between all three.
#
#   Compare to unit tests:
#   - TC-DB-06 (unit): directly inserts a role mapping in SQL and reads it back
#   - TC-API-08 (unit): calls the role assignment endpoint, checks HTTP 204
#   - TC-INT-05 (this): calls the API, confirms the DB, then reads back via a
#     separate API endpoint — three layers, one chain
#
# NOTE on JWT claims approach:
#   An earlier version verified the role in JWT realm_access claims.
#   This failed because admin-cli tokens do not include realm_access by default
#   — this is a Keycloak client scope configuration, not a bug.
#   The Admin API role-mappings GET endpoint is the authoritative verification.
#
# Run:  pytest tests/test_int_role_assignment_db_and_claims.py -v
#       pytest -m integration -v

import os
import requests
import pytest
from src.keycloak_api import get_admin_token
from src.db import fetch_one


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
def test_int_role_assignment_db_and_claims(created_user):
    """
    TC-INT-05: Role assignment reflected in DB and retrievable via Admin API.

    Integration chain (three layers):
      1) Admin API POST — assign realm role 'offline_access' to user
      2) Database       — query user_role_mapping to confirm DB persistence
      3) Admin API GET  — retrieve role-mappings, confirm role is present

    Layers crossed: Admin API (write) → PostgreSQL user_role_mapping → Admin API (read)
    """
    base = _base_url()
    realm = _realm()
    username = created_user["username"]
    user_id = created_user["id"]

    # ── Step 1: Get admin token ──
    admin_token = get_admin_token()

    # ── Step 2: Look up the 'offline_access' realm role ──
    roles_url = f"{base}/admin/realms/{realm}/roles/offline_access"
    r = requests.get(roles_url, headers=_admin_headers(admin_token), timeout=20)
    assert r.status_code == 200, (
        f"TC-INT-05 FAILED at Step 2: Could not retrieve role 'offline_access': "
        f"{r.status_code} {r.text}"
    )
    role = r.json()
    role_id = role["id"]
    role_name = role["name"]

    # ── Step 3: Assign realm role to user via Admin API ──
    # Layer 1: Admin API write
    assign_url = f"{base}/admin/realms/{realm}/users/{user_id}/role-mappings/realm"
    r = requests.post(
        assign_url,
        json=[{"id": role_id, "name": role_name}],
        headers=_admin_headers(admin_token),
        timeout=20,
    )
    assert r.status_code == 204, (
        f"TC-INT-05 FAILED at Step 3: Role assignment failed: {r.status_code} {r.text}"
    )

    # ── Step 4: Verify role mapping persisted in the database ──
    # Layer 2: DB read — confirms the Admin API write reached PostgreSQL
    row = fetch_one(
        """
        SELECT u.username, r.name AS role_name
        FROM user_entity u
        JOIN user_role_mapping m ON u.id = m.user_id
        JOIN keycloak_role r ON m.role_id = r.id
        WHERE u.id = %s AND r.name = %s
        """,
        [user_id, role_name],
    )
    assert row is not None, (
        f"TC-INT-05 FAILED at Step 4: Role '{role_name}' not found in user_role_mapping "
        f"for user '{username}'. Admin API returned 204 but DB has no record."
    )
    assert row["role_name"] == role_name, (
        f"TC-INT-05 FAILED at Step 4: DB role name mismatch. "
        f"Expected '{role_name}', got '{row['role_name']}'"
    )

    # ── Step 5: Retrieve role mappings via Admin API ──
    # Layer 3: Admin API read — confirms the assignment is retrievable
    # through a separate endpoint from the one used to write it
    mappings_url = f"{base}/admin/realms/{realm}/users/{user_id}/role-mappings/realm"
    r = requests.get(mappings_url, headers=_admin_headers(admin_token), timeout=20)
    assert r.status_code == 200, (
        f"TC-INT-05 FAILED at Step 5: Could not retrieve role mappings: "
        f"{r.status_code} {r.text}"
    )

    assigned_roles = [entry["name"] for entry in r.json()]
    assert role_name in assigned_roles, (
        f"TC-INT-05 FAILED at Step 5: Role '{role_name}' not found in Admin API "
        f"role-mappings response for user '{username}'. "
        f"DB confirmed the mapping, but Admin API does not reflect it. "
        f"Roles returned: {assigned_roles}"
    )