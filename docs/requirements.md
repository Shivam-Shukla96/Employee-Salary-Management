# Requirements Document — Employee Salary Management Software

## Goal

Build a web-based salary management application for ACME org's HR team. The software replaces manual Excel-based workflows and enables the HR Manager to manage salary data for 10,000 employees across multiple countries, and gain insights into how the organization compensates its people.

## User Persona

**HR Manager** — a single administrative user who manages all employee and salary data for the organization. No additional roles or permission levels are required.

## Scope & Features

### Employee Management
- **List employees** with search (by name, employee ID), filtering (by country, department, role, status), sorting, and pagination
- **View** employee profile with full details and salary information
- **Add** new employees with validated required fields
- **Edit** employee details
- **Soft delete** — mark employees as Inactive (preserves data for historical analytics)

### Employee Data Schema
| Field | Type | Notes |
|---|---|---|
| Employee ID | String (EMP-XXXX) | System-generated, unique |
| Full Name | String | Required |
| Email | String | Required, unique |
| Department | String | Required — e.g., Engineering, Sales, Marketing, HR, Finance, Operations, Support, Product |
| Job Title | String | Required — e.g., Software Engineer, Sales Manager, VP of Engineering |
| Country | String | Required — determines default currency |
| Base Salary | Decimal | Required, must be positive |
| Currency | String (ISO 4217) | Auto-set based on country, stored with salary |
| Status | Enum | Active / Inactive. Default: Active |
| Joining Date | Date | Required |
| Created At | Timestamp | System-managed |
| Updated At | Timestamp | System-managed |

### Salary Management
- **View current salary** in local currency and USD equivalent
- **Update salary** — creates a new salary history record with an effective date
- **Salary history** — append-only log of all salary changes per employee, each with an effective date. The most recent record represents the current salary.

### Currency Normalization
- **Exchange rate table** — seeded with static rates for all represented currencies against USD
- **Normalized view** — all analytics support toggling between local currency and USD-normalized values
- Exchange rates are **not live**; they are fixed seed data. This is a deliberate MVP trade-off.

### Analytics & Compensation Insights
- **KPI cards** — total headcount (active), average salary, median salary, salary range (min–max)
- **Salary distribution** — histogram showing how employees are distributed across salary bands
- **Comparison by country** — average/median salary per country (USD-normalized)
- **Comparison by department** — average/median salary per department
- **Comparison by role** — average/median salary per job title
- **Interactive filters** — filter all analytics by country, department, role, status
- **Currency toggle** — view analytics in local currencies or USD-normalized
- Analytics default to **Active employees only**, with an option to include Inactive

### Seed Data
- Seed script generating **10,000 employees** across 6–8 countries, 8 departments, and 12–15 job titles
- Realistic salary ranges per country (adjusted for cost of living)
- Seeded exchange rate table for all represented currencies

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy / Alembic |
| Frontend | Next.js (React) |
| Containerization | Docker, Docker Compose |
| Deployment | Docker Compose locally + cloud deployment |

## What Is Deliberately Out of Scope

| Excluded | Reasoning |
|---|---|
| Payroll components (allowances, bonuses, deductions, tax) | Confirmed out of scope. Base salary only. |
| Authentication / login | Single-user persona confirmed. Adds ceremony with no assessment value. First thing to add in production. |
| Multi-role access control (RBAC) | Single HR Manager role is sufficient. |
| Live exchange rates | Adds external dependency and caching complexity. Static rates are sufficient for analytics. Architecture supports swapping in a live provider. |
| Bulk edit / mass salary updates | Valuable feature but not required for MVP. |
| CSV import / export | Complex validation and error handling — out of scope. |
| Email notifications | No user story requires it. |
| Employee self-service | Only one persona (HR Manager). |
| Multi-tenancy | Single org (ACME). |
| Internationalization (i18n) | English-only UI. |

## Key Trade-offs

1. **Static exchange rates over live API** — avoids external dependencies. The seeded table is sufficient for demonstrating cross-country analytics. The architecture cleanly separates the rate-lookup so a live provider can be plugged in later.

2. **Server-side aggregation over client-side** — with 10K records, SQL-level aggregations are faster and more memory-efficient than shipping raw data to the browser.

3. **Soft delete over hard delete** — inactive employees remain in the database for historical salary analytics. Matches real-world HR behavior.

4. **Append-only salary history over in-place update** — each salary change is an immutable record with an effective date. Audit-friendly and supports future compensation trend analysis.

5. **Offset-based pagination over cursor-based** — simpler to implement and sufficient for 10K records.

6. **PostgreSQL over SQLite** — more production-realistic, supports concurrent access, aligns with Docker Compose deployment.

## Development Approach

- **Test-Driven Development** — tests written before or alongside implementation
- **Incremental commits** — each commit adds a working, testable slice of functionality
- **Phase order**: data model → backend CRUD → salary management → analytics → frontend → dashboard → deployment
