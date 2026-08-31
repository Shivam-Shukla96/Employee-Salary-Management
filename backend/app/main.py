from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analytics, employees, salaries

app = FastAPI(
    title=settings.app_name,
    description="Employee Salary Management API for Incubyte",
    version="0.1.0",
)

# CORS — origins from environment config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/config")
def get_public_config():
    """Return non-sensitive business domain configuration for the frontend."""
    return {
        "departments": settings.departments_list,
        "countries": settings.countries_list,
        "country_currency_map": settings.country_currency_dict,
        "currencies": list(settings.exchange_rates_dict.keys()),
    }


# Register routers
app.include_router(employees.router)
app.include_router(salaries.router)
app.include_router(analytics.router)
