import time
import pytest
from src.db import get_conn


@pytest.fixture
def db():
    """Provide a database connection through shared project helper."""
    with get_conn() as conn:
        yield conn


def test_user_query_performance(db):
    """
    Performance test to ensure user_entity query executes within time limits.
    """

    with db.cursor() as cur:
        # Optional warm-up query for more stable timing
        cur.execute("SELECT 1;")
        cur.fetchone()

        # Measure execution time
        start = time.time()

        cur.execute("SELECT * FROM user_entity;")
        cur.fetchall()

        end = time.time()
        execution_time = end - start

        # Requirement: must complete under 1 second
        assert execution_time < 1, f"Query took too long: {execution_time:.4f} seconds"