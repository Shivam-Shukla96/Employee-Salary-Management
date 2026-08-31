# Architecture & Design Notes

## Overview

The Employee Salary Management system is a web application built for an HR Manager to manage salary data for 10,000 employees across multiple countries. It replaces manual Excel-based workflows with a searchable, filterable interface and analytical dashboards.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                     │
│                                                             │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌──────────┐ │
│  │Dashboard │  │ Employee   │  │ Employee │  │Analytics │  │
│  │  (Home)  │  │   List     │  │  Detail  │  │Dashboard │  │
│  └──────────┘  └────────────┘  └──────────┘  └──────────┘  │
│                        │                                    │
│                  API Client (fetch)                          │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / JSON
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Routers (API Layer)                │   │
│  │  /api/employees  /api/employees/{id}/salary          │   │
│  │  /api/analytics  /api/config  /api/health            │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │               Services (Business Logic)              │   │
│  │  EmployeeService  SalaryService  AnalyticsService    │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │                 Models (SQLAlchemy)                   │   │
│  │  Employee  SalaryRecord  ExchangeRate                │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │ SQL
                          ▼
                    ┌──────────────┐
                    │ PostgreSQL   │
                    │  (Supabase)  │
                    └──────────────┘
```

## Layered Architecture

The backend follows a strict **three-layer architecture**:

| Layer | Responsibility | Example |
|---|---|---|
| **Routers** | HTTP concerns — parsing request params, status codes, response formatting | `employees.py`, `analytics.py` |
| **Services** | Business logic — validation, currency conversion, aggregation | `EmployeeService`, `SalaryService` |
| **Models** | Data persistence — SQLAlchemy ORM mappings, database schema | `Employee`, `SalaryRecord` |

Each layer only knows about the layer directly below it. Routers never touch the database directly; services never return HTTP responses.

---

## Data Model

```
┌─────────────────────┐        ┌──────────────────────┐
│     employees       │        │   salary_records     │
├─────────────────────┤        ├──────────────────────┤
│ id (UUID, PK)       │───┐    │ id (UUID, PK)        │
│ employee_id (EMP-X) │   │    │ employee_id (FK)     │◄──┐
│ full_name           │   └───►│ base_salary          │   │
│ email (unique)      │        │ currency             │   │
│ department          │        │ effective_date       │   │
│ job_title           │        │ salary_usd           │   │
│ country             │        │ created_at           │   │
│ status (enum)       │        └──────────────────────┘   │
│ joining_date        │                                    │
│ created_at          │        ┌──────────────────────┐   │
│ updated_at          │        │  exchange_rates      │   │
└─────────────────────┘        ├──────────────────────┤   │
                               │ id (UUID, PK)        │   │
                               │ currency (unique)    │───┘
                               │ rate_to_usd          │ (used for
                               │ effective_date       │  conversion)
                               └──────────────────────┘
```

### Key Design Decisions

1. **Append-only salary history**: Salary changes create new `SalaryRecord` rows rather than updating in place. The latest record (by `effective_date`) represents the current salary. This is audit-friendly and supports future trend analysis.

2. **Pre-computed USD equivalent**: Each salary record stores `salary_usd` at write time. This avoids re-computing conversions on every analytics query and makes aggregations fast.

3. **Soft delete via status enum**: Employees are never hard-deleted. Setting `status = INACTIVE` preserves data for historical analytics while hiding inactive employees from default views.

---

## Currency Normalization Strategy

The system stores salaries in their **local currency** and converts to USD using a seeded exchange rate table:

```
salary_usd = base_salary × exchange_rate.rate_to_usd
```

- Exchange rates are **static seed data** (deliberate MVP trade-off)
- USD conversion happens at **write time** (when salary is created/updated)
- Analytics always aggregate on `salary_usd` for cross-country comparisons
- The architecture supports swapping in a live exchange rate provider by replacing the rate lookup in `SalaryService`

---

## Analytics Engine

All analytics are computed via **server-side SQL aggregations** rather than shipping raw data to the browser. With 10,000 employees, this is significantly more efficient:

- **Summary KPIs**: COUNT, AVG, MEDIAN, MIN, MAX on `salary_usd`
- **By Department/Country/Role**: GROUP BY with the same aggregations
- **Active employees only**: All analytics filter to `status = ACTIVE` by default

The `AnalyticsService._get_active_employee_salaries_usd()` method is the single data source for all analytics — it joins employees with their latest salary record and the exchange rate, ensuring consistency.

---

## Frontend Architecture

| Concern | Approach |
|---|---|
| **Framework** | Next.js 16 (App Router) |
| **State Management** | Local state + URL search params (no global store needed) |
| **Theming** | CSS custom properties with `[data-theme]` switching (light/dark) |
| **API Communication** | Centralized `api.ts` client with typed interfaces |
| **Filter Persistence** | URL search params — survives navigation and back button |
| **Form UX** | Pre-filled edit forms, dirty checking (no API call if unchanged), field-level validation |

---

## Testing Strategy

| Layer | Approach | Count |
|---|---|---|
| **Models** | Unit tests for constraints (unique email, required fields, cascading deletes) | 13 |
| **Services** | Unit tests for business logic (salary conversion, search, filtering, pagination) | 40 |
| **API** | Integration tests via FastAPI TestClient (full request/response cycle) | 34 |
| **Health** | Smoke test for the health endpoint | 1 |

All tests use an **in-memory SQLite database** for speed and isolation. Each test runs in a transaction that is rolled back after the test, ensuring deterministic results.

---

## Configuration & Secrets

All configuration is externalized via environment variables (loaded from `.env` using Pydantic Settings):

- **Secrets** (`DATABASE_URL`) — never hardcoded, loaded from `.env`
- **Business domain** (departments, countries, currencies) — configurable via env vars with sensible defaults
- **Environment** (`APP_ENV`) — supports development/staging/production modes
- **CORS origins** — configurable per environment

A `.env.example` file documents all available variables.

---

## Key Trade-offs

| Decision | Rationale |
|---|---|
| Static exchange rates over live API | Avoids external dependencies for MVP. Architecture cleanly isolates rate conversion in service layer for future live sync. |
| Admin Settings Portal in Phase 2 | Keeps MVP focused on core employee compensation and analytics without introducing unnecessary master data CRUD bloat. |
| Server-side aggregation over client-side | With 10K records, SQL aggregations are faster and more memory-efficient. |
| Soft delete over hard delete | Matches real-world HR behavior. Inactive employees remain for historical analytics. |
| Append-only salary history | Immutable audit trail. Supports future compensation trend analysis. |
| Offset-based pagination | Simpler than cursor-based. Sufficient for 10K records. |
| URL search params over React state | Preserves filter state across navigation. Shareable URLs. |
| No authentication | Single-user persona (HR Manager). First thing to add for production. |
| PostgreSQL over SQLite | More production-realistic. Supports concurrent access. |

---

## Future Scalability & Enterprise Roadmap

As the platform matures from MVP to enterprise scale, the following architectural evolutions are planned:

### 1. Self-Service Admin Settings Portal (Master Data Management)
- **Goal**: Enable non-technical HR and Finance administrators to manage master data (countries, departments, supported currencies) directly through an Admin Settings UI without requiring developer intervention, environment variable updates, or code redeployments.
- **Architecture**: Dynamic master data tables and management endpoints (`/api/admin/currencies`, `/api/admin/departments`, `/api/admin/countries`) consumed directly by frontend forms.

### 2. Date-Effective Exchange Rate Ledger (Historical vs. Live Rates)
- **Accounting Challenge**: In live financial systems, market exchange rates fluctuate continuously. Updating a single exchange rate in place would incorrectly alter historical salary analytics retrospectively.
- **Solution**: Implement a **Temporal Exchange Rate Ledger**:
  ```sql
  CREATE TABLE exchange_rate_history (
      id UUID PRIMARY KEY,
      currency VARCHAR(3) NOT NULL,
      rate_to_usd NUMERIC(10, 6) NOT NULL,
      effective_from DATE NOT NULL,
      effective_to DATE,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );
  ```
- **Benefit**: Historical salary records are evaluated against the exchange rate active on their specific `effective_date`, ensuring bulletproof accounting integrity and auditability.

### 3. Automated Forex & Banking Feed Integration
- Integrate with live exchange rate providers (e.g., Open Exchange Rates, European Central Bank API) with scheduled daily background sync and fallback caching.

### 4. Role-Based Access Control (RBAC)
- **Admin**: Master data configuration, exchange rate management, user management.
- **HR Manager**: Employee CRUD, compensation updates, department assignments.
- **Executive / Viewer**: Read-only access to organizational analytics and dashboards.
