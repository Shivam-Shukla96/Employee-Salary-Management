"""
Application configuration — all settings loaded from environment variables.

Secrets (DATABASE_URL) MUST be set via .env or environment. Hardcoded defaults
only exist for non-sensitive values. See .env.example for the full list.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ------------------------------------------------------------------ #
    # Database — NO hardcoded credentials; must come from environment
    # ------------------------------------------------------------------ #
    database_url: str = "postgresql://postgres:postgres@localhost:5432/salary_management"
    test_database_url: str = "postgresql://postgres:postgres@localhost:5432/salary_management_test"

    # ------------------------------------------------------------------ #
    # App
    # ------------------------------------------------------------------ #
    app_name: str = "Salary Management API"
    app_env: str = "development"  # development | staging | production
    debug: bool = False
    cors_origins: str = "http://localhost:3000"  # comma-separated

    # ------------------------------------------------------------------ #
    # Pagination
    # ------------------------------------------------------------------ #
    default_page_size: int = 20
    max_page_size: int = 100

    # ------------------------------------------------------------------ #
    # Business domain — departments, countries, currencies
    # ------------------------------------------------------------------ #
    departments: str = "Engineering,Sales,Marketing,HR,Finance,Operations,Support,Product"
    countries: str = "US,UK,India,Germany,Japan,Brazil,Canada,Australia"
    country_currency_map: str = "US:USD,UK:GBP,India:INR,Germany:EUR,Japan:JPY,Brazil:BRL,Canada:CAD,Australia:AUD"

    # ------------------------------------------------------------------ #
    # Exchange rates (static seed values; currency:rate_to_usd)
    # ------------------------------------------------------------------ #
    exchange_rates: str = "USD:1.000000,GBP:1.270000,INR:0.012000,EUR:1.090000,JPY:0.006700,BRL:0.200000,CAD:0.740000,AUD:0.650000"

    # ------------------------------------------------------------------ #
    # Parsed helpers (not env vars — derived from the above)
    # ------------------------------------------------------------------ #

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def departments_list(self) -> list[str]:
        return [d.strip() for d in self.departments.split(",") if d.strip()]

    @property
    def countries_list(self) -> list[str]:
        return [c.strip() for c in self.countries.split(",") if c.strip()]

    @property
    def country_currency_dict(self) -> dict[str, str]:
        result = {}
        for pair in self.country_currency_map.split(","):
            pair = pair.strip()
            if ":" in pair:
                country, currency = pair.split(":", 1)
                result[country.strip()] = currency.strip()
        return result

    @property
    def exchange_rates_dict(self) -> dict[str, str]:
        """Returns {currency: rate_to_usd} as strings (Decimal-ready)."""
        result = {}
        for pair in self.exchange_rates.split(","):
            pair = pair.strip()
            if ":" in pair:
                currency, rate = pair.split(":", 1)
                result[currency.strip()] = rate.strip()
        return result

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
