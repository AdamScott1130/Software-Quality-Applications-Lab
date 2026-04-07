import pytest
from src.db import get_conn


@pytest.fixture
def db():
    """Provide a DB connection using the shared project helper and .env."""
    with get_conn() as conn:
        yield conn


def test_sql_injection_protection(db):
    """
    Ensures that parameterized queries properly block SQL injection attempts.
    """

    malicious_input = "' OR '1'='1"  # classic SQL injection payload

    query = """
        SELECT username
        FROM user_entity
        WHERE username = %s;
    """

    with db.cursor() as cur:
        cur.execute(query, (malicious_input,))
        results = cur.fetchall()

    # If SQL injection were possible, many users would be returned.
    # With parameterization, zero rows should match this malicious input.
    assert len(results) == 0