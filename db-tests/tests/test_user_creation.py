import time
import pytest
from src.keycloak_api import create_user
from src.db import fetch_one,get_conn
@pytest.fixture
def db():
    """Provide a reusable DB connection using existing project helper."""
    with get_conn() as conn:
        yield conn


def test_keycloak_create_user(db):
    # Generate unique ID each run
    user_id = f"utest_{int(time.time())}"
    email = f"{user_id}@example.com"

    # Insert user
    insert_query = """
        INSERT INTO user_entity
        (id, email, enabled, email_verified, first_name, last_name)
        VALUES (%s, %s, true, false, %s, %s);
    """

    with db.cursor() as cur:
        cur.execute(insert_query, (user_id, email, "Abdhul", "Rahuman"))
        db.commit()

    # Verify insertion
    row = fetch_one(
        "SELECT first_name, last_name, email FROM user_entity WHERE id = %s",
        [user_id],
    )

    assert row["first_name"] == "Abdhul"
    assert row["last_name"] == "Rahuman"
    assert row["email"] == email