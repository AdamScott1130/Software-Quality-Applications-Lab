# Keycloak QA Automation Framework

## Overview

This project is a unified QA automation framework for testing the Keycloak IAM system using multiple testing layers:

- **API Testing** (Postman + Newman)
- **UI Testing** (Selenium + Java + TestNG)
- **Database Validation** (Python + psycopg + pytest + PostgreSQL)
- **Containerized Environment** (Docker)

The objective is to simulate a real-world enterprise QA automation architecture with layered validation and reusable automation components.

---

## Architecture

```
qa-automation-project-keycloak/
├── api-tests/        → API automation tests
├── ui-tests/         → Selenium UI automation framework
├── db-tests/         → Python DB validation framework
├── ci-cd/            → CI/CD configs (future)
├── docs/             → Documentation
├── docker-compose.yml
└── README.md
```

### Testing Strategy

- Black-box testing approach
- Multi-layer validation (API → DB)
- Independent execution of test suites
- Containerized environment for reproducibility
- End-to-end persistence validation

---

## Quick Start

```bash
git clone <REPO_URL>
cd qa-automation-project-keycloak
docker compose up -d

cd api-tests && npm install && npx newman run collections/Keycloak_QA_Tests.postman_collection.json

cd ../ui-tests/keycloak-ui-tests && mvn clean test

cd ../../db-tests
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

---

## Full Setup Guide

### Step 1 — Clone Repository

```bash
git clone <REPO_URL>
cd qa-automation-project-keycloak
```

### Step 2 — Install Prerequisites

Install the following tools:

| Tool | Purpose |
|------|---------|
| Docker Desktop | Run Keycloak + PostgreSQL |
| Node.js | API tests |
| Java JDK 17 | UI automation |
| Maven | Build Selenium framework |
| Python 3.11+ | Database validation |

Verify installations:

```bash
docker -v
docker compose version
node -v
npm -v
java -version
mvn -version
python --version
```

### Step 3 — Start Containers

```bash
docker compose up -d
docker ps
```

Access Keycloak at:

```
http://localhost:8080
```

PostgreSQL runs on:

```
localhost:5433
```

Credentials:

```
admin / admin
```

---

## Running Tests

### Run API Tests

```bash
cd api-tests
npm install
npx newman run collections/Keycloak_QA_Tests.postman_collection.json
```

### Run UI Tests

```bash
cd ../ui-tests/keycloak-ui-tests
mvn clean test
```

### Run Database Validation Tests

Navigate to `db-tests`:

```bash
cd ../../db-tests
```

Create virtual environment (Windows):

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside `db-tests/`:

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=keycloak_db
DB_USER=keycloak
DB_PASSWORD=password

KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=admin
```

Run all DB tests:

```bash
pytest -q
```

Run smoke test only:

```bash
pytest tests/test_db_smoke.py -q
```

Run user persistence test:

```bash
pytest tests/test_user_persisted.py::test_user_created_persisted_in_db -q
```

---

## What Database Tests Validate

- Database connectivity
- Keycloak persistence layer
- User creation via API
- Direct verification in PostgreSQL `user_entity` table
- End-to-end validation (API → Database)

This ensures real integration validation beyond API-level testing.

---

## Troubleshooting

**Maven not recognized**
Add Maven `bin` folder to `PATH` and restart terminal.

**Docker containers not running**

Check status:
```bash
docker ps
```
Restart if needed:
```bash
docker compose up -d
```

**PostgreSQL connection errors**

Verify container port:
```bash
docker ps
```
PostgreSQL should map:
```
0.0.0.0:5433 -> 5432
```

**pytest not recognized**

Ensure virtual environment is activated:
```bash
.venv\Scripts\activate
```

**No tables found in DB**

Verify Keycloak is connected to PostgreSQL:
```bash
docker exec -it postgres psql -U keycloak -d keycloak_db -c "\dt"
```

---

## Tech Stack

- Selenium WebDriver
- TestNG
- Java
- Postman
- Newman
- Python
- psycopg3
- pytest
- PostgreSQL
- Docker
- Keycloak IAM

---

## Author

**Nanmi Zimik**  
QA Automation Framework Project