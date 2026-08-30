from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analytics, employees, salaries

app = FastAPI(
    title=settings.app_name,
    description="Employee Salary Management API for ACME org",
    version="0.1.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Register routers
app.include_router(employees.router)
app.include_router(salaries.router)
app.include_router(analytics.router)
