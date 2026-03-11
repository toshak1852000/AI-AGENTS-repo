"""Market data database models."""
import uuid
from sqlalchemy import Column, String, DateTime, Numeric, Index
from sqlalchemy.sql import func
from src.core.database import Base


def _uuid():
    return str(uuid.uuid4())


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(String, primary_key=True, default=_uuid)
    symbol = Column(String, nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Numeric, nullable=True)
    high_price = Column(Numeric, nullable=True)
    low_price = Column(Numeric, nullable=True)
    close_price = Column(Numeric, nullable=False)
    volume = Column(Numeric, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("idx_symbol_date", "symbol", "date"),)


class CommodityPrice(Base):
    __tablename__ = "commodity_prices"

    id = Column(String, primary_key=True, default=_uuid)
    commodity_type = Column(String, nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False)
    price = Column(Numeric, nullable=False)
    unit = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("idx_commodity_date", "commodity_type", "date"),)
