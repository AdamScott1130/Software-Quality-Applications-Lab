import time
import pytest
from src.db import get_conn


@pytest.fixture
def db():
    """Provide a DB connection using the shared helper and .env values."""
    with get_conn() as conn:
        yield conn


def test_invalid_role_assignment(db):
    """
    Test that inserting a role mapping with non‑existent foreign keys
    raises a ForeignKeyViolation error.
    """

    # Generate unique but invalid IDs (to guarantee failure)
    user_id = f"invalid_user_{int(time.time())}"
    role_id = f"invalid_role_{int(time.time())}"

    insert_query = """
        INSERT INTO user_role_mapping (user_id, role_id)
        VALUES (%s, %s);
    """

    with db.cursor() as cur:
        # Expect a foreign key violation
        with pytest.raises(Exception) as exc:
            cur.execute(insert_query, (user_id, role_id))
            db.commit()

        # Psycopg3 raises specific error types under psycopg.errors
        assert "foreign key" in str(exc.value).lower() or "ForeignKeyViolation" in str(type(exc.value))