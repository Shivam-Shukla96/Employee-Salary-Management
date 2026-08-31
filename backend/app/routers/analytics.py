"""
Analytics API router — salary aggregation endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import (
    AnalyticsResponse,
    CountrySalaryStat,
    DepartmentSalaryStat,
    RoleSalaryStat,
    SalarySummary,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _get_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("", response_model=AnalyticsResponse)
def get_full_analytics(service: AnalyticsService = Depends(_get_service)):
    """Get complete salary analytics (summary + by department + by country)."""
    data = service.get_full_analytics()
    return AnalyticsResponse(
        summary=SalarySummary(**data["summary"]),
        by_department=[DepartmentSalaryStat(**d) for d in data["by_department"]],
        by_country=[CountrySalaryStat(**c) for c in data["by_country"]],
        by_role=[RoleSalaryStat(**r) for r in data["by_role"]],
    )


@router.get("/summary", response_model=SalarySummary)
def get_summary(service: AnalyticsService = Depends(_get_service)):
    """Get global salary summary."""
    return SalarySummary(**service.get_summary())


@router.get("/by-department", response_model=list[DepartmentSalaryStat])
def get_department_stats(service: AnalyticsService = Depends(_get_service)):
    """Get salary statistics grouped by department."""
    return [DepartmentSalaryStat(**d) for d in service.get_department_stats()]


@router.get("/by-country", response_model=list[CountrySalaryStat])
def get_country_stats(service: AnalyticsService = Depends(_get_service)):
    """Get salary statistics grouped by country."""
    return [CountrySalaryStat(**c) for c in service.get_country_stats()]


@router.get("/by-role", response_model=list[RoleSalaryStat])
def get_role_stats(service: AnalyticsService = Depends(_get_service)):
    """Get salary statistics grouped by job title / role."""
    return [RoleSalaryStat(**r) for r in service.get_role_stats()]
