# Employee Salary Management Software

Web-based salary management application for ACME org's HR team. Manages salary data for 10,000 employees across multiple countries with compensation analytics and insights.

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic
- **Frontend:** Next.js (React)
- **Database:** PostgreSQL
- **Containerization:** Docker, Docker Compose

## Quick Start

### Prerequisites
- Docker and Docker Compose

### Run the full stack
```bash
docker-compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Run backend tests
```bash
cd backend
pip install -e ".[dev]"
pytest
```

## Project Structure

```
├── docs/                # Requirements and design documents
├── backend/             # FastAPI application
│   ├── app/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic request/response schemas
│   │   ├── routers/     # API route handlers
│   │   └── services/    # Business logic layer
│   ├── tests/           # pytest test suite
│   └── alembic/         # Database migrations
├── frontend/            # Next.js application
└── docker-compose.yml   # Full stack orchestration
```

## Documentation

- [Requirements Document](docs/requirements.md)
