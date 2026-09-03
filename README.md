# Employee Salary Management Software

Web-based salary management application for ACME org's HR team. Manages salary data for 10,000 employees across multiple countries with compensation analytics and insights.

- **Frontend Domain:** [https://incubyte.shivamshukla.tech](https://incubyte.shivamshukla.tech) (Hosted on Vercel)
- **Backend API Domain:** [https://api-incubyte.shivamshukla.tech](https://api-incubyte.shivamshukla.tech) (Hosted on GCP)

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL (Supabase)
- **Frontend:** Next.js 16 (React 19), Tailwind CSS, TypeScript
- **Containerization & Deployment:** Docker, Docker Compose, Docker Hub (`shivamdev96/salary-management`), GCP VM, Vercel

---

## Production Deployment Guide

### 1. Build & Push Backend Docker Image

Ensure you are logged in to Docker Hub (`docker login`), then from the root directory run:

```bash
npm run docker:api:publish
```

This runs:
```bash
docker buildx build --platform linux/amd64 -t shivamdev96/salary-management:latest -f backend/Dockerfile . --push
```

### 2. Deploy Backend on GCP Instance

On your GCP Compute Engine VM:
1. Ensure Docker and Docker Compose are installed.
2. Only two files are needed in your deployment folder:
   - `docker-compose.yml`
   - `.env`
3. Launch the container:
   ```bash
   docker compose up -d
   ```
   Docker will automatically pull the image `shivamdev96/salary-management:latest` from Docker Hub, apply any pending Alembic migrations on startup, and serve the API on port `8000`.

4. (Optional) Set up Nginx or Caddy on GCP with SSL for `api-incubyte.shivamshukla.tech` proxying to `http://localhost:8000`.

### 3. Deploy Frontend on Vercel

1. Import this repository in [Vercel](https://vercel.com).
2. Configure project settings:
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
3. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL` = `https://api-incubyte.shivamshukla.tech`
4. Add Custom Domain:
   - Navigate to **Settings > Domains** in Vercel.
   - Add `incubyte.shivamshukla.tech`.

### 4. DNS Configuration

Configure DNS records at your domain registrar/DNS provider:

| Type  | Name           | Value                      |
|-------|----------------|----------------------------|
| CNAME | `incubyte`     | `cname.vercel-dns.com`     |
| A     | `api-incubyte` | `<YOUR_GCP_VM_EXTERNAL_IP>` |

---

## Local Development

### Prerequisites
- Node.js & npm
- Python 3.12+ (or Docker)

### Option A: Local Docker Compose (Full Stack with Hot-Reload)

```bash
npm run dev:build
# or
docker compose -f docker-compose.dev.yml up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option B: Running Services Directly

**Backend:**
```bash
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Run Tests
```bash
cd backend
pytest
```

---

## Project Structure

```
├── .dockerignore         # Docker build exclusions
├── .env                  # Root environment configuration (GCP & local)
├── .env.example          # Environment template
├── docker-compose.yml    # Production Compose for GCP (fetches image from Docker Hub)
├── docker-compose.dev.yml# Local development full-stack Compose
├── package.json          # Root scripts (docker:api:publish, etc.)
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── config.py     # App settings & CORS
│   │   ├── database.py   # SQLAlchemy session & Base
│   │   ├── models/       # Database models
│   │   ├── routers/      # API endpoints
│   │   └── services/     # Business logic & analytics
│   ├── alembic/          # Database migrations
│   ├── Dockerfile        # Production backend Dockerfile
│   └── pyproject.toml    # Python dependencies
├── frontend/             # Next.js application
│   ├── src/lib/api.ts    # Frontend API client
│   └── package.json
└── docs/                 # Documentation & requirements
```
