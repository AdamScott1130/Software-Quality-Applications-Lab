# PostgreSQL connection helper

import os
from dotenv import load_dotenv

# --- LOAD .env CORRECTLY ---
# Automatically loads .env from the db-tests/ directory
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "..", ".env")
load_dotenv(env_path)

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