import time
import pytest
from src.db import get_conn


@pytest.fixture
def db():
    """Provide DB connection using project helper."""
    with get_conn() as conn:
        yield conn


def test_client_role_mapping(db):
    """
    Validate that a client role can be assigned to a user and retrieved correctly.
    """

    # Unique test data to avoid collisions
    client_id = f"client_{int(time.time())}"
    role_id = f"role_{int(time.time())}"
    user_id = f"user_{int(time.time())}"
    client_identifier = f"{client_id}_app"
    role_name = f"{client_id}_reader"

    try:
        with db.cursor() as cur:

            # Step 1 — Create client
            cur.execute(
                """
                INSERT INTO client (id, client_id, enabled)
                VALUES (%s, %s, true);
                """,
                (client_id, client_identifier),
            )

            # Step 2 — Create client role
            cur.execute(
                """
                INSERT INTO keycloak_role (id, name, client_role, client)
                VALUES (%s, %s, true, %s);
                """,
                (role_id, role_name, client_id),
            )

            # Step 3 — Insert user
            cur.execute(
                """
                INSERT INTO user_entity (id, username)
                VALUES (%s, %s);
                """,
                (user_id, "client-role-user"),
            )

            # Step 4 — Assign role to user
            cur.execute(
                """
                INSERT INTO user_role_mapping (user_id, role_id)
                VALUES (%s, %s);
                """,
                (user_id, role_id),
            )

            db.commit()

            # Step 5 — Validate mapping
            cur.execute(
                """
                SELECT 
                    u.username AS username,
                    r.name AS role_name,
                    c.client_id AS client_id
                FROM user_entity u
                JOIN user_role_mapping m ON u.id = m.user_id
                JOIN keycloak_role r ON r.id = m.role_id
                LEFT JOIN client c ON c.id = r.client
                WHERE u.id = %s;
                """,
                (user_id,),
            )

            result = cur.fetchone()

            assert result["username"] == "client-role-user"
            assert result["role_name"] == role_name
            assert result["client_id"] == client_identifier

    finally:
        # Cleanup ensures tests can run repeatedly
        with db.cursor() as cur:
            cur.execute("DELETE FROM user_role_mapping WHERE user_id=%s", (user_id,))
            cur.execute("DELETE FROM user_entity WHERE id=%s", (user_id,))
            cur.execute("DELETE FROM keycloak_role WHERE id=%s", (role_id,))
            cur.execute("DELETE FROM client WHERE id=%s", (client_id,))
            db.commit()