# Models package — import all models so SQLAlchemy and Alembic discover them.
from app.models.employee import Employee, EmployeeStatus  # noqa: F401
from app.models.salary_record import SalaryRecord  # noqa: F401
from app.models.exchange_rate import ExchangeRate  # noqa: F401
