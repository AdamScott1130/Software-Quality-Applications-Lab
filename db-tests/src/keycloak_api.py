# Keycloak admin API helper
import os
import requests

def base_url():
    return os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080").rstrip("/")

def get_admin_token():
    realm = os.getenv("KEYCLOAK_REALM", "master")
    url = f"{base_url()}/realms/{realm}/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": os.getenv("KEYCLOAK_ADMIN_USER", "admin"),
        "password": os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin"),
    }
    r = requests.post(url, data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def create_user(username: str, email: str | None = None, enabled: bool = True):
    realm = os.getenv("KEYCLOAK_REALM", "master")
    url = f"{base_url()}/admin/realms/{realm}/users"
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"username": username, "enabled": enabled}
    if email:
        payload["email"] = email

    r = requests.post(url, json=payload, headers=headers, timeout=30)

    # 201 created, 409 means already exists (fine for reruns)
    if r.status_code not in (201, 409):
        raise RuntimeError(f"Create user failed: {r.status_code} {r.text}")
    return r.status_code