# db-tests/tests/test_int_set_password_verify_credential.py
#
# TC-INT-02: Set password via API and verify credential record in DB
# Integration test — API layer (reset-password endpoint) → DB layer (credential table)
# Validates that a password set via the Keycloak Admin API is:
#   1) Stored as a credential row in the database
#   2) Not stored in plaintext

import uuid
import pytest
from src.keycloak_api import get_admin_token, reset_user_password
from src.db import (
    get_user_entity_id,
    find_credential_table,
    fetch_password_credential_row,
    count_plaintext_hits_in_password_credential,
)
import os


@pytest.mark.integration
def test_int_set_password_verify_credential(created_user):
    """
    TC-INT-02: Set password via API and verify credential record in DB.

    Steps:
    1) Use created_user fixture to get a live Keycloak user
    2) Set password via Admin API reset-password endpoint
    3) Query credential table directly in PostgreSQL
    4) Assert credential row exists with type='password'
    5) Assert plaintext password does not appear anywhere in credential storage
    6) Assert hashed/encoded data is present
    """

    base_url = os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080")
    realm = os.getenv("KEYCLOAK_REALM", "master")

    username = created_user["username"]
    user_id = created_user["id"]
    plaintext_password = f"IntTest_P@ss_{uuid.uuid4().hex[:8]}!"

    # ── Step 1: Get admin token ──
    admin_token = get_admin_token()

    # ── Step 2: Set password via API ──
    reset_user_password(
        base_url=base_url,
        realm=realm,
        user_id=user_id,
        admin_token=admin_token,
        password=plaintext_password,
        temporary=False,
    )

    # ── Step 3: Resolve DB identifiers ──
    credential_table = find_credential_table()
    user_entity_id = get_user_entity_id(username)

    # ── Step 4: Assert credential row exists ──
    cred_row = fetch_password_credential_row(credential_table, user_entity_id)
    assert cred_row["type"] == "password", (
        f"Expected credential type 'password', got '{cred_row['type']}'"
    )

    # ── Step 5: Assert plaintext is NOT stored ──
    hits = count_plaintext_hits_in_password_credential(
        credential_table, user_entity_id, plaintext_password
    )
    assert hits == 0, (
        f"Plaintext password found in DB credential table (hits={hits}). "
        "Credential storage is not secure."
    )

    # ── Step 6: Assert hashed data is present ──
    cred_data = str(cred_row.get("credential_data") or "")
    secret_data = str(cred_row.get("secret_data") or "")

    assert len(cred_data) > 0 or len(secret_data) > 0, (
        "Expected hashed credential data in credential_data or secret_data, "
        "but both fields are empty."
    )
    assert plaintext_password not in cred_data, (
        "Plaintext password found in credential_data field."
    )
    assert plaintext_password not in secret_data, (
        "Plaintext password found in secret_data field."
    )