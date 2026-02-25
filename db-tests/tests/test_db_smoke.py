from src.db import fetch_one

def test_db_connection_smoke():
    row = fetch_one("SELECT 1 AS ok")
    assert row["ok"] == 1