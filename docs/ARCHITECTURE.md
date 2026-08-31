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
| Static exchange rates over live API | Avoids external dependencies. Architecture cleanly separates the rate lookup for future swap. |
| Server-side aggregation over client-side | With 10K records, SQL aggregations are faster and more memory-efficient. |
| Soft delete over hard delete | Matches real-world HR behavior. Inactive employees remain for historical analytics. |
| Append-only salary history | Immutable audit trail. Supports future compensation trend analysis. |
| Offset-based pagination | Simpler than cursor-based. Sufficient for 10K records. |
| URL search params over React state | Preserves filter state across navigation. Shareable URLs. |
| No authentication | Single-user persona (HR Manager). First thing to add for production. |
| PostgreSQL over SQLite | More production-realistic. Supports concurrent access. |
