from pathlib import Path
from dotenv import load_dotenv

def pytest_sessionstart(session):
    env_path = Path(__file__).with_name(".env")
    load_dotenv(env_path)  # load EXACTLY db-tests/.env
    print("Loaded .env from:", env_path)