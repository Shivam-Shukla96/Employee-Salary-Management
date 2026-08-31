"""
Seed script — populates the database with 10,000 employees and exchange rates.

Generates realistic data across multiple countries, departments, and roles
with country-appropriate salary ranges in local currencies.

Usage:
    python -m app.seed
"""

import random
import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Employee, EmployeeStatus, ExchangeRate, SalaryRecord
from app.database import Base
from app.config import settings

# ---------------------------------------------------------------------------
# Reference data — sourced from environment configuration
# ---------------------------------------------------------------------------

# Country → currency mapping (from config)
COUNTRY_CURRENCY = settings.country_currency_dict

# Exchange rates: currency → rate_to_usd (from config)
EXCHANGE_RATES = {k: Decimal(v) for k, v in settings.exchange_rates_dict.items()}

# Departments (from config)
DEPARTMENTS = settings.departments_list

# Weighted country distribution — seed-only (not configurable, only for data generation)
COUNTRY_WEIGHTS = {c: 12 for c in settings.countries_list}
# Override with heavier weights for US and India
COUNTRY_WEIGHTS.update({"US": 25, "India": 25})

# Department weights — Engineering is the largest (seed-only)
DEPARTMENT_WEIGHTS = [25, 15, 10, 8, 10, 12, 12, 8]
# Pad or trim to match DEPARTMENTS length
while len(DEPARTMENT_WEIGHTS) < len(DEPARTMENTS):
    DEPARTMENT_WEIGHTS.append(10)
DEPARTMENT_WEIGHTS = DEPARTMENT_WEIGHTS[:len(DEPARTMENTS)]

# Job titles per department (pyramid: more juniors than seniors)
JOB_TITLES = {
    "Engineering": [
        ("Junior Software Engineer", 40),
        ("Software Engineer", 30),
        ("Senior Software Engineer", 15),
        ("Staff Engineer", 8),
        ("Engineering Manager", 5),
        ("VP of Engineering", 2),
    ],
    "Sales": [
        ("Sales Development Rep", 35),
        ("Account Executive", 30),
        ("Senior Account Executive", 15),
        ("Sales Manager", 12),
        ("Director of Sales", 5),
        ("VP of Sales", 3),
    ],
    "Marketing": [
        ("Marketing Coordinator", 30),
        ("Marketing Specialist", 30),
        ("Senior Marketing Manager", 20),
        ("Director of Marketing", 12),
        ("VP of Marketing", 8),
    ],
    "HR": [
        ("HR Coordinator", 35),
        ("HR Specialist", 30),
        ("Senior HR Manager", 20),
        ("Director of HR", 10),
        ("VP of HR", 5),
    ],
    "Finance": [
        ("Financial Analyst", 35),
        ("Senior Financial Analyst", 25),
        ("Finance Manager", 20),
        ("Director of Finance", 12),
        ("VP of Finance", 8),
    ],
    "Operations": [
        ("Operations Coordinator", 30),
        ("Operations Analyst", 30),
        ("Operations Manager", 20),
        ("Director of Operations", 12),
        ("VP of Operations", 8),
    ],
    "Support": [
        ("Support Agent", 40),
        ("Senior Support Agent", 25),
        ("Support Team Lead", 15),
        ("Support Manager", 12),
        ("Director of Support", 8),
    ],
    "Product": [
        ("Associate Product Manager", 30),
        ("Product Manager", 30),
        ("Senior Product Manager", 20),
        ("Director of Product", 12),
        ("VP of Product", 8),
    ],
}

# Salary ranges per country in LOCAL CURRENCY (min, max) for a mid-level role.
# Junior roles get ~60-80% of this range, senior roles get ~120-200%.
BASE_SALARY_RANGES = {
    "US": (60_000, 150_000),       # USD
    "UK": (35_000, 100_000),       # GBP
    "India": (600_000, 3_000_000), # INR
    "Germany": (45_000, 120_000),  # EUR
    "Japan": (4_000_000, 12_000_000),  # JPY
    "Brazil": (60_000, 300_000),   # BRL
    "Canada": (55_000, 140_000),   # CAD
    "Australia": (60_000, 160_000),# AUD
}

# Seniority multipliers based on title position in the list (index)
SENIORITY_MULTIPLIERS = [0.65, 0.85, 1.0, 1.25, 1.55, 1.90]

# First and last names for generating realistic employee names
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Arun", "Priya", "Raj", "Sunita", "Vikram", "Deepa", "Amit", "Anjali",
    "Hiroshi", "Yuki", "Kenji", "Sakura", "Takeshi", "Haruka", "Satoshi", "Mika",
    "Hans", "Anna", "Klaus", "Sophie", "Lukas", "Emma", "Felix", "Lena",
    "Carlos", "Maria", "Pedro", "Ana", "Lucas", "Julia", "Rafael", "Beatriz",
    "Liam", "Olivia", "Noah", "Ava", "Oliver", "Sophia", "Ethan", "Isabella",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Sharma", "Patel", "Kumar", "Singh", "Gupta", "Reddy", "Nair", "Verma",
    "Tanaka", "Yamamoto", "Sato", "Suzuki", "Watanabe", "Takahashi", "Ito", "Nakamura",
    "Mueller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
    "Silva", "Santos", "Oliveira", "Souza", "Costa", "Pereira", "Ferreira", "Almeida",
    "Campbell", "Stewart", "Fraser", "MacDonald", "Murphy", "O'Brien", "Walsh", "Kelly",
]


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------


def _generate_salary(country: str, title_index: int) -> Decimal:
    """Generate a realistic salary based on country and seniority level."""
    min_sal, max_sal = BASE_SALARY_RANGES[country]
    multiplier = SENIORITY_MULTIPLIERS[min(title_index, len(SENIORITY_MULTIPLIERS) - 1)]

    base = random.uniform(min_sal, max_sal) * multiplier
    # Round to nearest 1000
    rounded = round(base / 1000) * 1000
    return Decimal(str(max(rounded, min_sal)))


def _generate_employee_id(index: int) -> str:
    """Generate a formatted employee ID like EMP-0001."""
    return f"EMP-{index:05d}"


def _generate_joining_date() -> date:
    """Generate a random joining date within the last 10 years."""
    days_ago = random.randint(30, 3650)  # 1 month to 10 years
    return date.today() - timedelta(days=days_ago)


def seed_exchange_rates(session: Session) -> None:
    """Seed the exchange rate table."""
    existing = session.query(ExchangeRate).count()
    if existing > 0:
        print(f"  [SKIP] Exchange rates already exist ({existing} rates)")
        return

    for currency, rate in EXCHANGE_RATES.items():
        exchange_rate = ExchangeRate(currency=currency, rate_to_usd=rate)
        session.add(exchange_rate)
    session.commit()
    print(f"  [OK] Seeded and committed {len(EXCHANGE_RATES)} exchange rates")


def seed_employees(session: Session, count: int = 10_000, batch_size: int = 1000) -> None:
    """Seed employees with realistic data distribution in fast batches."""
    countries = list(COUNTRY_WEIGHTS.keys())
    country_weights = list(COUNTRY_WEIGHTS.values())

    used_emails: set[str] = set()
    employees_created = 0

    batch_employees = []
    batch_salaries = []

    for i in range(1, count + 1):
        # Pick country (weighted)
        country = random.choices(countries, weights=country_weights, k=1)[0]
        currency = COUNTRY_CURRENCY[country]

        # Pick department (weighted)
        department = random.choices(DEPARTMENTS, weights=DEPARTMENT_WEIGHTS, k=1)[0]

        # Pick job title from department (weighted, pyramid distribution)
        titles_with_weights = JOB_TITLES[department]
        titles = [t[0] for t in titles_with_weights]
        title_weights = [t[1] for t in titles_with_weights]
        title_index = random.choices(range(len(titles)), weights=title_weights, k=1)[0]
        job_title = titles[title_index]

        # Generate name
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"

        # Generate unique email
        email_base = f"{first_name.lower()}.{last_name.lower()}"
        email = f"{email_base}@acme.com"
        counter = 1
        while email in used_emails:
            email = f"{email_base}{counter}@acme.com"
            counter += 1
        used_emails.add(email)

        # Decide status (~90% active, ~10% inactive)
        status = EmployeeStatus.INACTIVE if random.random() < 0.10 else EmployeeStatus.ACTIVE

        # Create employee with pre-generated UUID so we don't need roundtrip flush
        emp_uuid = uuid.uuid4()
        joining_date = _generate_joining_date()
        employee = Employee(
            id=emp_uuid,
            employee_id=_generate_employee_id(i),
            full_name=full_name,
            email=email,
            department=department,
            job_title=job_title,
            country=country,
            status=status,
            joining_date=joining_date,
        )
        batch_employees.append(employee)

        # Create initial salary record
        salary = _generate_salary(country, title_index)
        salary_record = SalaryRecord(
            id=uuid.uuid4(),
            employee_id=emp_uuid,
            base_salary=salary,
            currency=currency,
            effective_date=joining_date,
        )
        batch_salaries.append(salary_record)

        employees_created += 1
        if len(batch_employees) >= batch_size:
            session.add_all(batch_employees)
            session.add_all(batch_salaries)
            session.commit()
            print(f"  ... committed {employees_created}/{count} employees")
            batch_employees.clear()
            batch_salaries.clear()

    if batch_employees:
        session.add_all(batch_employees)
        session.add_all(batch_salaries)
        session.commit()

    print(f"  [OK] Seeded {employees_created} employees with salary records")


def run_seed() -> None:
    """Main seed entry point — creates tables and populates data."""
    print("[SEED] Starting database seed...")

    # Create tables
    Base.metadata.create_all(bind=engine)
    print("  [OK] Database tables created")

    session = SessionLocal()
    try:
        # Check if already seeded
        existing = session.query(Employee).count()
        if existing > 0:
            print(f"  [SKIP] Database already has {existing} employees. Skipping seed.")
            return

        seed_exchange_rates(session)
        session.commit()
        seed_employees(session, count=10_000)
        print("[SEED] Seed complete!")
    except Exception as e:
        session.rollback()
        print(f"[SEED] Seed failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()
