import time
import pytest
from src.db import get_conn, fetch_one


@pytest.fixture
def db():
    """Provide a DB connection using shared helper and .env values."""
    with get_conn() as conn:
        yield conn


def test_update_user_email(db):
    """
    Ensures user email is updated correctly in the database.
    """

    # Create a unique user for testing
    user_id = f"update_test_{int(time.time())}"
    old_email = f"{user_id}@example.com"
    new_email = f"updated_{user_id}@example.com"

    # Insert temporary user
    insert_query = """
        INSERT INTO user_entity (id, email, enabled, email_verified, first_name, last_name)
        VALUES (%s, %s, true, false, %s, %s);
    """
    with db.cursor() as cur:
        cur.execute(insert_query, (user_id, old_email, "Test", "User"))
        db.commit()

    # Update email
    update_query = """
        UPDATE user_entity
        SET email = %s
        WHERE id = %s;
    """
    with db.cursor() as cur:
        cur.execute(update_query, (new_email, user_id))
        db.commit()

    # Verify update
    row = fetch_one(
        "SELECT email FROM user_entity WHERE id = %s",
        [user_id],
    )

    assert row["email"] == new_email