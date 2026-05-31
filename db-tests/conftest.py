# db-tests/conftest.py

from pathlib import Path
from dotenv import load_dotenv
import os
import uuid
import pytest
import requests


# ----------------------------------
# Load .env automatically
# ----------------------------------
def pytest_sessionstart(session):
    env_path = Path(__file__).with_name(".env")
    load_dotenv(env_path)
    print("Loaded .env from:", env_path)


# ----------------------------------
# Helper functions
# ----------------------------------
def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


# ----------------------------------
# Fixtures
# ----------------------------------

@pytest.fixture()
def admin_token():
    """
    Gets Keycloak admin access token.
    """
    base = _env("KEYCLOAK_BASE_URL").rstrip("/")
    url = f"{base}/realms/master/protocol/openid-connect/token"

    data = {
        "grant_type": "password",#this is what triggers keycloak to wsrite a session
        "client_id": "admin-cli",
        "username": _env("KEYCLOAK_ADMIN_USER"),
        "password": _env("KEYCLOAK_ADMIN_PASSWORD"),
    }

    response = requests.post(url, data=data, timeout=20)
    response.raise_for_status()

    return response.json()["access_token"]


@pytest.fixture()
def created_user(admin_token):
    """
    Creates a temporary user for DB tests.
    Cleans up after test completes.
    """
    base = _env("KEYCLOAK_BASE_URL").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "master")

    suffix = uuid.uuid4().hex[:8]
    username = f"db_pwd_user_{suffix}"
    email = f"{username}@example.com"

    # Create user
    create_url = f"{base}/admin/realms/{realm}/users"
    payload = {
        "username": username,
        "enabled": True,
        "email": email
    }

    r = requests.post(create_url, json=payload, headers=_headers(admin_token), timeout=20)
    if r.status_code not in (201, 204):
        r.raise_for_status()

    # Retrieve user ID
    search_url = f"{base}/admin/realms/{realm}/users"
    r = requests.get(search_url, params={"username": username}, headers=_headers(admin_token), timeout=20)
    r.raise_for_status()

    users = r.json()
    assert users, f"User not found after creation: {username}"
    user_id = users[0]["id"]

    yield {
        "username": username,
        "id": user_id
    }

    # Cleanup: delete user
    delete_url = f"{base}/admin/realms/{realm}/users/{user_id}"
    requests.delete(delete_url, headers=_headers(admin_token), timeout=20)