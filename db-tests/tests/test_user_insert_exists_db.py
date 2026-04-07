import uuid
import pytest

from src import db
from src.keycloak_api import create_user


@pytest.mark.db
def test_user_insertion_and_db_existence():
    """
    Simulate user insertion (via Keycloak Admin API) and verify persistence in DB (user_entity).
    """
    username = f"db_insert_user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"

    # 1) Insert user via Keycloak API (system behavior)
    status = create_user(username=username, email=email, enabled=True)
    assert status in (201, 409)

    # 2) Verify in DB
    assert db.user_exists(username), f"User {username} not found in DB after API insertion"

    # Optional: show ID (useful for debugging/demo)
    user_row = db.get_user_row(username)
    assert user_row is not None
    print("DB user row:", user_row)