import time
import pytest
from src.db import get_conn, fetch_one


@pytest.fixture
def db():
    """Use shared DB connection with proper .env loading."""
    with get_conn() as conn:
        yield conn


def test_delete_user(db):
    # Create a unique user ID to delete
    user_id = f"utest_delete_{int(time.time())}"
    email = f"{user_id}@example.com"

    # Insert a temporary user that we will delete
    insert_query = """
        INSERT INTO user_entity
        (id, email, enabled, email_verified, first_name, last_name)
        VALUES (%s, %s, true, false, %s, %s);
    """

    with db.cursor() as cur:
        cur.execute(insert_query, (user_id, email, "Temp", "User"))
        db.commit()

    # Delete that user
    delete_query = """
        DELETE FROM user_entity
        WHERE id = %s;
    """

    with db.cursor() as cur:
        cur.execute(delete_query, (user_id,))
        db.commit()

    # Verify deletion
    row = fetch_one(
        "SELECT * FROM user_entity WHERE id = %s;",
        [user_id],
    )

    assert row is None