import time
from src.keycloak_api import create_user
from src.db import fetch_one

def test_user_created_persisted_in_db():
    username = f"py_db_user_{int(time.time())}"
    email = f"{username}@example.com"

    create_user(username=username, email=email)

    row = fetch_one(
        "SELECT id, username, email, enabled FROM user_entity WHERE username = %s",
        [username],
    )

    assert row is not None, "User not found in DB"
    assert row["username"] == username
    assert row["email"] == email