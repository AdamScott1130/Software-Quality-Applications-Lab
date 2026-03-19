import pytest
from src.db import get_conn


@pytest.fixture
def db():
    """Provide a shared DB connection using project helper."""
    with get_conn() as conn:
        yield conn


def test_core_tables_exist(db):
    """
    Ensures essential Keycloak tables exist in the database.
    """

    expected_tables = {
        "user_entity",
        "client",
        "user_role_mapping",
        "credential",
    }

    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN (
            'user_entity',
            'client',
            'user_role_mapping',
            'credential'
        );
    """

    with db.cursor() as cur:
        cur.execute(query)
        results = cur.fetchall()

    # FIX: results are dict_row, not tuple row
    returned_tables = {row["table_name"] for row in results}

    for table in expected_tables:
        assert table in returned_tables, f"Missing required table: {table}"