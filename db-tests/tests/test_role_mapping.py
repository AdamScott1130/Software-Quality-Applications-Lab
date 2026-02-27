# This test represent verifying role mapping exists in user_role_mapping
from src.db import fetch_one
from src.db_helper import get_latest_api_user

def test_role_mapping():
    row = get_latest_api_user()
    assert row is not None, "There is no API created user." # Checking if there is user in DB

    username = row["username"]
    expected_role = "test-user" # TC-API-08 Returned roles include 'test-user'

    row = fetch_one(
        """
        SELECT 1
        FROM user_role_mapping urm
        JOIN user_entity ue ON ue.id = urm.user_id
        JOIN keycloak_role r ON r.id = urm.role_id
        WHERE ue.username = %s
          AND r.name = %s
        LIMIT 1
        """,
        [username, expected_role]
    )

    assert row is not None, f"Role '{expected_role}' is not mapped to user '{username}'"