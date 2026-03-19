import pytest
from src.db import get_conn


@pytest.fixture
def db():
    """Use the shared DB connection helper (loads .env automatically)."""
    with get_conn() as conn:
        yield conn


def test_sample(db):
    """Simple smoke test to verify that DB responds."""
    with db.cursor() as cur:
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        assert result["?column?"] == 1 or result[0] == 1