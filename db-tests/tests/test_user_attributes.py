# This test checks whether user attributes are stored correctly in database.
from src.db import fetch_one
from src.db_helper import get_latest_api_user

def test_user_attributes():
    row = get_latest_api_user()
    assert row is not None, "There is no API created user." # Checking if there is user in DB

    username = row["username"] # getting username from get_latest_api_user function

    attr = fetch_one( # Having attribute is optional.
        """
        SELECT ua.name, ua.value
        FROM user_attribute ua
        JOIN user_entity ue ON ue.id = ua.user_id
        WHERE ue.username = %s
        """,
        [username],
    )

    if attr is None:
        assert True
    else:
        assert attr["name"] is not None
        assert attr["value"] is not None