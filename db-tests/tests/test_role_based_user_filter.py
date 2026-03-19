import time
import pytest
from src.db import get_conn


@pytest.fixture
def db():
    """Provide DB connection using shared project helper (.env aware)."""
    with get_conn() as conn:
        yield conn


def test_role_based_user_filter(db):
    """
    Validate that filtering users by role_id returns only the correct users.
    """

    # Generate unique test data
    role_id = f"filter_role_{int(time.time())}"
    user_id = f"filter_user_{int(time.time())}"
    first_name = "Hasan"

    try:
        with db.cursor() as cur:

            # Step 1 — Create role
            cur.execute(
                """
                INSERT INTO keycloak_role (id, name, realm_id)
                VALUES (%s, %s, 'master');
                """,
                (role_id, f"{role_id}_name"),
            )

            # Step 2 — Create user
            cur.execute(
                """
                INSERT INTO user_entity (id, first_name, username)
                VALUES (%s, %s, %s);
                """,
                (user_id, first_name, f"{user_id}_username"),
            )

            # Step 3 — Assign role to user
            cur.execute(
                """
                INSERT INTO user_role_mapping (user_id, role_id)
                VALUES (%s, %s);
                """,
                (user_id, role_id),
            )

            db.commit()

            # Step 4 — Query users by role filter
            cur.execute(
                """
                SELECT u.first_name
                FROM user_entity u
                JOIN user_role_mapping m ON u.id = m.user_id
                WHERE m.role_id = %s;
                """,
                (role_id,),
            )

            results = cur.fetchall()

        # Extract first names (dict rows)
        first_names = [row["first_name"] for row in results]

        # Validation
        assert first_name in first_names

    finally:
        # Cleanup to make test repeatable
        with db.cursor() as cur:
            cur.execute("DELETE FROM user_role_mapping WHERE role_id=%s", (role_id,))
            cur.execute("DELETE FROM user_entity WHERE id=%s", (user_id,))
            cur.execute("DELETE FROM keycloak_role WHERE id=%s", (role_id,))
            db.commit()