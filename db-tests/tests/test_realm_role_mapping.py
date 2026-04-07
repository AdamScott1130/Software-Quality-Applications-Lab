import time
import pytest
from src.db import get_conn


@pytest.fixture
def db():
    """Provide DB connection using shared project helper (.env aware)."""
    with get_conn() as conn:
        yield conn


def test_realm_role_mapping(db):
    """
    Validate that a realm-level Keycloak role can be assigned to a user.
    """

    # Unique test data
    role_id = f"realm_role_{int(time.time())}"
    user_id = f"user_realm_{int(time.time())}"
    role_name = f"tester_role_{int(time.time())}"

    try:
        with db.cursor() as cur:

            # Step 1 — Create Realm Role (realm_id='master' is common)
            cur.execute(
                """
                INSERT INTO keycloak_role (id, name, realm_id)
                VALUES (%s, %s, 'master');
                """,
                (role_id, role_name),
            )

            # Step 2 — Create User
            cur.execute(
                """
                INSERT INTO user_entity (id, username)
                VALUES (%s, %s);
                """,
                (user_id, "tester-user"),
            )

            # Step 3 — Assign Realm Role to User
            cur.execute(
                """
                INSERT INTO user_role_mapping (user_id, role_id)
                VALUES (%s, %s);
                """,
                (user_id, role_id),
            )

            db.commit()

            # Step 4 — Validate Mapping
            cur.execute(
                """
                SELECT u.username AS username, r.name AS role_name
                FROM user_entity u
                JOIN user_role_mapping m ON u.id = m.user_id
                JOIN keycloak_role r ON m.role_id = r.id
                WHERE u.id = %s;
                """,
                (user_id,),
            )

            result = cur.fetchone()

            assert result["username"] == "tester-user"
            assert result["role_name"] == role_name

    finally:
        # Cleanup for re-runnable tests
        with db.cursor() as cur:
            cur.execute("DELETE FROM user_role_mapping WHERE user_id=%s", (user_id,))
            cur.execute("DELETE FROM user_entity WHERE id=%s", (user_id,))
            cur.execute("DELETE FROM keycloak_role WHERE id=%s", (role_id,))
            db.commit()