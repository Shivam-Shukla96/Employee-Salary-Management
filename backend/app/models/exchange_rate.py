"""ExchangeRate model — static currency-to-USD conversion table."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.types import PortableUUID


class ExchangeRate(Base):
    """
    Stores a static exchange rate for converting a currency to USD.

    Conversion formula: salary_in_usd = base_salary * rate_to_usd

    For USD, rate_to_usd = 1.0 (base currency).
    Rates are seeded once and not updated live — this is a deliberate MVP trade-off.
    """

    __tablename__ = "exchange_rates"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    currency: Mapped[str] = mapped_column(
        String(3), unique=True, nullable=False, index=True
    )
    rate_to_usd: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=6), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ExchangeRate {self.currency}: {self.rate_to_usd}>"
