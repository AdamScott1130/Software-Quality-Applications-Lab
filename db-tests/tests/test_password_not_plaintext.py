# db-tests/tests/test_password_not_plaintext.py

import os
import uuid
import pytest

from src.keycloak_api import reset_user_password
from src import db


def _env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


@pytest.mark.db
def test_tc_db_03_password_credential_stored_not_plaintext(admin_token, created_user):
    """
    TC-DB-03: Verify password credential stored and not plaintext (US-006) — Database

    API is used ONLY to set password.
    All assertions are DB-level.
    """
    base_url = _env("KEYCLOAK_BASE_URL")
    realm = os.getenv("KEYCLOAK_REALM", "master")

    username = created_user["username"]
    user_id_api = created_user["id"]

    plaintext_password = f"P@ssw0rd_{uuid.uuid4().hex[:10]}!"

    # Setup (API)
    reset_user_password(
        base_url=base_url,
        realm=realm,
        user_id=user_id_api,
        admin_token=admin_token,
        password=plaintext_password,
        temporary=False
    )

    # Assertions (DB)
    cred_table = db.find_credential_table()
    user_entity_id = db.get_user_entity_id(username)

    cred_row = db.fetch_password_credential_row(cred_table, user_entity_id)

    # 1) password credential row exists
    assert cred_row["type"] == "password"

    # 2) plaintext password must NOT appear
    hits = db.count_plaintext_hits_in_password_credential(cred_table, user_entity_id, plaintext_password)
    assert hits == 0, f"Plaintext password found in DB credential storage (hits={hits})"

    # 3) hashed/encoded data present
    cred_data = "" if cred_row.get("credential_data") is None else str(cred_row.get("credential_data"))
    secret_data = "" if cred_row.get("secret_data") is None else str(cred_row.get("secret_data"))

    assert (len(cred_data) > 0) or (len(secret_data) > 0), "Expected hashed credential data, got empty fields."
    assert plaintext_password not in cred_data
    assert plaintext_password not in secret_data