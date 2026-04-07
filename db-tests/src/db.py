# PostgreSQL connection helper
import os
print("DB CONNECT:", os.getenv("PGHOST"), os.getenv("PGPORT"), os.getenv("PGDATABASE"), os.getenv("PGUSER"))
import psycopg
from psycopg.rows import dict_row

def get_conn():
    print(
    "DB CONNECT:",
    os.getenv("PGHOST"),
    os.getenv("PGPORT"),
    os.getenv("PGDATABASE"),
    os.getenv("PGUSER"),
    "PGPASSWORD_LEN=",
    len(os.getenv("PGPASSWORD") or ""),
)
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "keycloak_db"),
        user=os.getenv("PGUSER", "keycloak"),
        password=os.getenv("PGPASSWORD", "password"),
        row_factory=dict_row,
    )

def fetch_one(query: str, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or [])
            return cur.fetchone()

def user_exists(username: str) -> bool:
    row = fetch_one("SELECT 1 AS ok FROM user_entity WHERE username=%s", [username])
    return row is not None

def get_user_row(username: str):
    return fetch_one("SELECT id, username FROM user_entity WHERE username=%s", [username])

def table_exists(table_name: str) -> bool:
    q = """
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema='public' AND table_name=%s
    """
    return fetch_one(q, [table_name]) is not None


def find_credential_table() -> str:
    """
    Keycloak schema varies by version.
    Common tables: credential, credential_entity
    """
    for t in ("credential", "credential_entity"):
        if table_exists(t):
            return t
    raise AssertionError("Credential table not found (expected 'credential' or 'credential_entity').")


def get_user_entity_id(username: str) -> str:
    row = fetch_one("SELECT id FROM user_entity WHERE username=%s", [username])
    if not row:
        raise AssertionError(f"user_entity not found for username={username}")
    return row["id"]


def fetch_password_credential_row(credential_table: str, user_entity_id: str) -> dict:
    q = f"""
    SELECT id, type, credential_data, secret_data
    FROM {credential_table}
    WHERE user_id=%s AND type='password'
    ORDER BY created_date DESC NULLS LAST
    LIMIT 1
    """
    row = fetch_one(q, [user_entity_id])
    if not row:
        raise AssertionError(f"No password credential row found in {credential_table} for user_id={user_entity_id}")
    return row


def count_plaintext_hits_in_password_credential(credential_table: str, user_entity_id: str, plaintext: str) -> int:
    like = f"%{plaintext}%"
    q = f"""
    SELECT COUNT(*) AS hits
    FROM {credential_table}
    WHERE user_id=%s AND type='password'
      AND (
        CAST(credential_data AS TEXT) ILIKE %s
        OR CAST(secret_data     AS TEXT) ILIKE %s
      )
    """
    row = fetch_one(q, [user_entity_id, like, like])
    return int(row["hits"])