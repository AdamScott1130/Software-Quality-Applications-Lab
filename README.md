# Keycloak QA Automation Framework

---

## Overview
This project is a unified QA automation framework for testing the **Keycloak IAM system** using multiple testing layers:

- API Testing (Postman + Newman)
- UI Testing (Selenium + Java + TestNG)
- Database Validation (Node.js + PostgreSQL)
- Containerized Environment (Docker)

The objective is to simulate a real-world enterprise QA automation architecture with layered validation and reusable automation components.

---

## Architecture

```
qa-automation-project-keycloak/
├── api-tests/        → API automation tests
├── ui-tests/         → Selenium UI automation framework
├── db-tests/         → Database validation scripts
├── ci-cd/            → CI/CD configs (future)
├── docs/             → Documentation
├── docker-compose.yml
└── README.md
```

Testing Strategy:
- Black-box testing approach
- Multi-layer validation
- Independent execution of test suites
- Containerized environment for reproducibility

---

## Quick Start

```
git clone <REPO_URL>
cd qa-automation-project-keycloak
docker compose up -d

cd api-tests && npm install && npx newman run collections/Keycloak_QA_Tests.postman_collection.json

cd ../ui-tests/keycloak-ui-tests && mvn clean test

cd ../../db-tests && npm install && node validateUsers.js
```

---

## Full Setup Guide

### Step 1 — Clone Repository
```
git clone <REPO_URL>
cd qa-automation-project-keycloak
```

---

### Step 2 — Install Prerequisites

Install the following tools:

| Tool | Purpose |
|-----|--------|
Docker Desktop | Run Keycloak + PostgreSQL |
Node.js | API + DB tests |
Java JDK 17 | UI automation |
Maven | Build Selenium framework |

Verify installations:

```
docker -v
docker compose version
node -v
npm -v
java -version
mvn -version
```

---

### Step 3 — Start Containers

```
docker compose up -d
docker ps
```

Access Keycloak:
```
http://localhost:8080
```

Credentials:
```
admin / admin
```

---

## Running Tests

### Run API Tests
```
cd api-tests
npm install
npx newman run collections/Keycloak_QA_Tests.postman_collection.json
```

---

### Run UI Tests
```
cd ../ui-tests/keycloak-ui-tests
mvn clean test
```

---

### Run Database Validation Tests
```
cd ../../db-tests
npm install
node validateUsers.js
```

---

## Troubleshooting

### Maven not recognized
Add Maven bin folder to PATH and restart terminal.

---

### Docker containers not running
Check status:
```
docker ps
```

---

### Realm does not exist
Ensure realm name matches your Postman environment or Keycloak setup.

---

### Invalid client error
Verify client exists in Keycloak and credentials are correct.

---

## Tech Stack

- Selenium WebDriver
- TestNG
- Java
- Postman
- Newman
- Node.js
- PostgreSQL
- Docker
- Keycloak IAM

---

## Author
**Nanmi Zimik**

QA Automation Framework Project
