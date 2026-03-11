"""Alert database models."""
import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from src.core.database import Base


def _uuid():
    return str(uuid.uuid4())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=_uuid)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=True)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True)
    run_id = Column(String, nullable=True)
    read = Column(Boolean, default=False, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
