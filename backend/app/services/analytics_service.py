"""
AnalyticsService — salary aggregations by department, country, and overall.

All monetary values are normalized to USD using the exchange rate table.
Only ACTIVE employees are included in analytics.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import func, and_, desc
from sqlalchemy.orm import Session

from app.models.employee import Employee, EmployeeStatus
from app.models.exchange_rate import ExchangeRate
from app.models.salary_record import SalaryRecord


class AnalyticsService:
    """Service layer for salary analytics and aggregations."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_department_stats(self) -> list[dict]:
        """
        Get salary statistics grouped by department.

        Returns avg, min, max, total payroll in USD per department.
        Only includes active employees with their latest salary.
        """
        salaries = self._get_active_employee_salaries_usd()

        dept_groups: dict[str, list[Decimal]] = {}
        for emp in salaries:
            dept = emp["department"]
            if dept not in dept_groups:
                dept_groups[dept] = []
            dept_groups[dept].append(emp["salary_usd"])

        result = []
        for dept, amounts in sorted(dept_groups.items()):
            result.append({
                "department": dept,
                "employee_count": len(amounts),
                "avg_salary_usd": self._round(sum(amounts) / len(amounts)),
                "min_salary_usd": self._round(min(amounts)),
                "max_salary_usd": self._round(max(amounts)),
                "total_payroll_usd": self._round(sum(amounts)),
            })

        return result

    def get_country_stats(self) -> list[dict]:
        """
        Get salary statistics grouped by country.

        Returns avg salary in local currency and USD, total payroll in USD.
        Only includes active employees with their latest salary.
        """
        salaries = self._get_active_employee_salaries_usd()

        country_groups: dict[str, dict] = {}
        for emp in salaries:
            country = emp["country"]
            if country not in country_groups:
                country_groups[country] = {
                    "currency": emp["currency"],
                    "local_amounts": [],
                    "usd_amounts": [],
                }
            country_groups[country]["local_amounts"].append(emp["base_salary"])
            country_groups[country]["usd_amounts"].append(emp["salary_usd"])

        result = []
        for country, data in sorted(country_groups.items()):
            local = data["local_amounts"]
            usd = data["usd_amounts"]
            result.append({
                "country": country,
                "currency": data["currency"],
                "employee_count": len(usd),
                "avg_salary_local": self._round(sum(local) / len(local)),
                "avg_salary_usd": self._round(sum(usd) / len(usd)),
                "total_payroll_usd": self._round(sum(usd)),
            })

        return result

    def get_summary(self) -> dict:
        """
        Get global salary summary across the entire organization.

        Returns total employees, avg/min/max/total payroll in USD.
        Only includes active employees.
        """
        salaries = self._get_active_employee_salaries_usd()

        if not salaries:
            return {
                "total_employees": 0,
                "avg_salary_usd": Decimal("0"),
                "median_salary_usd": Decimal("0"),
                "min_salary_usd": Decimal("0"),
                "max_salary_usd": Decimal("0"),
                "total_payroll_usd": Decimal("0"),
            }

        usd_amounts = [s["salary_usd"] for s in salaries]
        sorted_amounts = sorted(usd_amounts)
        n = len(sorted_amounts)

        # Median calculation
        if n % 2 == 0:
            median = (sorted_amounts[n // 2 - 1] + sorted_amounts[n // 2]) / 2
        else:
            median = sorted_amounts[n // 2]

        return {
            "total_employees": n,
            "avg_salary_usd": self._round(sum(usd_amounts) / n),
            "median_salary_usd": self._round(median),
            "min_salary_usd": self._round(min(usd_amounts)),
            "max_salary_usd": self._round(max(usd_amounts)),
            "total_payroll_usd": self._round(sum(usd_amounts)),
        }

    def get_role_stats(self) -> list[dict]:
        """
        Get salary statistics grouped by job title / role.

        Returns avg, min, max, employee count in USD per role.
        Only includes active employees with their latest salary.
        """
        salaries = self._get_active_employee_salaries_usd()

        role_groups: dict[str, list[Decimal]] = {}
        for emp in salaries:
            role = emp["job_title"]
            if role not in role_groups:
                role_groups[role] = []
            role_groups[role].append(emp["salary_usd"])

        result = []
        for role, amounts in sorted(role_groups.items()):
            result.append({
                "job_title": role,
                "employee_count": len(amounts),
                "avg_salary_usd": self._round(sum(amounts) / len(amounts)),
                "min_salary_usd": self._round(min(amounts)),
                "max_salary_usd": self._round(max(amounts)),
            })

        return result

    def get_full_analytics(self) -> dict:
        """Get the complete analytics response (summary + department + country + role)."""
        return {
            "summary": self.get_summary(),
            "by_department": self.get_department_stats(),
            "by_country": self.get_country_stats(),
            "by_role": self.get_role_stats(),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_active_employee_salaries_usd(self) -> list[dict]:
        """
        Get the latest salary for each active employee, converted to USD.

        This is the core data source for all analytics. It:
        1. Filters to active employees only
        2. Picks the latest salary record per employee (by effective_date)
        3. Converts each salary to USD using the exchange rate table
        """
        # Build a subquery for the latest salary record per employee
        latest_salary_sq = (
            self.db.query(
                SalaryRecord.employee_id,
                func.max(SalaryRecord.effective_date).label("max_date"),
            )
            .group_by(SalaryRecord.employee_id)
            .subquery()
        )

        # Join employees with their latest salary and exchange rate
        rows = (
            self.db.query(Employee, SalaryRecord, ExchangeRate)
            .join(
                SalaryRecord,
                Employee.id == SalaryRecord.employee_id,
            )
            .join(
                latest_salary_sq,
                and_(
                    SalaryRecord.employee_id == latest_salary_sq.c.employee_id,
                    SalaryRecord.effective_date == latest_salary_sq.c.max_date,
                ),
            )
            .outerjoin(
                ExchangeRate,
                SalaryRecord.currency == ExchangeRate.currency,
            )
            .filter(Employee.status == EmployeeStatus.ACTIVE)
            .all()
        )

        result = []
        for emp, salary, rate in rows:
            rate_to_usd = rate.rate_to_usd if rate else Decimal("1")
            salary_usd = salary.base_salary * rate_to_usd

            result.append({
                "employee_id": emp.id,
                "department": emp.department,
                "country": emp.country,
                "job_title": emp.job_title,
                "base_salary": salary.base_salary,
                "currency": salary.currency,
                "salary_usd": self._round(salary_usd),
            })

        return result

    @staticmethod
    def _round(value: Decimal) -> Decimal:
        """Round to 2 decimal places."""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
