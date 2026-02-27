# getting the latest API test user from db
from src.db import fetch_one

def get_latest_api_user(prefix="apitest_user_"): # using apitest_user_ as per test case repot
    return fetch_one(
        """
        SELECT username
        FROM user_entity
        WHERE username LIKE %s
        ORDER BY created_timestamp DESC
        LIMIT 1
        """,
        [f"{prefix}%"]
    )