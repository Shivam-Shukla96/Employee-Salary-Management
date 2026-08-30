from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql://postgres:postgres@localhost:5432/salary_management"
    test_database_url: str = "postgresql://postgres:postgres@localhost:5432/salary_management_test"

    # App
    app_name: str = "Salary Management API"
    debug: bool = False

    # Pagination defaults
    default_page_size: int = 20
    max_page_size: int = 100

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
