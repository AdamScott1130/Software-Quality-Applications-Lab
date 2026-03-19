import time
import pytest
from src.db import get_conn


@pytest.fixture
def db():
    """Provide a DB connection using the shared project helper."""
    with get_conn() as conn:
        yield conn


def test_primary_key_constraint(db):
    """
    Verifies that inserting two rows with the same primary key
    triggers a UniqueViolation constraint error.
    """

    # Generate a unique PK value for this test run
    user_id = f"pk_test_{int(time.time())}"

    with db.cursor() as cur:
        # Insert the first user
        insert_query = """
            INSERT INTO user_entity (id, first_name, last_name)
            VALUES (%s, %s, %s);
        """
        cur.execute(insert_query, (user_id, "Abdhullah", "Ahamed"))
        db.commit()

        # Attempt a duplicate insert — should fail
        with pytest.raises(Exception) as exc:
            cur.execute(insert_query, (user_id, "Abdhullah", "Ahamed"))
            db.commit()

        # Validate that this is indeed a unique constraint violation
        assert "unique" in str(exc.value).lower()